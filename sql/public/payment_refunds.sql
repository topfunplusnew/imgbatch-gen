create table payment_refunds
(
    payment_order_id      varchar(100) not null
        references payment_orders (order_id),
    refund_id             varchar(100) not null
        unique,
    refund_amount         integer      not null,
    refund_reason         varchar(255),
    status                varchar(20),
    refund_transaction_id varchar(100),
    refund_time           timestamp,
    created_at            timestamp,
    id                    varchar(36)  not null
        primary key,
    updated_at            timestamp    not null
);

comment on column payment_refunds.payment_order_id is '原支付订单ID';

comment on column payment_refunds.refund_id is '退款单号';

comment on column payment_refunds.refund_amount is '退款金额(分)';

comment on column payment_refunds.refund_reason is '退款原因';

comment on column payment_refunds.status is '状态: pending, success, failed, cancelled';

comment on column payment_refunds.refund_transaction_id is '第三方退款交易ID';

comment on column payment_refunds.refund_time is '退款完成时间';

comment on column payment_refunds.created_at is '创建时间';

alter table payment_refunds
    owner to postgres;

