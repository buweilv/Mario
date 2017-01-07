"""Add Host status column

Revision ID: 5a25f1dd381e
Revises: 58e3e853aae9
Create Date: 2016-11-26 12:58:33.919604

"""

# revision identifiers, used by Alembic.
revision = '5a25f1dd381e'
down_revision = '58e3e853aae9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hosts', sa.Column('status', sa.String(length=64), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('hosts', 'status')
    ### end Alembic commands ###