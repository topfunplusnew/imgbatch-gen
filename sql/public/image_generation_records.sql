create table image_generation_records
(
    user_request_id   varchar(36) not null
        references user_requests,
    provider          varchar(100),
    model             varchar(100),
    prompt            text,
    negative_prompt   text,
    width             integer,
    height            integer,
    n                 integer,
    style             varchar(50),
    quality           varchar(50),
    extra_params      json,
    status            varchar(50),
    image_urls        json,
    image_paths       json,
    processing_time   double precision,
    start_time        timestamp,
    end_time          timestamp,
    prompt_tokens     integer,
    completion_tokens integer,
    total_tokens      integer,
    call_mode         varchar(50),
    id                varchar(36) not null
        primary key,
    created_at        timestamp   not null,
    updated_at        timestamp   not null
);

comment on column image_generation_records.provider is 'Provider名称';

comment on column image_generation_records.model is '模型名称';

comment on column image_generation_records.prompt is '提示词';

comment on column image_generation_records.negative_prompt is '负面提示词';

comment on column image_generation_records.width is '图片宽度';

comment on column image_generation_records.height is '图片高度';

comment on column image_generation_records.n is '生成数量';

comment on column image_generation_records.style is '风格';

comment on column image_generation_records.quality is '质量';

comment on column image_generation_records.extra_params is '额外参数';

comment on column image_generation_records.status is '生成状态';

comment on column image_generation_records.image_urls is '生成的图片URL列表';

comment on column image_generation_records.image_paths is '本地图片路径列表';

comment on column image_generation_records.processing_time is '处理耗时（秒）';

comment on column image_generation_records.start_time is '开始时间';

comment on column image_generation_records.end_time is '结束时间';

comment on column image_generation_records.prompt_tokens is '提示词Token数';

comment on column image_generation_records.completion_tokens is '完成Token数';

comment on column image_generation_records.total_tokens is '总Token数';

comment on column image_generation_records.call_mode is '调用模式: serial, parallel, batch';

alter table image_generation_records
    owner to postgres;

