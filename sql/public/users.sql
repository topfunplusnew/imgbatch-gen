create table users
(
    username      varchar(50)  not null,
    phone         varchar(20)
        unique,
    password_hash varchar(255) not null,
    status        varchar(20),
    role          varchar(20),
    last_login_at timestamp,
    last_login_ip varchar(50),
    id            varchar(36)  not null
        primary key,
    created_at    timestamp    not null,
    updated_at    timestamp    not null
);

comment on column users.username is '用户名';

comment on column users.phone is '手机号(可选)';

comment on column users.password_hash is '密码哈希';

comment on column users.status is '状态: active, suspended, deleted';

comment on column users.role is '角色: user, admin';

comment on column users.last_login_at is '最后登录时间';

comment on column users.last_login_ip is '最后登录IP';

alter table users
    owner to postgres;

create unique index ix_users_username
    on users (username);

