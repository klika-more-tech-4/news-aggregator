"""tgbot chat_id

Revision ID: 757d04d80adf
Revises: 14e81536afad
Create Date: 2022-10-08 17:57:32.604506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '757d04d80adf'
down_revision = '14e81536afad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('telegram_users', sa.Column('chat_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('telegram_users', 'chat_id')
    # ### end Alembic commands ###
