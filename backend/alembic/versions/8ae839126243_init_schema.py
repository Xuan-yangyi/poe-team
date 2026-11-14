"""init_schema

Revision ID: 8ae839126243
Revises:
Create Date: 2026-11-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8ae839126243'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. material
    op.create_table(
        'material',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('material_code', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=False, default=''),
        sa.Column('unit', sa.String(20), nullable=False, default='pcs'),
        sa.Column('std_loss_rate', sa.Numeric(5, 4), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. material_alias
    op.create_table(
        'material_alias',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('alias_code', sa.String(50), nullable=False),
        sa.Column('source', sa.String(50), nullable=False, default='idh'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('material_id', 'alias_code', name='uq_material_alias'),
    )

    # 3. lot
    op.create_table(
        'lot',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('lot_no', sa.String(50), nullable=False, unique=True),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('wafer_lot', sa.String(50), nullable=False, default=''),
        sa.Column('assembly_lot', sa.String(50), nullable=False, default=''),
        sa.Column('date_code', sa.String(10), nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. work_order
    op.create_table(
        'work_order',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_no', sa.String(30), nullable=False, unique=True),
        sa.Column('idh_id', sa.String(50), nullable=False, index=True),
        sa.Column('customer_id', sa.String(50), nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('confirmed_due_date', sa.Date, nullable=True),
        sa.Column('bom_ver', sa.String(20), nullable=False, default=''),
        sa.Column('settle_mode', sa.String(20), nullable=False, default='purchase'),
        sa.Column('priority', sa.SmallInteger, nullable=False, default=5),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. wo_line
    op.create_table(
        'wo_line',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('line_no', sa.SmallInteger, nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('qty_ordered', sa.Integer, nullable=False),
        sa.Column('qty_shipped', sa.Integer, nullable=False, default=0),
        sa.Column('qty_received', sa.Integer, nullable=False, default=0),
        sa.Column('qty_consumed', sa.Integer, nullable=False, default=0),
        sa.Column('unit_price', sa.Numeric(12, 4), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('wo_id', 'line_no', name='uq_wo_line'),
    )

    # 6. shipment
    op.create_table(
        'shipment',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('dn_no', sa.String(30), nullable=False, unique=True),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('idh_id', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('eta', sa.Date, nullable=True),
        sa.Column('carrier', sa.String(100), nullable=False, default=''),
        sa.Column('tracking_no', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. shipment_line
    op.create_table(
        'shipment_line',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('shipment.id'), nullable=False),
        sa.Column('line_no', sa.SmallInteger, nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('container_id', sa.String(50), nullable=False),
        sa.Column('parent_container_id', sa.String(50), nullable=False, default=''),
        sa.Column('container_type', sa.String(20), nullable=False, default='reel'),
        sa.Column('qty_per_container', sa.Integer, nullable=False),
        sa.Column('qty_shipped', sa.Integer, nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('shipment_id', 'line_no', name='uq_shipment_line'),
    )

    # 8. goods_receipt
    op.create_table(
        'goods_receipt',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('dn_no', sa.String(30), nullable=False),
        sa.Column('container_id', sa.String(50), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('qty_received', sa.Integer, nullable=False),
        sa.Column('qty_shipped', sa.Integer, nullable=False),
        sa.Column('diff_reason', sa.String(20), nullable=False, default=''),
        sa.Column('received_by', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('dn_no', 'container_id', name='uq_goods_receipt'),
    )

    # 9. stock_ledger
    op.create_table(
        'stock_ledger',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('idh_id', sa.String(50), nullable=False, default=''),
        sa.Column('owner', sa.String(20), nullable=False, default='factory'),
        sa.Column('status', sa.String(20), nullable=False, default='available'),
        sa.Column('qty_change', sa.Integer, nullable=False),
        sa.Column('qty_after', sa.Integer, nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_id', sa.String(100), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 10. issue
    op.create_table(
        'issue',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('qty', sa.Integer, nullable=False),
        sa.Column('operator', sa.String(100), nullable=False, default=''),
        sa.Column('scan_method', sa.String(20), nullable=False, default='h5'),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 11. wip_report
    op.create_table(
        'wip_report',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('process_code', sa.String(20), nullable=False),
        sa.Column('process_seq', sa.SmallInteger, nullable=False),
        sa.Column('qty_in', sa.Integer, nullable=False),
        sa.Column('qty_out', sa.Integer, nullable=False),
        sa.Column('qty_scrap', sa.Integer, nullable=False, default=0),
        sa.Column('scrap_reason', sa.String(50), nullable=False, default=''),
        sa.Column('reported_by', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 12. fg_receipt
    op.create_table(
        'fg_receipt',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('wo_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('work_order.id'), nullable=False),
        sa.Column('sn', sa.String(100), nullable=False, unique=True),
        sa.Column('qty', sa.Integer, nullable=False, default=1),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('received_by', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 13. recon_period
    op.create_table(
        'recon_period',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('period', sa.String(7), nullable=False),
        sa.Column('idh_id', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, default='open'),
        sa.Column('total_items', sa.Integer, nullable=False, default=0),
        sa.Column('matched', sa.Integer, nullable=False, default=0),
        sa.Column('diff_count', sa.Integer, nullable=False, default=0),
        sa.Column('diff_rate', sa.Numeric(6, 4), nullable=False, default=0),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('period', 'idh_id', name='uq_recon_period'),
    )

    # 14. recon_item
    op.create_table(
        'recon_item',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('recon_period.id'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('material.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('diff_code', sa.String(10), nullable=False),
        sa.Column('qty_a', sa.Integer, nullable=False, default=0),
        sa.Column('qty_b', sa.Integer, nullable=False, default=0),
        sa.Column('qty_c', sa.Integer, nullable=False, default=0),
        sa.Column('qty_diff', sa.Integer, nullable=False, default=0),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('dispute_reason', sa.Text, nullable=False, default=''),
        sa.Column('dispute_attachments', postgresql.JSONB, nullable=False, default=[]),
        sa.Column('dispute_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 15. adjustment
    op.create_table(
        'adjustment',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('adj_no', sa.String(30), nullable=False, unique=True),
        sa.Column('period_id', sa.Integer, sa.ForeignKey('recon_period.id'), nullable=False),
        sa.Column('recon_item_id', sa.Integer, sa.ForeignKey('recon_item.id'), nullable=False),
        sa.Column('lot_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('lot.id'), nullable=False),
        sa.Column('qty_before', sa.Integer, nullable=False),
        sa.Column('qty_after', sa.Integer, nullable=False),
        sa.Column('diff_code', sa.String(10), nullable=False),
        sa.Column('reason', sa.Text, nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('factory_approved_by', sa.String(100), nullable=False, default=''),
        sa.Column('factory_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('idh_approved_by', sa.String(100), nullable=False, default=''),
        sa.Column('idh_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 16. event_log
    op.create_table(
        'event_log',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('aggregate_type', sa.String(50), nullable=False, index=True),
        sa.Column('aggregate_id', sa.String(100), nullable=False, index=True),
        sa.Column('payload', postgresql.JSONB, nullable=False, default={}),
        sa.Column('actor_id', sa.String(100), nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )

    # 17. conversation
    op.create_table(
        'conversation',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('conv_type', sa.String(20), nullable=False, index=True),
        sa.Column('ref_id', sa.String(100), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False, default=''),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 18. conversation_member
    op.create_table(
        'conversation_member',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('conversation.id'), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('conversation_id', 'user_id', name='uq_conv_member'),
    )

    # 19. message
    op.create_table(
        'message',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('conversation.id'), nullable=False),
        sa.Column('sender_id', sa.String(100), nullable=False),
        sa.Column('msg_type', sa.String(20), nullable=False, default='text'),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('parent_msg_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 20. msg_tag
    op.create_table(
        'msg_tag',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('message_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('message.id'), nullable=False),
        sa.Column('tag_type', sa.String(30), nullable=False, index=True),
        sa.Column('tag_value', sa.String(500), nullable=False),
        sa.Column('tagged_by', sa.String(20), nullable=False, default='ai'),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 21. alert
    op.create_table(
        'alert',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('alert_type', sa.String(30), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False, default='warning'),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('detail', sa.Text, nullable=False, default=''),
        sa.Column('ref_type', sa.String(30), nullable=False, default=''),
        sa.Column('ref_id', sa.String(100), nullable=False, default=''),
        sa.Column('status', sa.String(20), nullable=False, default='open', index=True),
        sa.Column('acknowledged_by', sa.String(100), nullable=False, default=''),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(100), nullable=False, default=''),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution', sa.Text, nullable=False, default=''),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # RLS: Enable row-level security on all tenant-isolated tables
    tables_with_tenant = [
        'material', 'material_alias', 'lot', 'work_order', 'wo_line',
        'shipment', 'shipment_line', 'goods_receipt', 'stock_ledger',
        'issue', 'wip_report', 'fg_receipt', 'recon_period', 'recon_item',
        'adjustment', 'event_log', 'conversation', 'conversation_member',
        'message', 'msg_tag', 'alert',
    ]
    for table in tables_with_tenant:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')
        op.execute(f'''
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (tenant_id = current_setting('app.tenant_id', true))
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
        ''')

    # Create indexes
    op.create_index('ix_event_log_aggregate', 'event_log',
                    ['aggregate_type', 'aggregate_id'])
    op.create_index('ix_event_log_created', 'event_log', ['created_at'])
    op.create_index('ix_stock_ledger_material_lot', 'stock_ledger',
                    ['material_id', 'lot_id'])
    op.create_index('ix_message_conv_created', 'message',
                    ['conversation_id', 'created_at'])


def downgrade() -> None:
    for table in [
        'msg_tag', 'message', 'conversation_member', 'conversation',
        'alert', 'adjustment', 'recon_item', 'recon_period',
        'fg_receipt', 'wip_report', 'issue', 'stock_ledger',
        'goods_receipt', 'shipment_line', 'shipment',
        'wo_line', 'work_order', 'lot', 'material_alias', 'material',
        'event_log',
    ]:
        op.drop_table(table)
