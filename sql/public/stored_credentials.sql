create table stored_credentials
(
    provider          varchar(50) not null,
    base_url          varchar(500),
    user_id           varchar(100),
    session_id        varchar(100),
    encrypted_api_key text        not null,
    key_hint          varchar(32),
    status            varchar(20),
    expires_at        timestamp,
    last_used_at      timestamp,
    id                varchar(36) not null
        primary key,
    created_at        timestamp   not null,
    updated_at        timestamp   not null
);

comment on column stored_credentials.base_url is '凭据对应的Base URL';

comment on column stored_credentials.user_id is '关联用户ID';

comment on column stored_credentials.session_id is '关联会话ID';

comment on column stored_credentials.encrypted_api_key is '加密后的API Key';

comment on column stored_credentials.key_hint is '脱敏后的Key提示';

comment on column stored_credentials.status is 'active/expired/revoked';

comment on column stored_credentials.expires_at is '过期时间';

comment on column stored_credentials.last_used_at is '最近使用时间';

alter table stored_credentials
    owner to postgres;

create index ix_stored_credentials_user_id
    on stored_credentials (user_id);

create index ix_stored_credentials_provider
    on stored_credentials (provider);

create index ix_stored_credentials_status
    on stored_credentials (status);

create index ix_stored_credentials_session_id
    on stored_credentials (session_id);

