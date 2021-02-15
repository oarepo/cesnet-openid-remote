# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""
from flask import url_for, g, session
from flask_security import login_user, logout_user
from invenio_accounts.models import Role
from invenio_openid_connect.utils import get_dict_from_response

from cesnet_openid_remote import CesnetOpenIdRemote
from cesnet_openid_remote.config import CESNET_OPENID_REMOTE_SESSION_KEY
from cesnet_openid_remote.constants import OPENIDC_GROUPS_KEY
from tests.helpers import mock_response, mock_remote_get, get_state


def test_account_info(app, example_cesnet):
    # TODO: implement tests after group filtering happens here
    pass


def test_fetch_extra_data(app, example_cesnet, models_fixture):
    """Test extra data extraction."""
    example_response, _, _ = example_cesnet
    res = get_dict_from_response(example_response)

    remote = CesnetOpenIdRemote()

    datastore = app.extensions['security'].datastore
    roles = Role.query.all()
    assert len(roles) == 0
    user_info = remote.userinfo_cls(res)
    user_info.username = remote.get_username(user_info)

    extra_data = remote.fetch_extra_data(user_info, user_info['sub'])

    # Check roles were created for each group
    roles = Role.query.all()
    assert len(roles) == 2
    assert set([r.name for r in roles]) == {'f0c14f62-b19c-447e-b044-c3098cebb426',
                                            '8ece6adb-8677-4482-9aec-5a556c646389'}
    assert set([r.description for r in roles]) == {'example', 'example:subgroup'}
    assert set([r.name for r in roles]) == set(extra_data[OPENIDC_GROUPS_KEY])
    extra_data['external_id'] = 'abcd1234@einfra.cesnet.cz'


def test_account_setup(app, example_cesnet, models_fixture):
    """Test account setup after login."""
    with app.test_client() as c:
        ioc = app.extensions['oauthlib.client']

        # Ensure remote apps have been loaded (due to before first request)
        resp = c.get(url_for('invenio_oauthclient.rest_login',
                             remote_app='cesnet'))
        assert resp.status_code == 302

        example_response, example_token, example_account_info = \
            example_cesnet

        mock_response(app.extensions['oauthlib.client'], 'cesnet',
                      example_token)
        mock_remote_get(ioc, 'cesnet', example_response)

        resp = c.get(url_for(
            'invenio_oauthclient.rest_authorized',
            remote_app='cesnet', code='test',
            state=get_state('cesnet')))
        assert resp.status_code == 302
        assert resp.location == 'http://localhost/api/oauth/complete/?message=Successfully+authorized.&code=200'
        assert len(g.identity.provides) == 4

    datastore = app.extensions['invenio-accounts'].datastore
    user = datastore.find_user(email='john.doe@example.oarepo.org')
    assert user
    assert len(user.roles) == 2


def test_disconnect(app, models_fixture, example_cesnet):
    with app.test_client() as c:
        ioc = app.extensions['oauthlib.client']

        # Ensure remote apps have been loaded (due to before first request)
        resp = c.get(url_for('invenio_oauthclient.rest_login',
                             remote_app='cesnet'))
        assert resp.status_code == 302

        example_response, example_token, example_account_info = \
            example_cesnet

        mock_response(app.extensions['oauthlib.client'], 'cesnet',
                      example_token)
        mock_remote_get(ioc, 'cesnet', example_response)

        resp = c.get(url_for(
            'invenio_oauthclient.rest_authorized',
            remote_app='cesnet', code='test',
            state=get_state('cesnet')))
        assert resp.status_code == 302
        assert resp.location == 'http://localhost/api/oauth/complete/?message=Successfully+authorized.&code=200'
        assert len(g.identity.provides) == 4

        # Test user loses all role & id provides both from identity & session on logout
        logout_user()
        assert len(g.identity.provides) == 0
        assert OPENIDC_GROUPS_KEY not in session
        assert CESNET_OPENID_REMOTE_SESSION_KEY not in session

        datastore = app.extensions['invenio-accounts'].datastore
        user = datastore.find_user(email='john.doe@example.oarepo.org')

        # Test user is assigned to correct Invenio roles
        assert len(user.roles) == 2
        login_user(user)

        # Test user regains correct provides on login
        assert len(g.identity.provides) == 4

        # Test remove remote account and from remote groups
        CesnetOpenIdRemote().handle_disconnect(ioc.remote_apps['cesnet'])
        assert len(user.roles) == 0
        assert len(g.identity.provides) == 0
