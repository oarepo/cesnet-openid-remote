# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from functools import wraps

import sqlalchemy
from invenio_accounts.models import Role, User
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_oauthclient.models import RemoteAccount
from sqlalchemy import func, cast

from cesnet_openid_remote.constants import OPENIDC_GROUPS_KEY
from cesnet_openid_remote.errors import OAuthCESNETInvalidGroupURI, OAuthCESNETGroupExists, OAuthCESNETRoleProtected
from cesnet_openid_remote.groups import validate_group_uri, parse_group_uri
from cesnet_openid_remote.models import CesnetGroup


def check_role_protected(f):
    """Decorator checking if passed role is protected."""

    @wraps(f)
    def inner(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, Role) and arg in self.protected_roles:
                raise OAuthCESNETRoleProtected

        return f(self, *args, **kwargs)

    return inner


class CesnetOpenIdRemoteAPI(object):
    """Cesnet OIDC Remote API."""

    def __init__(self, app, remote):
        self.app = app
        self.remote_app = remote
        self.validate_group_uri = app.config.get(
            'OAUTHCLIENT_CESNET_OPENID_GROUP_VALIDATOR', validate_group_uri)
        self.parse_group_uri = app.config.get(
            'OAUTHCLIENT_CESNET_OPENID_GROUP_PARSER', parse_group_uri)

    @property
    def protected_roles(self):
        protected_role_names = self.app.config.get(
            'OAUTHCLIENT_CESNET_OPENID_PROTECTED_ROLES', [])
        protected_roles = [current_datastore.find_role(r) for r in protected_role_names]
        return list(filter(None, protected_roles))

    @classmethod
    def find_group(cls, uuid: str) -> CesnetGroup:
        """Find a CESNET group by its unique identifier.

            :param uuid: The unique external identifier of the group
            :returns CesnetGroup: group instance, None if not found
        """
        return CesnetGroup.query.filter_by(uuid=uuid).first()

    def find_or_create_group(self, uri: str) -> CesnetGroup:
        """Find a CESNET group by its URI, or create a new one.

            :param uri: External group URI
            :returns CesnetGroup: found or created CesnetGroup object
        """
        if not validate_group_uri(uri):
            raise OAuthCESNETInvalidGroupURI(uri)

        guuid, attrs = self.parse_group_uri(uri)
        return self.find_group(guuid) or self.create_group(uuid=guuid, attrs=attrs, uri=uri)

    @classmethod
    def remote_accounts(cls, group: CesnetGroup) -> list:
        """Find all remote accounts that are members of a given cesnet group.

            :param group: CesnetGroup to list all members of
            :returns list of all group members
        """
        if db.session.bind.dialect.name != 'postgresql':
            group_field = cast(RemoteAccount.extra_data, sqlalchemy.String)
        else:
            group_field = func.jsonb_array_elements_text(RemoteAccount.extra_data, OPENIDC_GROUPS_KEY)

        query = RemoteAccount.query.filter(group_field.contains(group.uri))
        return query.all()

    @classmethod
    def remote_group_uris(cls, account: RemoteAccount):
        """Returns list of all CESNET group URIs for a given RemoteAccount."""
        return account.extra_data[OPENIDC_GROUPS_KEY]

    @classmethod
    def create_group(cls, uuid: str, attrs: dict, uri: str) -> CesnetGroup:
        """Create a CESNET group record from external group URI.

           :param uuid: External group unique UUID identifier
           :param attrs: External group additional attributes
           :param uri: External group URI
           :returns CesnetGroup: created cesnet group object
           :raises OAuthCESNETInvalidGroupURI:
        """
        display_name = attrs.get('displayName', None)
        with db.session.begin_nested():
            if CesnetGroup.query.filter_by(uuid=uuid).count():
                raise OAuthCESNETGroupExists(uuid)

            cg = CesnetGroup(uuid=uuid,
                             display_name=display_name,
                             uri=uri)
            db.session.add(cg)
            return cg

    def groups_roles(self, group_uris: list) -> list:
        """Return a list of all Invenio Roles associated with group URIs.

            :param group_uris: List of CESNET group URIs
            :returns list[Role]: list of all associated Invenio roles
        """
        group_roles = []
        for uri in group_uris:
            group_roles += self.find_or_create_group(uri).roles

        return group_roles

    @check_role_protected
    def add_group_role(self, group: CesnetGroup, role: Role):
        """Assign a CESNET group to Invenio role.

            :param group: CESNET group to be assigned
            :param role: target Invenio role to be assigned to group
            :returns True if group was assigned, False otherwise
        """
        if role not in group.roles:
            with db.session.begin_nested():
                group.roles.append(role)

                # Find and add to role all remote accounts with this group
                for ra in self.remote_accounts(group):
                    self.sync_user_roles(ra.user, self.remote_group_uris(ra))

    @check_role_protected
    def remove_group_role(self, group: CesnetGroup, role: Role):
        """Remove CESNET group from Invenio role.

            :param group: CESNET group to be removed
            :param role: Invenio role
            :raises OAuthCESNETGroupNotInRole:
        """
        if role in group.roles:
            with db.session.begin_nested():
                group.roles.remove(role)

                # Find and remove from role all remote account users
                # with this group that haven't any other group assigned to this role
                for ra in self.remote_accounts(group):
                    self.sync_user_roles(ra.user, self.remote_group_uris(ra))

    def add_user_roles(self, user: User, group_roles: list):
        """Assign Invenio roles to user based on his cesnet groups.

            :param user: User instance to be roles assigned to
            :param group_roles: list of user group's roles
        """
        group_roles = set(group_roles) - set(self.protected_roles)
        with db.session.begin_nested():
            for role in group_roles:
                current_datastore.add_role_to_user(user, role)

    def remove_user_roles(self, user: User, group_roles: list, reverse=False):
        """Remove user from any role that is not in group-granted roles.

            :param user: User instance to remove roles from
            :param group_roles: list of user group's roles
            :param reverse: if True, removes roles granted by group roles instead
        """
        if not reverse:
            extra_roles = (set(user.roles) - set(group_roles)) - set(self.protected_roles)
        else:
            extra_roles = set(user.roles).union(set(group_roles)) - set(self.protected_roles)
        with db.session.begin_nested():
            for extra in extra_roles:
                current_datastore.remove_role_from_user(user, extra)

    def sync_user_roles(self, user: User, group_uris: list):
        """Synchronize user's roles based on his cesnet group URIs."""

        roles = self.groups_roles(group_uris)

        self.remove_user_roles(user, roles)
        self.add_user_roles(user, roles)
