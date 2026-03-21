create table payment_orders
(
    order_id        varchar(100) not null
        unique,
    user_id         varchar(100) not null
        references users,
    order_type      varchar(20)  not null,
    amount          integer      not null,
    plan_id         varchar(50),
    payment_method  varchar(20)  not null,
    payment_channel varchar(50),
    status          varchar(20),
    transaction_id  varchar(100),
    prepay_id       varchar(100),
    qr_code_url     text,
    pay_url         text,
    notify_time     timestamp,
    notify_data     json,
    expire_time     timestamp,
    paid_at         timestamp,
    subject         varchar(255),
    body            text,
    attach          json,
    client_ip       varchar(50),
    user_agent      varchar(500),
    id              varchar(36)  not null
        primary key,
    created_at      timestamp    not null,
    updated_at      timestamp    not null
);

comment on column payment_orders.order_id is '订单号';

comment on column payment_orders.user_id is '用户ID';

comment on column payment_orders.order_type is '订单类型: recharge, subscription';

comment on column payment_orders.amount is '订单金额(分)';

comment on column payment_orders.plan_id is '关联的套餐ID';

comment on column payment_orders.payment_method is '支付方式: wechat, alipay';

comment on column payment_orders.payment_channel is '支付渠道: native, h5, jsapi';

comment on column payment_orders.status is '状态: pending, paid, failed, cancelled, refunded, timeout';

comment on column payment_orders.transaction_id is '第三方交易ID';

comment on column payment_orders.prepay_id is '预支付ID';

comment on column payment_orders.qr_code_url is '支付二维码URL';

comment on column payment_orders.pay_url is '支付跳转URL(H5支付用)';

comment on column payment_orders.notify_time is '支付回调时间';

comment on column payment_orders.notify_data is '回调原始数据';

comment on column payment_orders.expire_time is '订单过期时间';

comment on column payment_orders.paid_at is '支付完成时间';

comment on column payment_orders.subject is '订单标题';

comment on column payment_orders.body is '订单描述';

comment on column payment_orders.attach is '附加数据(JSON)';

comment on column payment_orders.client_ip is '客户端IP';

comment on column payment_orders.user_agent is '用户代理';

alter table payment_orders
    owner to postgres;

create index ix_payment_orders_user_id
    on payment_orders (user_id);

