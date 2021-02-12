# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from flask import Flask

from cesnet_openid_remote import CESNETOpenIDRemote


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
