# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""

from . import config
from .constants import OPENIDC_CONFIG


class CESNETOpenIDRemote(object):
    """CESNET-OpenID-Remote extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['cesnet-openid-remote'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('CESNET_OPENID_REMOTE_') or \
               k in ['OAUTHCLIENT_REST_REMOTE_APPS', OPENIDC_CONFIG]:
                app.config.setdefault(k, getattr(config, k))
