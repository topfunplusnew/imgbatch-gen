create table consumption_records
(
    user_id      varchar(100) not null
        references users,
    request_id   varchar(100),
    model_name   varchar(100),
    provider     varchar(50),
    cost_type    varchar(20)  not null,
    points_used  integer,
    amount       integer,
    prompt       text,
    image_count  integer,
    image_urls   json,
    status       varchar(20),
    error_reason text,
    created_at   timestamp,
    id           varchar(36)  not null
        primary key,
    updated_at   timestamp    not null
);

comment on column consumption_records.user_id is '用户ID';

comment on column consumption_records.request_id is '关联的生成请求ID';

comment on column consumption_records.model_name is '使用的模型名称';

comment on column consumption_records.provider is 'Provider名称';

comment on column consumption_records.cost_type is '计费类型: free, subscription, points, balance';

comment on column consumption_records.points_used is '消耗积分';

comment on column consumption_records.amount is '消耗金额(分)';

comment on column consumption_records.prompt is '提示词';

comment on column consumption_records.image_count is '生成图片数量';

comment on column consumption_records.image_urls is '生成的图片URL列表';

comment on column consumption_records.status is '状态: success, failed';

comment on column consumption_records.error_reason is '失败原因';

comment on column consumption_records.created_at is '创建时间';

alter table consumption_records
    owner to postgres;

create index ix_consumption_records_user_id
    on consumption_records (user_id);

