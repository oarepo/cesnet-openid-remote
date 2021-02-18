# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from datetime import timedelta

from flask import current_app, session, g
from flask_login import current_user, user_logged_out
from flask_principal import identity_loaded, AnonymousIdentity, identity_changed, RoleNeed, UserNeed
from invenio_oauthclient.models import RemoteAccount
from invenio_oauthclient.utils import obj_or_import_string
from werkzeug.local import LocalProxy

from cesnet_openid_remote.constants import OPENIDC_GROUPS_KEY
from cesnet_openid_remote.proxies import current_cesnet_openid

CESNET_OPENID_REMOTE_SESSION_KEY = 'identity.cesnet_provides'
"""Name of session key where CESNET roles are stored."""

CESNET_OPENID_REMOTE_REFRESH_TIMEDELTA = timedelta(minutes=-5)
"""Default interval for refreshing user's extra data (e.g. groups)."""

sconf = LocalProxy(
    lambda: dict(key=current_app.config.get(
        "CESNET_OPENID_REMOTE_SESSION_KEY",
        CESNET_OPENID_REMOTE_SESSION_KEY),
        refresh=current_app.config.get(
            "CESNET_OPENID_REMOTE_REFRESH_TIMEDELTA",
            CESNET_OPENID_REMOTE_REFRESH_TIMEDELTA)))


@identity_changed.connect
def on_identity_changed(sender, identity):
    """Store roles in session whenever identity changes.

    :param sender: Sender of the signal
    :param identity: The user identity where information are stored.
    """
    remote = current_cesnet_openid.remote_app

    if isinstance(identity, AnonymousIdentity):
        return

    logged_in_via_token = \
        hasattr(current_user, 'login_via_oauth2') \
        and getattr(current_user, 'login_via_oauth2')

    client_id = remote.get_consumer_key()
    remote_account = RemoteAccount.get(
        user_id=identity.id, client_id=client_id
    )

    groups = []
    if remote_account and not logged_in_via_token:
        if sconf['refresh']:
            user_info = remote.get_userinfo(remote)
            resource = dict(user_info=user_info,
                            user_id=remote.get_user_id(remote, email=user_info.email))
            groups = remote.remote_groups_and_extra_data(
                remote_account, resource, refresh_timedelta=sconf['refresh']
            )
        else:
            groups = remote_account.extra_data[OPENIDC_GROUPS_KEY]
    elif remote_account and logged_in_via_token:
        groups = remote_account.extra_data[OPENIDC_GROUPS_KEY]

    current_cesnet_openid.sync_user_roles(current_user, groups)
