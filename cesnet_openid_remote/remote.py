# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo."""
from datetime import datetime

from flask import current_app, g
from flask_login import current_user
from flask_principal import AnonymousIdentity
from invenio_db import db
from invenio_oauthclient.handlers.rest import response_handler, default_remote_response_handler
from invenio_oauthclient.models import RemoteAccount
from invenio_oauthclient.utils import oauth_unlink_external_id, oauth_link_external_id, obj_or_import_string
from invenio_openid_connect import InvenioAuthOpenIdRemote
from werkzeug.local import LocalProxy

from cesnet_openid_remote.constants import OPENIDC_GROUPS_KEY, OPENIDC_CONFIG, OPENIDC_GROUPS_SCOPE
from cesnet_openid_remote.errors import OAuthCESNETRejectedAccountError
from cesnet_openid_remote.proxies import current_cesnet_openid

"""Pre-configured remote application for enabling sign in/up with eduID federated accounts."""

OAUTHCLIENT_CESNET_HIDDEN_GROUPS = ()
"""Tunable list of groups that will be invisible to this app."""

OAUTHCLIENT_CESNET_HIDDEN_GROUPS_RE = ()
"""Tunable list of regexps of groups to invisible to this app."""


class CesnetOpenIdRemote(InvenioAuthOpenIdRemote):
    """CESNET OIDC Remote Auth backend for OARepo."""
    CONFIG_OPENID = OPENIDC_CONFIG

    name = 'CESNET eduID Login'
    description = 'Log In with your eduID account'

    def __init__(self):
        """Initialize the remote app."""
        super(CesnetOpenIdRemote, self).__init__()

        self.extras_serializer = LocalProxy(lambda: obj_or_import_string(
            current_app.config.get(
                'OAUTHCLIENT_CESNET_OPENID_EXTRA_DATA_SERIALIZER', self.fetch_extra_data)))

    def remote_app(self) -> dict:
        """Configure and return remote app."""
        conf = super(CesnetOpenIdRemote, self).remote_app()
        conf.update(dict(
            response_handler=default_remote_response_handler,
            authorized_redirect_url='/api/oauth/complete/',
            error_redirect_url='/error',
            disconnect_redirect_url='/logged-out',
            logout_url='https://login.cesnet.cz/oidc/endsession'))
        return conf

    def handle_authorized(self, resp, remote, *args, **kwargs):
        """Handle user authorization.
        :param resp: User authorization response
        :param remote: The remote application
        """
        from invenio_oauthclient.handlers.rest import authorized_signup_handler
        return authorized_signup_handler(resp, remote, *args, **kwargs)

    def handle_signup(self, remote, *args, **kwargs):
        """Handle signup.
        :param remote: The remote application
        """
        from invenio_oauthclient.handlers.rest import signup_handler
        return signup_handler(remote, *args, **kwargs)

    def account_setup(self, remote, token, resp):
        """Perform additional setup after user have been logged in."""
        user_info = self.get_userinfo(remote)
        user_id = self.get_user_id(remote, email=user_info.email)

        with db.session.begin_nested():
            # Put userinfo in extra_data.
            token.remote_account.extra_data = {}

            groups = self.remote_groups_and_extra_data(token.remote_account,
                                                       dict(user_info=user_info, user_id=user_id))
            assert not isinstance(g.identity, AnonymousIdentity)

            user = token.remote_account.user
            current_cesnet_openid.sync_user_roles(user, groups)

            # Create user <-> external id link.
            oauth_link_external_id(user, dict(id=user_id, method=self.name))

    def fetch_extra_data(self, user_info, user_id):
        """"Fetch extra account data from resource."""
        extra_data = user_info

        group_uris = extra_data.pop(OPENIDC_GROUPS_SCOPE, [])
        group_uris = [u for u in group_uris if current_cesnet_openid.validate_group_uri(u)]
        extra_data[OPENIDC_GROUPS_KEY] = group_uris

        extra_data['external_id'] = user_id
        extra_data['external_method'] = self.name
        return extra_data

    def remote_groups_and_extra_data(self, account, resource, refresh_timedelta=None):
        """Fetch account roles and extra data from resource if necessary."""
        updated = datetime.utcnow()
        modified_since = updated
        if refresh_timedelta is not None:
            modified_since += refresh_timedelta
        modified_since = modified_since.isoformat()
        last_update = account.extra_data.get("updated", modified_since)

        if last_update > modified_since:
            return account.extra_data.get(OPENIDC_GROUPS_KEY, [])

        user_info = resource.get('user_info')
        user_id = resource.pop('user_id')
        extra_data = self.extras_serializer(user_info, user_id)

        groups = extra_data.get(OPENIDC_GROUPS_KEY, [])
        account.extra_data.update(
            updated=updated.isoformat(), **extra_data
        )
        return groups

    def _disconnect(self, remote, *args, **kwargs):
        """Handle unlinking of remote account.

           :param remote: The remote application.
        """
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

        account = RemoteAccount.get(user_id=current_user.get_id(),
                                    client_id=remote.consumer_key)
        sub = account.extra_data.get('sub')
        user_info = self.get_userinfo(remote)
        resource = dict(user_info=user_info,
                        user_id=self.get_user_id(remote, email=user_info.email))

        groups = self.remote_groups_and_extra_data(account, resource)
        roles = current_cesnet_openid.groups_roles(groups)
        current_cesnet_openid.remove_user_roles(current_user, roles, reverse=True)

        if sub:
            oauth_unlink_external_id({'id': sub, 'method': self.name})
        if account:
            with db.session.begin_nested():
                account.delete()

    def handle_disconnect(self, remote, *args, **kwargs):
        """Handle unlinking of remote account."""
        self._disconnect(remote, *args, **kwargs)
        redirect_url = current_app.config["OAUTHCLIENT_REST_REMOTE_APPS"][
            remote.name
        ]["disconnect_redirect_url"]
        return response_handler(remote, redirect_url)
