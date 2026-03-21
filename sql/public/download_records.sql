create table download_records
(
    user_id               varchar(100) not null
        references users,
    image_url             text,
    file_name             varchar(255),
    file_size             integer,
    request_id            varchar(100),
    consumption_record_id varchar(100)
        references consumption_records,
    download_ip           varchar(50),
    user_agent            varchar(500),
    created_at            timestamp,
    id                    varchar(36)  not null
        primary key,
    updated_at            timestamp    not null
);

comment on column download_records.user_id is '用户ID';

comment on column download_records.image_url is '图片URL';

comment on column download_records.file_name is '下载文件名';

comment on column download_records.file_size is '文件大小(字节)';

comment on column download_records.request_id is '关联请求ID';

comment on column download_records.consumption_record_id is '关联消费记录ID';

comment on column download_records.download_ip is '下载IP';

comment on column download_records.user_agent is '用户代理';

comment on column download_records.created_at is '下载时间';

alter table download_records
    owner to postgres;

create index ix_download_records_user_id
    on download_records (user_id);

