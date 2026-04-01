create table login_logs
(
    user_id        varchar(100)
        references users,
    login_type     varchar(20),
    login_ip       varchar(50),
    login_location varchar(100),
    user_agent     varchar(500),
    status         varchar(20),
    fail_reason    varchar(255),
    logout_at      timestamp,
    id             varchar(36) not null
        primary key,
    created_at     timestamp   not null,
    updated_at     timestamp   not null
);

comment on column login_logs.user_id is '用户ID(游客为NULL)';

comment on column login_logs.login_type is '登录类型: email, phone, oauth';

comment on column login_logs.login_ip is '登录IP';

comment on column login_logs.login_location is '登录地点(可选)';

comment on column login_logs.user_agent is '用户代理';

comment on column login_logs.status is '状态: success, failed';

comment on column login_logs.fail_reason is '失败原因';

comment on column login_logs.logout_at is '登出时间';

alter table login_logs
    owner to postgres;

