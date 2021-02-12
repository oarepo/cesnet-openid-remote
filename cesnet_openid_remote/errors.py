# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from invenio_oauthclient.errors import OAuthResponseError


class OAuthCESNETRejectedAccountError(OAuthResponseError):
    """Define exception for not allowed cesnet group accounts."""
