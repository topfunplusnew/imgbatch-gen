create table user_auth
(
    user_id            varchar(100) not null
        references users,
    auth_type          varchar(20)  not null,
    auth_identifier    varchar(255) not null,
    verified           boolean,
    verify_code        varchar(10),
    verify_code_expiry timestamp,
    oauth_provider     varchar(50),
    oauth_openid       varchar(255),
    oauth_unionid      varchar(255),
    id                 varchar(36)  not null
        primary key,
    created_at         timestamp    not null,
    updated_at         timestamp    not null
);

comment on column user_auth.user_id is '用户ID';

comment on column user_auth.auth_type is '认证类型: email, phone, oauth';

comment on column user_auth.auth_identifier is '认证标识(邮箱/手机号/openid)';

comment on column user_auth.verified is '是否已验证';

comment on column user_auth.verify_code is '验证码';

comment on column user_auth.verify_code_expiry is '验证码过期时间';

comment on column user_auth.oauth_provider is 'OAuth提供商: wechat, github';

comment on column user_auth.oauth_openid is 'OAuth OpenID';

comment on column user_auth.oauth_unionid is 'OAuth UnionID(微信)';

alter table user_auth
    owner to postgres;

create index ix_user_auth_type_identifier
    on user_auth (auth_type, auth_identifier);

