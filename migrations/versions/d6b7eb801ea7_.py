"""empty message

Revision ID: d6b7eb801ea7
Revises: aab555e68b46
Create Date: 2017-11-07 18:13:43.200069

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd6b7eb801ea7'
down_revision = 'aab555e68b46'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('analytics', 'is_human')
    op.drop_column('analytics', 'user_data')
    op.drop_column('analytics', 'source')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('analytics', sa.Column('source', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('analytics', sa.Column('user_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('analytics', sa.Column('is_human', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
