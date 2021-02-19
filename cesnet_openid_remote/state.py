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
    return state
