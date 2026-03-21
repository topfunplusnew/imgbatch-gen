create table system_logs
(
    level             varchar(20),
    module            varchar(100),
    function          varchar(100),
    message           text,
    details           json,
    user_id           varchar(100),
    request_id        varchar(36)
        references user_requests,
    exception_type    varchar(100),
    exception_message text,
    traceback         text,
    id                varchar(36) not null
        primary key,
    created_at        timestamp   not null,
    updated_at        timestamp   not null
);

comment on column system_logs.level is '日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL';

comment on column system_logs.module is '模块名称';

comment on column system_logs.function is '函数名称';

comment on column system_logs.message is '日志消息';

comment on column system_logs.details is '详细信息';

comment on column system_logs.user_id is '关联的用户ID';

comment on column system_logs.request_id is '关联的请求ID';

comment on column system_logs.exception_type is '异常类型';

comment on column system_logs.exception_message is '异常消息';

comment on column system_logs.traceback is '异常堆栈';

alter table system_logs
    owner to postgres;

create index ix_system_logs_level
    on system_logs (level);

create index ix_system_logs_user_id
    on system_logs (user_id);

create index ix_system_logs_module
    on system_logs (module);

