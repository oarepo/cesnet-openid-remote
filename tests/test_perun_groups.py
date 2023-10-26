import importlib
from unittest.mock import Mock

from invenio_access.permissions import system_identity
from invenio_communities import current_communities
from invenio_search.engine import dsl

from cesnet_openid_remote.remote import link_perun_groups

# userinfo url 'https://login.cesnet.cz/oidc/'


def get_user_community_roles(user):
    members_service = current_communities.service.members
    search = members_service._search(
        "search",
        system_identity,
        {},
        None,
        extra_filter=dsl.Q("term", **{"user.id": str(user.id)}),
    )
    result = search.execute()
    ret = []
    for hit in result:
        ret.append((hit["community_id"], hit["role"]))
    return ret


def token_getter_mock(remote, token=""):
    return ["token"]


def set_remote(return_userinfo_fixture, monkeypatch):
    remote = Mock()
    remote.consumer_key = "333e0e21-83bc-414f-bb4c-6df622fc1331"
    remote.base_url = "https://login.cesnet.cz/oidc/"

    remote.get.side_effect = return_userinfo_fixture
    module = importlib.import_module("cesnet_openid_remote.remote")
    monkeypatch.setattr(module, "token_getter", token_getter_mock)
    return remote


def test_two_communities(
    community_with_aai_mapping_cf,
    community2_with_aai_mapping_cf,
    users,
    return_userinfo_two_communities,
    monkeypatch,
    search_clear,
):
    remote = set_remote(return_userinfo_two_communities, monkeypatch)
    user = users["curator"]

    roles_before = get_user_community_roles(user)

    link_perun_groups(
        remote,
        token=None,
        response=None,
        account_info={"user": {"email": "curator@curator.org"}},
    )

    roles_after = get_user_community_roles(user)
    assert len(roles_before) == 0
    assert len(roles_after) == 2

    link_perun_groups(
        remote,
        token=None,
        response=None,
        account_info={"user": {"email": "curator@curator.org"}},
    )
    roles_after_repeat = get_user_community_roles(user)
    assert len(roles_after_repeat) == 2


def test_adding_groups(
    community_with_aai_mapping_cf,
    users,
    return_userinfo_both,
    monkeypatch,
    search_clear,
):
    remote = set_remote(return_userinfo_both, monkeypatch)
    user = users["curator"]

    roles_before = get_user_community_roles(user)

    link_perun_groups(
        remote,
        token=None,
        response=None,
        account_info={"user": {"email": "curator@curator.org"}},
    )

    roles_after = get_user_community_roles(user)
    assert len(roles_before) == 0
    assert len(roles_after) == 1
    assert roles_after[0][1] == "curator"

    link_perun_groups(
        remote,
        token=None,
        response=None,
        account_info={"user": {"email": "curator@curator.org"}},
    )
    roles_after_repeat = get_user_community_roles(user)
    assert len(roles_after_repeat) == 1
    assert roles_after_repeat[0][1] == "curator"


def test_remove_groups(
    community_with_aai_mapping_cf,
    users,
    return_userinfo_curator,
    return_userinfo_noone,
    monkeypatch,
    search_clear,
):
    remote = set_remote(return_userinfo_curator, monkeypatch)
    user = users["curator"]

    roles_before = get_user_community_roles(user)

    link_perun_groups(
        remote,
        token=None,
        response=None,
        account_info={"user": {"email": "curator@curator.org"}},
    )

    roles_after = get_user_community_roles(user)
    assert len(roles_before) == 0
    assert len(roles_after) == 1
    assert roles_after[0][1] == "curator"

    remote.get.side_effect = return_userinfo_noone
    link_perun_groups(
        remote,
        token=None,
        response=None,
        account_info={"user": {"email": "curator@curator.org"}},
    )
    roles_after_perun_deletion = get_user_community_roles(user)
    assert len(roles_after_perun_deletion) == 1
