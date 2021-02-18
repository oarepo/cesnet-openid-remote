[![image][0]][1]
[![image][2]][3]
[![image][4]][5]
[![image][6]][7]

  [0]: https://github.com/oarepo/cesnet-openid-remote/workflows/CI/badge.svg
  [1]: https://github.com/oarepo/cesnet-openid-remote/actions?query=workflow%3ACI
  [2]: https://img.shields.io/github/tag/oarepo/cesnet-openid-remote.svg
  [3]: https://github.com/oarepo/cesnet-openid-remote/releases
  [4]: https://img.shields.io/pypi/dm/cesnet-openid-remote.svg
  [5]: https://pypi.python.org/pypi/cesnet-openid-remote
  [6]: https://img.shields.io/github/license/oarepo/cesnet-openid-remote.svg
  [7]: https://github.com/oarepo/cesnet-openid-remote/blob/master/LICENSE


# CESNET OIDC Auth backend for OARepo

This remote backend is appropriate for e.g. a SPA application which communicates
with Invenio via REST calls. It also manages mapping of external CESNET (Perun) groups
onto internal Invenio roles and Invenio user-role synchronization using this mapping.

## Installation

Cesnet OpenID Remote is on PyPI so all you need is:

``` console
$ pip install cesnet-openid-remote
```

Then run the following to ensure `cesnet_group` and `cesnet_group_role` mapping database tables
are created:
```console
$ invenio alembic upgrade heads
```

## Configuration

1. Register a new application with CESNET OIDC Provider. When registering the
   application ensure that the *Redirect URI* points to:
```url
https://<my_invenio_site>:5000/api/oauth/authorized/eduid/
```
2. Grab the *Client ID* and *Client Secret* after registering the application
   and add them to your ENVIRONMENT (`.env`):
```python
OPENIDC_KEY=*Client ID*
OPENIDC_SECRET=*Client Secret*
```
4. Now access the login page from your SPA using CESNET OAuth:
```javascript
    window.location =
    "https://<my_invenio_site>:5000/api/oauth/login/eduid?next=<my_next_page>";
```
By default the CESNET module will try first look if a link already exists
between an eduID account and a user. If no link is found, it will be created.
Any external Perun groups will be automatically linked to invenio roles on
each login.
For more details you can play with a :doc:`working example <examplesapp>`.

If you wish to prevent this module from managing (adding/removing users to/from role)
certain Invenio roles, configure such roles in:

```python
OAUTHCLIENT_CESNET_OPENID_PROTECTED_ROLES = ['admin']
"""Role names that shouldn't be managed/(un)assigned to users by this extension."""
```

## CLI

To manage CESNET group to Invenio Role mappings you can use the following CLI command group:
```
$ invenio cesnet:groups --help
Usage: invenio cesnet:group [OPTIONS] COMMAND [ARGS]...

  Management commands for CESNET external group mappings.

Options:
  --help  Show this message and exit.

Commands:
  add     Add a CESNET group to Invenio Role.
  create  Create an external CESNET group.
  list    List external CESNET groups.
  remove  Remove a CESNET group from an Invenio Role.
```

## Customization

To customize group handling and validation, refer to your custom validation and parse
functions using the following config values:

````python
OAUTHCLIENT_CESNET_OPENID_GROUP_VALIDATOR = 'cesnet_openid_remote.groups.validate_group_uri'
"""Function used to validate external group URI."""

OAUTHCLIENT_CESNET_OPENID_GROUP_PARSER = 'cesnet_openid_remote.groups.parse_group_uri'
"""Function used to parse external group URI to (UUID, extra_data) pair."""
````

Further documentation is available on
https://cesnet-openid-remote.readthedocs.io/

Copyright (C) 2021 CESNET.

CESNET-OpenID-Remote is free software; you can redistribute it and/or
modify it under the terms of the MIT License; see LICENSE file for more
details.
