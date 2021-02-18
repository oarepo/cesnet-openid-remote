# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# CESNET-OpenID-Remote is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CESNET OIDC Auth backend for OARepo"""
from flask_babelex import gettext
from invenio_db import db
from speaklater import make_lazy_gettext
from sqlalchemy_utils import UUIDType

_ = make_lazy_gettext(lambda: gettext)


cesnet_group_role = db.Table(
    'cesnet_group_roles',
    db.Column('group_id', db.Integer(), db.ForeignKey(
        'cesnet_group.id', name='fk_cesnet_group_roles_group_id')),
    db.Column('role_id', db.Integer(), db.ForeignKey(
        'accounts_role.id', name='fk_cesnet_group_roles_role_id')),
)
"""Relationship between CESNET groups and Invenio roles."""


class CesnetGroup(db.Model):
    """Cesnet external group data model."""

    __tablename__ = 'cesnet_group'

    id = db.Column(db.Integer(), primary_key=True)
    uuid = db.Column(UUIDType(), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(255))
    uri = db.Column(db.String(1024), unique=True, nullable=False)
    roles = db.relationship('Role', secondary=cesnet_group_role,
                            backref=db.backref('cesnet_groups', lazy='dynamic'))

    def __str__(self):
        """Return the name and description of the role."""
        return 'CesnetGroup<{0.uuid}> {0.display_name}'.format(self)

    def __repr__(self):
        return self.__str__()


