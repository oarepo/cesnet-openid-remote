# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""
import pytest
from invenio_accounts.models import Role, User
from invenio_accounts.proxies import current_datastore
from invenio_db import db

from cesnet_openid_remote.api import CesnetOpenIdRemoteAPI
from cesnet_openid_remote.constants import OPENIDC_GROUPS_KEY
from cesnet_openid_remote.errors import OAuthCESNETInvalidGroupURI, OAuthCESNETGroupExists, OAuthCESNETRoleProtected
from cesnet_openid_remote.models import CesnetGroup
from cesnet_openid_remote.proxies import current_cesnet_openid
from tests.test_remote import _login_user


def test_init(app, protected_roles):
    api = CesnetOpenIdRemoteAPI(app, None)
    assert len(api.protected_roles) == len(protected_roles)
    assert api.protected_roles[0] == protected_roles[0]


def test_find_group(app, group_uris):
    assert len(CesnetGroup.query.all()) == 2

    # Test find existing group
    gr = current_cesnet_openid.find_group('f0c14f62-b19c-447e-b044-c3098cebb426')
    assert gr is not None
    assert str(gr.uuid) == 'f0c14f62-b19c-447e-b044-c3098cebb426'
    assert gr.display_name == 'example'

    # Test find non-existing group
    gr = current_cesnet_openid.find_group('e0c14f62-b19c-447e-b044-c3098cebb42e')
    assert gr is None


def test_find_or_create_group(app, group_uris):
    # Test find existing group
    gr = current_cesnet_openid.find_or_create_group(group_uris['exists'])
    assert gr is not None
    assert str(gr.uuid) == 'f0c14f62-b19c-447e-b044-c3098cebb426'
    assert gr.display_name == 'example'

    # Test create group
    gr = current_cesnet_openid.find_or_create_group(group_uris['new'])
    assert gr is not None
    assert str(gr.uuid == 'f0c14f62-b19c-447e-b044-c3098c3bb426')
    assert gr.display_name == 'new'

    # Test find invalid URI
    with pytest.raises(OAuthCESNETInvalidGroupURI):
        current_cesnet_openid.find_or_create_group(group_uris['invalid'])


def test_group_create(app, group_uris):
    """Test cesnet group creation using api."""

    # Test create from valid uri
    assert len(CesnetGroup.query.all()) == 2
    res = current_cesnet_openid.create_group(
        'f0c14f62-b19c-447e-b044-c3098ce2b426',
        {'displayName': 'example'}, group_uris['new'])

    assert isinstance(res, CesnetGroup)
    groups = CesnetGroup.query.all()
    assert len(groups) == 3
    assert groups[2] == res
    assert res.display_name == 'example'
    assert res.uri == group_uris['new']
    assert res.uuid == 'f0c14f62-b19c-447e-b044-c3098ce2b426'
    assert len(res.roles) == 0

    # Test create already created group
    with pytest.raises(OAuthCESNETGroupExists):
        current_cesnet_openid.create_group(
            'f0c14f62-b19c-447e-b044-c3098cebb426',
            {'displayName': 'nope'}, group_uris['exists'])


def test_add_group_to_role(communities_app, cesnet_groups, example_cesnet, community, protected_roles, users_fixture):
    """Test adding a cesnet group to invenio role."""
    roles = Role.query.all()
    admin = current_datastore.find_role('admin')
    assert len(roles) == 4
    assert len(CesnetGroup.query.all()) == 2

    group = CesnetGroup.query.first()
    assert len(group.roles) == 0

    # Test add not assigned cesnet group
    current_cesnet_openid.add_group_role(group, roles[0])
    assert len(group.roles) == 1
    assert len(roles[0].cesnet_groups.all()) == 1
    assert group.roles[0] == roles[0]

    # Test add already added group
    current_cesnet_openid.add_group_role(group, roles[0])
    assert len(group.roles) == 1
    assert group.roles[0] == roles[0]

    # Test add to protected roles fails miserably
    with pytest.raises(OAuthCESNETRoleProtected):
        current_cesnet_openid.add_group_role(group, admin)

    # Test remote account role is added on group role addition
    user = User.query.filter_by(email='john.doe@example.oarepo.org').first()
    with communities_app.test_client() as c:
        _login_user(communities_app, example_cesnet, c)
        ra = current_cesnet_openid.remote_accounts(group)[0]
        assert len(ra.user.roles) == 1
        assert ra.user.roles[0] == roles[0]

        current_cesnet_openid.add_group_role(group, roles[1])
        assert len(group.roles) == 2
        assert len(ra.user.roles) == 2
        assert roles[1] in ra.user.roles


def test_rm_role_from_group(communities_app, cesnet_groups, community, protected_roles, example_cesnet, users_fixture):
    """Test removing a role from a cesnet group."""
    group = CesnetGroup.query.first()
    roles = Role.query.all()
    admin = current_datastore.find_role('admin')
    current_cesnet_openid.add_group_role(group, roles[0])
    assert len(group.roles) == 1

    # Remove group from assigned roles
    current_cesnet_openid.remove_group_role(group, roles[0])
    assert len(group.roles) == 0

    # Remove group from non assigned role
    current_cesnet_openid.remove_group_role(group, roles[0])
    assert len(group.roles) == 0

    # Test remove from protected role fails miserably
    group.roles.append(admin)
    assert admin in group.roles
    with pytest.raises(OAuthCESNETRoleProtected):
        current_cesnet_openid.remove_group_role(group, admin)

    # Test remote account role is removed on group role removal
    user = User.query.filter_by(email='john.doe@example.oarepo.org').first()
    group.roles.append(roles[0])
    user.roles.append(roles[0])

    with communities_app.test_client() as c:
        _login_user(communities_app, example_cesnet, c)
        ra = current_cesnet_openid.remote_accounts(group)[0]

        assert len(ra.user.roles) == 1
        assert ra.user.roles[0] == roles[0]
        current_cesnet_openid.remove_group_role(group, roles[0])
        assert set(group.roles) == {admin}
        assert len(ra.user.roles) == 0


def test_add_user_roles(communities_app, community, cesnet_groups, protected_roles, users_fixture):
    """Test role assignment based on user's cesnet groups."""
    group = CesnetGroup.query.first()
    role = Role.query.first()
    user = User.query.filter_by(email='john.doe@example.oarepo.org').first()
    group.roles.append(role)

    assert len(user.roles) == 0

    # Test add to valid role granted by group
    current_cesnet_openid.add_user_roles(user, group.roles)
    assert len(user.roles) == 1
    assert user.roles[0] == role

    # Test add roles from group doesn't add user to protected_role
    group.roles.append(protected_roles[0])
    current_cesnet_openid.add_user_roles(user, group.roles)
    assert len(user.roles) == 1
    assert protected_roles[0] not in user.roles


def test_remove_user_roles(communities_app, community, cesnet_groups, protected_roles, users_fixture):
    """Test removal from roles not granted by any of user's groups."""
    group = CesnetGroup.query.first()
    role = Role.query.first()
    extra_role = Role.query.all()[1]
    user = User.query.filter_by(email='john.doe@example.oarepo.org').first()

    group.roles.append(role)
    user.roles.append(role)
    user.roles.append(extra_role)
    assert len(user.roles) == 2

    # Test remove regular extra roles from user
    current_cesnet_openid.remove_user_roles(user, group.roles)
    assert len(user.roles) == 1
    assert extra_role not in user.roles

    # Test that protected role is not stripped from user
    user.roles.append(protected_roles[0])
    current_cesnet_openid.remove_user_roles(user, group.roles)
    assert len(user.roles) == 2
    assert protected_roles[0] in user.roles

    # Test reversed role removal
    user.roles.append(extra_role)
    assert role in user.roles
    assert role in group.roles

    current_cesnet_openid.remove_user_roles(user, group.roles, reverse=True)
    assert role in group.roles
    assert role not in user.roles
    assert extra_role not in user.roles
    assert len(user.roles) == 1


def test_sync_user_roles(communities_app, community, cesnet_groups, protected_roles, users_fixture):
    """Test synchronization of user roles based on his cesnet groups."""
    group = CesnetGroup.query.first()
    role = Role.query.first()
    extra_role = Role.query.all()[1]
    user = User.query.filter_by(email='john.doe@example.oarepo.org').first()

    group.roles.append(role)
    user.roles.append(extra_role)

    # Test sync adds group role and removes extra role
    current_cesnet_openid.sync_user_roles(user, [group.uri])
    assert len(user.roles) == 1
    assert extra_role not in user.roles
    assert role in user.roles


def test_remote_accounts(communities_app, community, example_cesnet, cesnet_groups, users_fixture):
    group = CesnetGroup.query.first()
    role = Role.query.first()
    user = User.query.filter_by(email='john.doe@example.oarepo.org').first()

    group.roles.append(role)
    user.roles.append(role)

    with communities_app.test_client() as c:
        _login_user(communities_app, example_cesnet, c)

        ras = current_cesnet_openid.remote_accounts(group)
        assert len(ras) == 1
        assert ras[0].user == user
        assert group.uri in ras[0].extra_data[OPENIDC_GROUPS_KEY]
