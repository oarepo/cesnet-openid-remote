# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""

from flask import current_app
from urnparse import URN8141, InvalidURNFormatError
from werkzeug.local import LocalProxy

CESNET_OPENID_REMOTE_GROUP_REALM = 'cesnet.cz'
"""Default realm of group attribute URNs."""

CESNET_OPENID_REMOTE_GROUP_AUTHORITY = 'perun.cesnet.cz'
"""Default authority that issues the group attribute URIs."""

gconf = LocalProxy(
    lambda: dict(
        realm=current_app.config.get(
            "CESNET_OPENID_REMOTE_GROUP_REALM",
            CESNET_OPENID_REMOTE_GROUP_REALM),
        authority=current_app.config.get(
            "CESNET_OPENID_REMOTE_GROUP_AUTHORITY",
            CESNET_OPENID_REMOTE_GROUP_AUTHORITY)))


def validate_group_uri(group_uri):
    """Checks if group URI is well-formatted and valid.

       @param group_uri: group URI string
       @returns: True if group URI is valid, False otherwise
    """
    try:
        urn = URN8141.from_string(group_uri)

        if (len(urn.specific_string.parts) != 3) or \
           ([gconf['realm'], 'groupAttributes'] != urn.specific_string.parts[:-1]) or \
           (urn.rqf_component.fragment != gconf['authority']):
            return False
    except InvalidURNFormatError:
        return False

    return True


def parse_group_uri(group_uri):
    """Parses UUID and any extra data from the group URI string.

        @param group_uri: group URI string
        @returns Tuple with (UUID, dict(extra_data)) specification of the group
    """
    urn = URN8141.from_string(group_uri)
    return urn.specific_string.parts[-1], urn.rqf_component.query
