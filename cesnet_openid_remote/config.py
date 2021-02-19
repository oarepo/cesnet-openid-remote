# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
import os
from datetime import timedelta

from cesnet_openid_remote import CesnetOpenIdRemote
from cesnet_openid_remote.constants import OPENIDC_GROUPS_SCOPE, OPENIDC_BASE_URL

CESNET_OPENIDC_CONFIG = dict(
    base_url=OPENIDC_BASE_URL,
    consumer_key=os.environ.get('OPENIDC_KEY', 'MISSING_OIDC_KEY'),
    consumer_secret=os.environ.get('OPENIDC_SECRET', 'MISSING_OIDC_SECRET'),
    scope=f'openid email profile {OPENIDC_GROUPS_SCOPE} isCesnetEligibleLastSeen'
)

CESNET_OPENID_REMOTE_REFRESH_TIMEDELTA = timedelta(minutes=-5)
"""Default interval for refreshing user's extra data (e.g. groups)."""

CESNET_OPENID_REMOTE_GROUP_PREFIX = 'urn:geant:cesnet.cz:'
"""Default prefix of group attribute URIs."""

CESNET_OPENID_REMOTE_GROUP_AUTHORITY = 'perun.cesnet.cz'
"""Default authority that issues the group attribute URIs."""

CESNET_OPENID_REMOTE_SESSION_KEY = 'identity.cesnet_provides'
"""Name of session key where CESNET roles are stored."""

OAUTHCLIENT_CESNET_OPENID_GROUP_VALIDATOR = 'cesnet_openid_remote.groups.validate_group_uri'
"""Function used to validate external group URIs."""

OAUTHCLIENT_CESNET_OPENID_GROUP_PARSER = 'cesnet_openid_remote.groups.parse_group_uri'
"""Function used to parse external group URIs to (UUID, extra_data) pairs."""

OAUTHCLIENT_CESNET_OPENID_STATE_TRANSFORM = 'cesnet_openid_remote.state.transform_state_data'
"""Function used to validate external group URIs."""

OAUTHCLIENT_CESNET_OPENID_PROTECTED_ROLES = ['admin']
"""Role names that shouldn't be managed/(un)assigned to users by this extension."""

OAUTHCLIENT_REST_REMOTE_APPS = dict(
    eduid=CesnetOpenIdRemote().remote_app(),
)
