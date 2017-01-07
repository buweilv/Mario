"""initial migration -- Host model Only

Revision ID: 58e3e853aae9
Revises: None
Create Date: 2016-11-26 11:47:41.577621

"""

# revision identifiers, used by Alembic.
revision = '58e3e853aae9'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hosts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('IP', sa.String(length=64), nullable=True),
    sa.Column('password', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('IP')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('hosts')
    ### end Alembic commands ###