import datetime
from invenio_db import db
import jwt

from invenio_accounts.models import User, UserIdentity
from invenio_oauthclient import current_oauthclient
from invenio_oauthclient.contrib.settings import OAuthSettingsHelper
from invenio_oauthclient.utils import oauth_link_external_id
from invenio_oauthclient.signals import account_info_received

class PerunOAuthSettingsHelper(OAuthSettingsHelper):
    """
    Default configuration for Perun OAuth provider.
    """

    def __init__(self):
        access_token_url = "https://login.cesnet.cz/oidc/token"
        authorize_url = "https://login.cesnet.cz/oidc/authorize"
        
        super().__init__(
            "Perun",
            "Perun oauth service.",
            "https://login.cesnet.cz/oidc/",
            "PERUN_APP_CREDENTIALS",
            request_token_params={ "scope": "openid profile email" },
            access_token_url=access_token_url,
            authorize_url=authorize_url,
            content_type="application/json",
            precedence_mask=None,
            signup_options=None
            )

        self._handlers = dict(
            authorized_handler="invenio_oauthclient.handlers:authorized_signup_handler",
            signup_handler=dict(
                info="perun_openid_remote.perun:account_info",
                info_serializer="perun_openid_remote.perun:account_info_serializer",
                setup="perun_openid_remote.perun:account_setup",
                view="invenio_oauthclient.handlers:signup_handler",
            ),
        )

        self._rest_handlers = dict(
            authorized_handler="invenio_oauthclient.handlers.rest:authorized_signup_handler",
            signup_handler=dict(
                info="perun_openid_remote.perun:account_info",
                info_serializer="perun_openid_remote.perun:account_info_serializer",
                setup="perun_openid_remote.perun:account_setup",
                view="invenio_oauthclient.handlers.rest:signup_handler",
            ),
            response_handler="invenio_oauthclient.handlers.rest:default_remote_response_handler",
            authorized_redirect_url="/",
            signup_redirect_url="/",
            error_redirect_url="/",
        )

    def get_handlers(self):
        """Return Perun auth handlers."""
        return self._handlers

    def get_rest_handlers(self):
        """Return Perun auth REST handlers."""
        return self._rest_handlers


_perun_app = PerunOAuthSettingsHelper()

"""
Perun OpenID remote app.
"""
REMOTE_APP = _perun_app.remote_app

def account_info_serializer(remote, resp):
    """
    Serialize the account info response object.
    
    :param remote: The remote application.
    :param resp: The response of the `authorized` endpoint.
    
    :returns: A dictionary with serialized user information.
    """
    decoded_token = jwt.decode(resp["id_token"], options={"verify_signature": False})
    
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
    
    return handlers["info_serializer"](resp)

def account_setup(remote, token, resp):
    """
    Perform additional setup after user have been logged in.
    
    :param remote: The remote application.
    :param token: The token value.
    :param resp: The response.
    """
    decoded_token = jwt.decode(resp["id_token"], options={"verify_signature": False})
    
    with db.session.begin_nested():
        token.remote_account.extra_data = {
            "full_name": decoded_token["name"],
        }

        user = token.remote_account.user

        # Create user <-> external id link.
        oauth_link_external_id(user, {"id": decoded_token["sub"], "method": "perun"})
        

# During overlay initialization.
@account_info_received.connect
def autocreate_user(remote, token=None, response=None,
                            account_info=None):
    assert account_info is not None
    
    email = account_info["user"]["email"]
    id, method = account_info["external_id"], account_info["external_method"]
    user_profile = {
        "affiliations": "",
        "full_name": account_info["user"]["profile"]["full_name"]
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
        
        # the user now has id
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