create table user_requests
(
    user_id       varchar(100),
    user_ip       varchar(50),
    user_agent    varchar(500),
    request_type  varchar(50),
    request_data  json,
    status        varchar(50),
    error_message text,
    id            varchar(36) not null
        primary key,
    created_at    timestamp   not null,
    updated_at    timestamp   not null
);

comment on column user_requests.user_id is '用户ID';

comment on column user_requests.user_ip is '用户IP';

comment on column user_requests.user_agent is '用户代理';

comment on column user_requests.request_type is '请求类型: image_generation, chat, etc';

comment on column user_requests.request_data is '请求参数';

comment on column user_requests.status is '状态: pending, processing, completed, failed';

comment on column user_requests.error_message is '错误信息';

alter table user_requests
    owner to postgres;

create index ix_user_requests_user_id
    on user_requests (user_id);

create index ix_user_requests_request_type
    on user_requests (request_type);

