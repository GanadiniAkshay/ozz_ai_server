"""empty message

Revision ID: 0a48cf5e89f1
Revises: a41c8adb542f
Create Date: 2017-09-25 20:10:10.547043

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0a48cf5e89f1'
down_revision = 'a41c8adb542f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('intents', 'patterns')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('intents', sa.Column('patterns', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    # ### end Alembic commands ###