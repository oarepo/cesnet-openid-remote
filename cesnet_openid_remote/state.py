# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from flask import current_app
from invenio_accounts.proxies import current_datastore


def transform_state_data(user, state):
    """Transforms auth state data where necessary."""
    if 'oarepo-communities' in current_app.extensions:
        from oarepo_communities.api import OARepoCommunity

        for role in state['user']['roles']:
            rol = current_datastore.find_role(role['id'])
            comm = OARepoCommunity.get_community_from_role(rol)
            if comm:
                title = comm.json['title']
                role['label'] = f'{title} - {rol.description}'

    return state
