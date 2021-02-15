# Create Flask application
"""Minimal Flask application example.
SPHINX-START
First install examples, setup the application and load
fixture data by running:
.. code-block:: console
   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh  # put your OPENIDC client details here before
Next, start the development server:
.. code-block:: console
   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run
and open the example application in your browser:
.. code-block:: console
    $ open http://127.0.0.1:5000/
To reset the example application run:
.. code-block:: console
    $ ./app-teardown.sh
SPHINX-END
"""
from __future__ import absolute_import, print_function

import os

from flask_login import current_user
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from flask_oauthlib.client import OAuth as FlaskOAuth
from invenio_oauthclient import InvenioOAuthClient, InvenioOAuthClientREST
from invenio_oauthclient.views.client import rest_blueprint

from cesnet_openid_remote import CESNETOpenIDRemote
from flask import Flask, redirect, url_for
from flask_babelex import Babel

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db'
)

app.config.update(
    ACCOUNTS_USE_CELERY=False,
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND='memory',
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND='cache',
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY='CHANGE_ME',
    SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

Babel(app)
InvenioDB(app)
InvenioAccounts(app)
FlaskOAuth(app)
InvenioOAuthClient(app)
InvenioOAuthClientREST(app)
CESNETOpenIDRemote(app)

app.register_blueprint(rest_blueprint)


@app.route('/cesnet')
def cesnet():
    """Home page: try to print user email or redirect to login with cern."""
    if not current_user.is_authenticated:
        return redirect(url_for('invenio_oauthclient.rest_login',
                                remote_app='eduid'))

    return 'hello {}'.format(current_user)
