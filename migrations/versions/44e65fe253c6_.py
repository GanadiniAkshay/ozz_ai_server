"""empty message

Revision ID: 44e65fe253c6
Revises: 4098098fdff5
Create Date: 2017-09-04 21:35:55.350467

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44e65fe253c6'
down_revision = '4098098fdff5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('intents', sa.Column('calls', sa.Integer(), nullable=True))
    op.add_column('intents', sa.Column('responses', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('intents', 'responses')
    op.drop_column('intents', 'calls')
    # ### end Alembic commands ###
