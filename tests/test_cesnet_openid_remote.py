# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask
from flask_oauthlib.client import OAuth as FlaskOAuth
from invenio_oauthclient import InvenioOAuthClient
from invenio_openid_connect.remote import LazyOAuthRemoteApp

from cesnet_openid_remote import CESNETOpenIDRemote, CesnetOpenIdRemote


def test_version():
    """Test version import."""
    from cesnet_openid_remote import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = CESNETOpenIDRemote(app)
    assert 'cesnet-openid-remote' in app.extensions

    app = Flask('testapp')
    ext = CESNETOpenIDRemote()
    assert 'cesnet-openid-remote' not in app.extensions
    ext.init_app(app)
    assert 'cesnet-openid-remote' in app.extensions


class _CustomCesnetRemoteApp(CesnetOpenIdRemote):
    """Custom OAuthRemoteApp used for testing."""


def test_standard_remote_app_factory(base_app):
    """Test standard remote_app class."""
    base_app.config.update(
        OAUTHCLIENT_REMOTE_APPS=dict(
            custom_app=_CustomCesnetRemoteApp().remote_app()
        )
    )
    FlaskOAuth(base_app)
    InvenioOAuthClient(base_app)
    CESNETOpenIDRemote(base_app)
    assert isinstance(
        base_app.extensions['oauthlib.client'].remote_apps['custom_app'],
        LazyOAuthRemoteApp)
    assert not isinstance(
        base_app.extensions['oauthlib.client'].remote_apps['custom_app'],
        _CustomCesnetRemoteApp)
