# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from invenio_oauthclient.errors import OAuthResponseError


class OAuthCESNETInvalidGroupURI(Exception):
    """External group URI did not match the expected pattern."""

    def __init__(self, uri, *args, **kwargs):
        super(OAuthCESNETInvalidGroupURI, self).__init__('Invalid external group URI',
                                                         uri, *args)


class OAuthCESNETRoleProtected(Exception):
    """External group URI did not match the expected pattern."""


class OAuthCESNETGroupExists(Exception):
    """External group with this URI already exists."""

    def __init__(self, uuid, *args, **kwargs):
        super(OAuthCESNETGroupExists, self).__init__('External group with this UUID already exists',
                                                     uuid, *args)


class OAuthCESNETRejectedAccountError(OAuthResponseError):
    """Define exception for not allowed cesnet group accounts."""
