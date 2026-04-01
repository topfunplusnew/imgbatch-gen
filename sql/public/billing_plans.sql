create table billing_plans
(
    plan_id          varchar(50)  not null
        unique,
    name             varchar(100) not null,
    description      text,
    price            integer      not null,
    original_price   integer,
    duration_days    integer,
    points_included  integer,
    generation_quota integer,
    daily_quota      integer,
    features         json,
    is_active        boolean,
    sort_order       integer,
    badge_text       varchar(50),
    id               varchar(36)  not null
        primary key,
    created_at       timestamp    not null,
    updated_at       timestamp    not null
);

comment on column billing_plans.plan_id is '套餐ID';

comment on column billing_plans.name is '套餐名称';

comment on column billing_plans.description is '套餐描述';

comment on column billing_plans.price is '价格(分)';

comment on column billing_plans.original_price is '原价(分)，用于显示折扣';

comment on column billing_plans.duration_days is '有效天数(NULL表示永久)';

comment on column billing_plans.points_included is '包含积分';

comment on column billing_plans.generation_quota is '生成次数额度(0表示无限制)';

comment on column billing_plans.daily_quota is '每日生成次数额度(0表示无限制)';

comment on column billing_plans.features is '特权列表(JSON数组)';

comment on column billing_plans.is_active is '是否启用';

comment on column billing_plans.sort_order is '排序序号';

comment on column billing_plans.badge_text is '徽章文字(如''热门'')';

alter table billing_plans
    owner to postgres;

