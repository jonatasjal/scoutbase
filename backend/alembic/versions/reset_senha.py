"""fase 15 - colunas de redefinicao de senha (reset_token_hash / reset_token_expira)

Revision ID: b15f2a7c9d01
Revises: 7a282b4eb5c0
"""
from alembic import op
import sqlalchemy as sa

# Identificadores do alembic (como nº de série dest mudança)
revision = 'b15f2a7c9d01'
down_revision = '7a282b4eb5c0'   # a migration anterior (fase 6)
branch_labels = None
depends_on = None

def upgrade() -> None:
    # nullable=True = coluna pode ficar vazia (só quem pediu reset preenche)
    op.add_column('usuario', sa.Column('reset_token_hash', sa.String(length=255), nullable=True))
    op.add_column('usuario', sa.Column('reset_token_expira', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Desfazer = apagar as colunas (o caminho de volta, caso a mudança dê errado)
    op.drop_column('usuario', 'reset_token_expira')
    op.drop_column('usuario', 'reset_token_hash')