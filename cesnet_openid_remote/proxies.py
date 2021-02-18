# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helper proxy to the state object."""

from flask import current_app
from werkzeug.local import LocalProxy

from cesnet_openid_remote.api import CesnetOpenIdRemoteAPI

current_cesnet_openid: CesnetOpenIdRemoteAPI = LocalProxy(
    lambda: current_app.extensions['cesnet-openid-remote'].api
)
"""Proxy to the current CesnetOpenIdRemoteAPI."""
