create table uploaded_files
(
    original_filename varchar(255),
    stored_filename   varchar(255)
        unique,
    file_path         varchar(500),
    file_url          varchar(500),
    file_size         integer,
    file_type         varchar(100),
    file_extension    varchar(20),
    category          varchar(50),
    conversation_id   varchar(100),
    message_id        integer,
    is_public         boolean,
    status            varchar(50),
    id                varchar(36) not null
        primary key,
    created_at        timestamp   not null,
    updated_at        timestamp   not null
);

comment on column uploaded_files.original_filename is '原始文件名';

comment on column uploaded_files.stored_filename is '存储的文件名';

comment on column uploaded_files.file_path is '文件存储路径';

comment on column uploaded_files.file_url is '文件访问URL';

comment on column uploaded_files.file_size is '文件大小（字节）';

comment on column uploaded_files.file_type is '文件MIME类型';

comment on column uploaded_files.file_extension is '文件扩展名';

comment on column uploaded_files.category is '文件分类: image, document, other';

comment on column uploaded_files.conversation_id is '关联的对话ID';

comment on column uploaded_files.message_id is '关联的消息ID';

comment on column uploaded_files.is_public is '是否公开访问';

comment on column uploaded_files.status is '文件状态: active, deleted, archived';

alter table uploaded_files
    owner to postgres;

create index ix_uploaded_files_message_id
    on uploaded_files (message_id);

create index ix_uploaded_files_conversation_id
    on uploaded_files (conversation_id);

