"""empty message

Revision ID: fdca80e072ee
Revises: c754a989724f
Create Date: 2018-01-03 20:35:43.306033

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdca80e072ee'
down_revision = 'c754a989724f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('intents', sa.Column('modified', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('intents', 'modified')
    # ### end Alembic commands ###
