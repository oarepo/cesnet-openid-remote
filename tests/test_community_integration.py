# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""
from flask import url_for, g

from tests.helpers import mock_response, mock_remote_get, get_state


def test_communities_state_transform(communities_app, example_cesnet, community):
    """Test state transform handler."""
    with communities_app.test_client() as c:
        ioc = communities_app.extensions['oauthlib.client']

        # Ensure remote apps have been loaded (due to before first request)
        resp = c.get(url_for('invenio_oauthclient.rest_login',
                             remote_app='cesnet'))
        assert resp.status_code == 302

        example_response, example_token, example_account_info = \
            example_cesnet

        mock_response(communities_app.extensions['oauthlib.client'], 'cesnet',
                      example_token)
        mock_remote_get(ioc, 'cesnet', example_response)

        resp = c.get(url_for(
            'invenio_oauthclient.rest_authorized',
            remote_app='cesnet', code='test',
            state=get_state('cesnet')))
        assert resp.status_code == 302
        assert resp.location == 'http://localhost/api/oauth/complete/?message=Successfully+authorized.&code=200'
        assert len(g.identity.provides) == 4

        resp = c.get(url_for('invenio_openid_connect.state'))
        assert resp.status_code == 200

        user_info = resp.json
        assert 'user' in user_info
        assert len(user_info['user']['roles']) == 2
        assert user_info['user']['roles'] == [
            {'id': 'f0c14f62-b19c-447e-b044-c3098cebb426', 'label': 'Community Title - member'},
            {'id': '8ece6adb-8677-4482-9aec-5a556c646389', 'label': 'Community Title - curator'}]
