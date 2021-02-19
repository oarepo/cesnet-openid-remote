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
from invenio_accounts.proxies import current_datastore
from invenio_oauthclient.models import RemoteAccount
from invenio_openid_connect.utils import get_dict_from_response

from cesnet_openid_remote import CesnetOpenIdRemote
from cesnet_openid_remote.config import CESNET_OPENID_REMOTE_SESSION_KEY
from cesnet_openid_remote.constants import OPENIDC_GROUPS_KEY
from cesnet_openid_remote.models import CesnetGroup
from tests.helpers import mock_response, mock_remote_get, get_state


def _login_user(app, example_cesnet, c):
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


def test_fetch_extra_data(app, example_cesnet, cesnet_groups, users_fixture):
    """Test extra data extraction."""
    example_response, _, _ = example_cesnet
    res = get_dict_from_response(example_response)

    remote = CesnetOpenIdRemote()

    user_info = remote.userinfo_cls(res)
    user_info.username = remote.get_username(user_info)

    extra_data = remote.fetch_extra_data(user_info, user_info['sub'])

    # Test only valid group URIs remained in extra_data
    assert len(extra_data[OPENIDC_GROUPS_KEY]) == 2
    assert set(extra_data[OPENIDC_GROUPS_KEY]) == {
        'urn:geant:cesnet.cz:groupAttributes:f0c14f62-b19c-447e-b044-c3098cebb426?displayName=example#perun.cesnet.cz',
        'urn:geant:cesnet.cz:groupAttributes:8ece6adb-8677-4482-9aec-5a556c646389?displayName=example:subgroup#perun.cesnet.cz'
    }

    assert extra_data['external_id'] == 'abcd1234@einfra.cesnet.cz'


def test_remote_groups_and_extra_data(app, example_cesnet, users_fixture):
    """Test get remote groups and extra data."""
    remote = CesnetOpenIdRemote()
    user = current_datastore.find_user(email='john.doe@example.oarepo.org')

    with app.test_client() as c:
        _login_user(app, example_cesnet, c)

        ra = RemoteAccount.query.first()
        assert ra

        groups = remote.remote_groups_and_extra_data(
            ra, dict(user_info=example_cesnet[2], user_id=user.id))

        assert groups
        assert len(groups) == 2
        assert set(groups) == {
            'urn:geant:cesnet.cz:groupAttributes:f0c14f62-b19c-447e-b044-c3098cebb426?displayName=example#perun.cesnet.cz',
            'urn:geant:cesnet.cz:groupAttributes:8ece6adb-8677-4482-9aec-5a556c646389?displayName=example:subgroup#perun.cesnet.cz'
        }
        assert OPENIDC_GROUPS_KEY in ra.extra_data
        assert ra.extra_data
        assert len(ra.extra_data[OPENIDC_GROUPS_KEY]) == len(groups)


def test_account_setup(communities_app, community, example_cesnet, cesnet_groups, users_fixture):
    """Test account setup after login."""
    group = CesnetGroup.query.first()
    role = Role.query.first()
    group.roles.append(role)

    with communities_app.test_client() as c:
        _login_user(communities_app, example_cesnet, c)

        user = current_datastore.find_user(email='john.doe@example.oarepo.org')
        assert user
        assert len(user.roles) == 1
        assert user.roles[0] == role


def test_disconnect(communities_app, community, cesnet_groups, users_fixture, example_cesnet, protected_roles):
    user = current_datastore.find_user(email='john.doe@example.oarepo.org')
    role = Role.query.first()
    extra_role = Role.query.all()[1]
    group = CesnetGroup.query.first()

    user.roles.append(protected_roles[0])
    user.roles.append(extra_role)
    user.roles.append(role)
    group.roles.append(role)

    assert len(user.roles) == 3
    assert len(group.roles) == 1

    with communities_app.test_client() as c:
        _login_user(communities_app, example_cesnet, c)

        remote = communities_app.extensions['oauthlib.client'].remote_apps['cesnet']
        # Test remove remote account and from remote groups
        CesnetOpenIdRemote().handle_disconnect(remote)
        assert len(user.roles) == 1  # only protected role should remain
        assert protected_roles[0] in user.roles
        assert len(group.roles) == 1
        assert group.roles[0] == role
