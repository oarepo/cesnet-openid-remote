# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""

from .remote import CesnetOpenIdRemote
from .ext import CESNETOpenIDRemote
from .version import __version__

__all__ = ('__version__', 'CesnetOpenIdRemote', 'CESNETOpenIDRemote')
