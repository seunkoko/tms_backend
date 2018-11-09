"""empty message

Revision ID: e62f788dd343
Revises: 90b97df7f038
Create Date: 2018-03-23 21:38:33.232320

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e62f788dd343'
down_revision = '90b97df7f038'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('DriverInfo', 'car_slots',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('DriverInfo', 'car_slots',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
