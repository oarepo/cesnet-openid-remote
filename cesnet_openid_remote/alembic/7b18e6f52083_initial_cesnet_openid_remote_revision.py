#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Initial cesnet openid remote revision."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b18e6f52083'
down_revision = None
branch_labels = ('cesnet_openid_remote',)
depends_on = None


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
