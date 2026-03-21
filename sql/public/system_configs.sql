create table system_configs
(
    config_key   varchar(100) not null,
    config_value text,
    config_type  varchar(50),
    category     varchar(50),
    description  text,
    is_encrypted boolean,
    is_public    boolean,
    updated_at   timestamp,
    updated_by   varchar(100),
    id           varchar(36)  not null
        primary key,
    created_at   timestamp    not null
);

comment on column system_configs.config_key is '配置键';

comment on column system_configs.config_value is '配置值（JSON字符串）';

comment on column system_configs.config_type is '配置类型: string, number, boolean, json';

comment on column system_configs.category is '配置分类: api, storage, general, etc';

comment on column system_configs.description is '配置说明';

comment on column system_configs.is_encrypted is '是否加密存储';

comment on column system_configs.is_public is '是否公开（前端可读取）';

comment on column system_configs.updated_at is '更新时间';

comment on column system_configs.updated_by is '更新者用户ID';

alter table system_configs
    owner to postgres;

create unique index ix_system_configs_config_key
    on system_configs (config_key);

