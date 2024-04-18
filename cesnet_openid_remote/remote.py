# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import datetime
from dateutil.relativedelta import relativedelta
from invenio_oauthclient.contrib.settings import OAuthSettingsHelper


class EinfraOAuthSettingsHelper(OAuthSettingsHelper):
    """e-INFRA AAI Remote Auth backend settings."""

    def __init__(
        self,
        title=None,
        description=None,
        base_url=None,
        app_key=None,
        icon=None,
        precedence_mask=None,
        signup_options=None,
        content_type="application/json",
        scopes="openid profile email eduperson_entitlement isCesnetEligibleLastSeen"
    ):
        """Constructor."""
        super().__init__(
            title or "e-INFRA AAI",
            description or "Authentication and authorisation for services within e-INFRA CZ.",
            base_url or "https://login.cesnet.cz/oidc/",
            app_key or "EINFRA_AAI_APP_CREDENTIALS",
            icon=icon or "fa fa-cloud",
            content_type=content_type,
            request_token_params={"scope": scopes},
            access_token_url="https://login.cesnet.cz/oidc/token",
            authorize_url="https://login.cesnet.cz/oidc/authorize",
            precedence_mask=precedence_mask,
            signup_options=signup_options,
        )

        self._handlers = dict(
            authorized_handler="invenio_oauthclient.handlers:authorized_signup_handler",
            disconnect_handler="cesnet_openid_remote.handlers:disconnect_handler",
            signup_handler=dict(
                info="cesnet_openid_remote.handlers:account_info",
                info_serializer="cesnet_openid_remote.handlers:account_info_serializer",
                setup="cesnet_openid_remote.handlers:account_setup",
                view="cesnet_openid_remote.handlers:signup_handler",
            ),
        )

        self._rest_handlers = dict(
            authorized_handler="invenio_oauthclient.handlers.rest"
            ":authorized_signup_handler",
            disconnect_handler="cesnet_openid_remote.handlers"
            ":disconnect_rest_handler",
            signup_handler=dict(
                info="cesnet_openid_remote.handlers:account_info",
                info_serializer="cesnet_openid_remote.handlers:account_info_serializer",
                setup="cesnet_openid_remote.handlers:account_setup",
                view="invenio_oauthclient.handlers.rest:signup_handler",
            ),
            response_handler="invenio_oauthclient.handlers.rest"
            ":default_remote_response_handler",
            authorized_redirect_url="/",
            disconnect_redirect_url="/",
            signup_redirect_url="/",
            error_redirect_url="/",
        )

    def get_handlers(self):
        """Return auth handlers."""
        return self._handlers

    def get_rest_handlers(self):
        """Return auth REST handlers."""
        return self._rest_handlers


_einfra_app = EinfraOAuthSettingsHelper()

BASE_APP = _einfra_app.base_app
REMOTE_APP = _einfra_app.remote_app
"""e-INFRA AAI OpenID remote application configuration."""
REMOTE_REST_APP = _einfra_app.remote_rest_app
"""e-INFRA AAI OpenID remote rest application configuration."""

