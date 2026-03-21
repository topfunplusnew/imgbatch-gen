create table announcements
(
    title             varchar(200) not null,
    content           text         not null,
    priority          varchar(20),
    announcement_type varchar(50),
    is_pinned         boolean,
    is_published      boolean,
    published_at      timestamp,
    expires_at        timestamp,
    cover_image_url   varchar(500),
    cover_image_path  varchar(500),
    target_audience   varchar(50),
    view_count        integer,
    click_count       integer,
    created_by        varchar(100),
    updated_by        varchar(100),
    id                varchar(36)  not null
        primary key,
    created_at        timestamp    not null,
    updated_at        timestamp    not null
);

comment on column announcements.title is '公告标题';

comment on column announcements.content is '公告内容（富文本HTML）';

comment on column announcements.priority is '优先级: low, normal, high, urgent';

comment on column announcements.announcement_type is '公告类型: system, maintenance, feature, promotion';

comment on column announcements.is_pinned is '是否置顶';

comment on column announcements.is_published is '是否发布';

comment on column announcements.published_at is '发布时间';

comment on column announcements.expires_at is '过期时间（可选）';

comment on column announcements.cover_image_url is '封面图片URL';

comment on column announcements.cover_image_path is '封面图片存储路径';

comment on column announcements.target_audience is '目标受众: all, users_only, admins_only';

comment on column announcements.view_count is '浏览次数';

comment on column announcements.click_count is '点击次数';

comment on column announcements.created_by is '创建者ID（管理员）';

comment on column announcements.updated_by is '更新者ID（管理员）';

alter table announcements
    owner to postgres;

create index ix_announcements_priority
    on announcements (priority);

create index ix_announcements_is_published
    on announcements (is_published);

create index ix_announcements_priority_pinned
    on announcements (priority, is_pinned);

create index ix_announcements_published_expires
    on announcements (is_published, expires_at);

create index ix_announcements_is_pinned
    on announcements (is_pinned);

create index ix_announcements_expires_at
    on announcements (expires_at);

