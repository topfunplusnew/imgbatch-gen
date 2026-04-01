create table transactions
(
    user_id            varchar(100) not null
        references users,
    transaction_type   varchar(50)  not null,
    amount             integer,
    points_change      integer,
    balance_after      integer,
    points_after       integer,
    related_order_id   varchar(100),
    related_request_id varchar(100),
    description        varchar(255),
    status             varchar(20),
    extra_data         json,
    id                 varchar(36)  not null
        primary key,
    created_at         timestamp    not null,
    updated_at         timestamp    not null
);

comment on column transactions.user_id is '用户ID';

comment on column transactions.transaction_type is '交易类型: recharge, consumption, refund, subscription, gift, system_adjust';

comment on column transactions.amount is '金额变化(分，正为增加，负为减少)';

comment on column transactions.points_change is '积分变化(正为增加，负为减少)';

comment on column transactions.balance_after is '交易后余额';

comment on column transactions.points_after is '交易后积分';

comment on column transactions.related_order_id is '关联订单ID';

comment on column transactions.related_request_id is '关联请求ID';

comment on column transactions.description is '交易描述';

comment on column transactions.status is '状态: pending, success, failed, cancelled';

comment on column transactions.extra_data is '额外信息(JSON)';

alter table transactions
    owner to postgres;

create index ix_transactions_user_id
    on transactions (user_id);

