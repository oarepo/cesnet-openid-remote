# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


import jwt
from invenio_db import db
from invenio_accounts.models import User, UserIdentity
from invenio_oauthclient.signals import account_info_received
from invenio_oauthclient.utils import oauth_link_external_id
from invenio_oauthclient import current_oauthclient
from cesnet_openid_remote.communities import (
    account_info_link_perun_groups,
    link_perun_groups,
)


def _verify_eligibility(isCesnetEligibleLastSeen):
    last_eligible_date = datetime.datetime.fromtimestamp(int(isCesnetEligibleLastSeen))
    eligible_treshold = datetime.datetime.now() - relativedelta(years=1)
    if last_eligible_date < eligible_treshold:
        raise AttributeError


def account_info_serializer(remote, resp):
    """
    Serialize the account info response object.

    :param remote: The remote application.
    :param resp: The response of the `authorized` endpoint.

    :returns: A dictionary with serialized user information.
    """
    decoded_token = jwt.decode(resp["id_token"], options={"verify_signature": True})

    return {
        "external_id": decoded_token["sub"],
        "external_method": remote.name,
        "user": {
            "email": decoded_token.get("email"),
            "profile": {
                "full_name": decoded_token.get("name"),
            },
        },
    }


def account_info(remote, resp):
    """
    Retrieve remote account information used to find local user.

    It returns a dictionary with the following structure:
        {
            'external_id': 'sub',
            'external_method': 'perun',
            'user': {
                'email': 'Email address',
                'profile': {
                    'full_name': 'Full Name',
                },
            }
        }
    :param remote: The remote application.
    :param resp: The response of the `authorized` endpoint.

    :returns: A dictionary with the user information.
    """
    handlers = current_oauthclient.signup_handlers[remote.name]
    handler_resp = handlers["info_serializer"](resp)

    return handler_resp


def account_setup(remote, token, resp):
    """
    Perform additional setup after user have been logged in.

    :param remote: The remote application.
    :param token: The token value.
    :param resp: The response.
    """
    decoded_token = jwt.decode(resp["id_token"], options={"verify_signature": True})

    with db.session.begin_nested():
        token.remote_account.extra_data = {
            "full_name": decoded_token["name"],
        }

        user = token.remote_account.user

        # Create user <-> external id link.
        oauth_link_external_id(user, {"id": decoded_token["sub"], "method": "perun"})

    link_perun_groups(remote, user)


# During overlay initialization.
@account_info_received.connect
def autocreate_user(remote, token=None, response=None, account_info=None):
    assert account_info is not None

    email = account_info["user"]["email"]
    id, method = account_info["external_id"], account_info["external_method"]
    user_profile = {
        "affiliations": "",
        "full_name": account_info["user"]["profile"]["full_name"],
    }

    user_identity = UserIdentity.query.filter_by(id=id, method=method).one_or_none()
    if not user_identity:
        user = User(email=email, active=True, user_profile=user_profile)

        """
        Workaround note:

        When we create a user, we need to set 'confirmed_at' property,
        because contrary to the default security settings (False),
        the config variable SECURITY_CONFIRMABLE is set to True.
        Without setting 'confirmed_at' to some value, it is impossible to log in.
        """
        user.confirmed_at = datetime.datetime.now()

        try:
            db.session.add(user)
        except:
            db.session.rollback()
            raise
        finally:
            db.session.commit()

        user_identity = UserIdentity(id=id, method=method, id_user=user.id)
        try:
            db.session.add(user_identity)
        except:
            db.session.rollback()
            raise
        finally:
            db.session.commit()

    else:
        assert user_identity.user is not None

        user_identity.user.email = email
        user_identity.user.user_profile = user_profile

        try:
            db.session.add(user_identity.user)
        except:
            db.session.rollback()
            raise
        finally:
            db.session.commit()


account_info_received.connect(account_info_link_perun_groups)
