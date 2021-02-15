# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""
from unittest.mock import MagicMock

from invenio_oauthclient._compat import _create_identifier
from invenio_oauthclient.views.client import serializer


def get_state(app='test'):
    """Get state."""
    return serializer.dumps({'app': app, 'sid': _create_identifier(),
                             'next': None, })


def mock_response(oauth, remote_app='test', data=None):
    """Mock the oauth response to use the remote."""
    oauth.remote_apps[remote_app].handle_oauth2_response = MagicMock(
        return_value=data
    )


def mock_remote_get(oauth, remote_app='test', data=None):
    """Mock the oauth remote get response."""
    oauth.remote_apps[remote_app].get = MagicMock(
        return_value=data
    )
