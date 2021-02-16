# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from invenio_oauthclient.utils import obj_or_import_string
from invenio_openid_connect.signals import prepare_state_view_data

from . import config
from .constants import OPENIDC_CONFIG
from .state import transform_state_data


class CESNETOpenIDRemote(object):
    """CESNET-OpenID-Remote extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.connect_signals(app)
        app.extensions['cesnet-openid-remote'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('CESNET_OPENID_REMOTE_') or \
                k in ['OAUTHCLIENT_REST_REMOTE_APPS', OPENIDC_CONFIG]:
                app.config.setdefault(k, getattr(config, k))

    def connect_signals(self, app):
        state_transformer = obj_or_import_string(
            app.config.get(
                "OAUTHCLIENT_CESNET_OPENID_STATE_TRANSFORM", transform_state_data))
        prepare_state_view_data.connect(state_transformer)
