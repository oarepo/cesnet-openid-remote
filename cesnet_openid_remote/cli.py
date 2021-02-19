# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
import click
from click import UUID
from flask.cli import with_appcontext
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from oarepo_micro_api.cli import with_api

from cesnet_openid_remote.models import CesnetGroup
from cesnet_openid_remote.proxies import current_cesnet_openid


def _prepare_group_role(group_uuid, role_name):
    group = current_cesnet_openid.find_group(group_uuid)
    if not group:
        click.secho(f'CESNET group with UUID {group_uuid} does not exist', fg='red')
        exit(2)
    role = current_datastore.find_role(role_name)
    if not role:
        click.secho(f'Role {role_name} does not exist', fg='red')
        exit(3)
    return group, role


@click.group()
def cesnet_group():
    """Management commands for CESNET external group mappings."""


@cesnet_group.command('create')
@click.argument('uri')
@with_appcontext
@with_api
def create(uri):
    """Create an external CESNET group."""
    if not current_cesnet_openid.validate_group_uri(uri):
        click.secho(f'Group URI is invalid', fg='red')

    uuid, attrs = current_cesnet_openid.parse_group_uri(uri)
    created = current_cesnet_openid.create_group(uuid, attrs, uri)
    db.session.commit()

    click.secho(f'Successfully Created: {created}', fg='green')


@cesnet_group.command('add')
@click.argument('group_uuid')
@click.argument('role_name')
@with_appcontext
@with_api
def add(group_uuid, role_name):
    """Add a CESNET group to Invenio Role."""
    group, role = _prepare_group_role(group_uuid, role_name)
    current_cesnet_openid.add_group_role(group, role)
    db.session.commit()
    click.secho(f'Roles assigned with {group}: {group.roles}', fg='green')


@cesnet_group.command('remove')
@click.argument('group_uuid')
@click.argument('role_name')
@with_appcontext
@with_api
def remove(group_uuid, role_name):
    """Remove a CESNET group from an Invenio Role."""
    group, role = _prepare_group_role(group_uuid, role_name)
    current_cesnet_openid.remove_group_role(group, role)
    db.session.commit()
    roles = [r.name for r in group.roles]
    click.secho(f'Roles assigned with {group}: {roles}', fg='green')


@cesnet_group.command('list')
@with_appcontext
@with_api
def list_groups():
    """List external CESNET groups."""
    groups = CesnetGroup.query.all()
    for g in groups:
        roles = [r.name for r in g.roles]
        click.secho('{0.uuid} {0.display_name} -> {1}'.format(g, roles))
