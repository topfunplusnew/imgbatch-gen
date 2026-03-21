create table chat_messages
(
    user_request_id   varchar(36)
        references user_requests,
    session_id        varchar(100) not null
        references conversation_sessions (),
    role              varchar(50),
    content           text,
    model             varchar(100),
    provider          varchar(100),
    prompt_tokens     integer,
    completion_tokens integer,
    total_tokens      integer,
    temperature       double precision,
    max_tokens        integer,
    top_p             double precision,
    images            text,
    files             text,
    id                varchar(36)  not null
        primary key,
    created_at        timestamp    not null,
    updated_at        timestamp    not null
);

comment on column chat_messages.user_request_id is '关联的用户请求ID';

comment on column chat_messages.session_id is '会话ID';

comment on column chat_messages.role is '角色: system, user, assistant';

comment on column chat_messages.content is '对话内容';

comment on column chat_messages.model is '使用的模型';

comment on column chat_messages.provider is 'Provider名称';

comment on column chat_messages.prompt_tokens is '提示词Token数';

comment on column chat_messages.completion_tokens is '完成Token数';

comment on column chat_messages.total_tokens is '总Token数';

comment on column chat_messages.temperature is '温度参数';

comment on column chat_messages.max_tokens is '最大Token数';

comment on column chat_messages.top_p is 'top_p参数';

comment on column chat_messages.images is '图片URL列表(JSON)';

comment on column chat_messages.files is '文件信息列表(JSON)';

alter table chat_messages
    owner to postgres;

