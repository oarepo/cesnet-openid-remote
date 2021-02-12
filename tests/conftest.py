# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
import os
import tempfile

import pytest
from flask import Flask

from cesnet_openid_remote.config import CESNET_APP_CREDENTIALS
from cesnet_openid_remote import CesnetOpenIdRemote


@pytest.fixture
def base_app(request):
    """Flask application fixture without OAuthClient initialized."""
    # allow HTTP for keycloak tests, and create the KEYCLOAK_REMOTE_APP
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    base_url, realm = "http://localhost:8080", "test"

    instance_path = tempfile.mkdtemp()
    base_app = Flask('testapp')
    base_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,
        CACHE_TYPE='simple',
        OAUTHCLIENT_REST_REMOTE_APPS=dict(
            cesnet=CesnetOpenIdRemote().remote_app(),
        ),
        CESNET_APP_CREDENTIALS=CESNET_APP_CREDENTIALS,
        OAUTHCLIENT_STATE_EXPIRES=300,
        # use local memory mailbox
        EMAIL_BACKEND='flask_email.backends.locmem.Mail',
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite://'),
        SERVER_NAME='localhost',
        DEBUG=False,
        SECRET_KEY='TEST',
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
        APP_ALLOWED_HOSTS=['localhost'],
    )
    return base_app
