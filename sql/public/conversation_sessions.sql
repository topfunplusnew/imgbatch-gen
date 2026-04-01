create table conversation_sessions
(
    session_id    varchar(100) not null,
    client_id     varchar(100),
    title         varchar(200),
    model         varchar(100),
    provider      varchar(100),
    status        varchar(20),
    message_count integer,
    image_count   integer,
    file_count    integer,
    created_at    timestamp,
    updated_at    timestamp,
    id            varchar(36)  not null
        primary key
);

comment on column conversation_sessions.session_id is '会话ID';

comment on column conversation_sessions.client_id is '客户端Cookie ID，用于区分不同客户端';

comment on column conversation_sessions.title is '对话标题';

comment on column conversation_sessions.model is '使用的模型';

comment on column conversation_sessions.provider is 'Provider名称';

comment on column conversation_sessions.status is '状态: active, completed, deleted';

comment on column conversation_sessions.message_count is '消息数量';

comment on column conversation_sessions.image_count is '图片数量';

comment on column conversation_sessions.file_count is '文件数量';

comment on column conversation_sessions.created_at is '创建时间';

comment on column conversation_sessions.updated_at is '更新时间';

alter table conversation_sessions
    owner to postgres;

create unique index ix_conversation_sessions_session_id
    on conversation_sessions (session_id);

create index ix_conversation_sessions_client_id
    on conversation_sessions (client_id);

