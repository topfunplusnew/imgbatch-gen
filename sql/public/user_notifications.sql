create table user_notifications
(
    announcement_id varchar(36)  not null
        references announcements,
    user_id         varchar(100) not null,
    is_read         boolean,
    read_at         timestamp,
    is_clicked      boolean,
    clicked_at      timestamp,
    is_pushed       boolean,
    pushed_at       timestamp,
    push_method     varchar(20),
    id              varchar(36)  not null
        primary key,
    created_at      timestamp    not null,
    updated_at      timestamp    not null,
    constraint unique_user_announcement
        unique (announcement_id, user_id)
);

comment on column user_notifications.user_id is '用户ID';

comment on column user_notifications.is_read is '是否已读';

comment on column user_notifications.read_at is '读取时间';

comment on column user_notifications.is_clicked is '是否点击查看详情';

comment on column user_notifications.clicked_at is '点击时间';

comment on column user_notifications.is_pushed is '是否已推送';

comment on column user_notifications.pushed_at is '推送时间';

comment on column user_notifications.push_method is '推送方式: sse, email, sms';

alter table user_notifications
    owner to postgres;

create index ix_user_notifications_user_read
    on user_notifications (user_id, is_read);

create index ix_user_notifications_announcement_id
    on user_notifications (announcement_id);

create index ix_user_notifications_is_read
    on user_notifications (is_read);

create index ix_user_notifications_user_id
    on user_notifications (user_id);

create index ix_user_notifications_announcement_read
    on user_notifications (announcement_id, is_read);

