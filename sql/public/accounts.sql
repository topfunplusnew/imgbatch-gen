create table accounts
(
    user_id                  varchar(100) not null
        unique
        references users,
    balance                  integer,
    points                   integer,
    subscription_plan        varchar(50),
    subscription_expires_at  timestamp,
    total_generated          integer,
    total_spent              integer,
    total_points_earned      integer,
    free_quota_used          integer,
    subscription_quota_used  integer,
    gift_points              integer,
    gift_points_expiry       timestamp,
    gift_points_date         date,
    last_checkin_date        date,
    consecutive_checkin_days integer,
    invite_code              varchar(20)
        unique,
    inviter_id               varchar(100)
        references users,
    total_invite_count       integer,
    id                       varchar(36)  not null
        primary key,
    created_at               timestamp    not null,
    updated_at               timestamp    not null
);

comment on column accounts.user_id is '用户ID';

comment on column accounts.balance is '余额(分)';

comment on column accounts.points is '积分';

comment on column accounts.subscription_plan is '订阅套餐ID';

comment on column accounts.subscription_expires_at is '订阅到期时间';

comment on column accounts.total_generated is '总生成次数';

comment on column accounts.total_spent is '总消费(分)';

comment on column accounts.total_points_earned is '总获得积分';

comment on column accounts.free_quota_used is '已使用免费额度';

comment on column accounts.subscription_quota_used is '已使用订阅额度';

comment on column accounts.gift_points is '赠送积分（每日清零）';

comment on column accounts.gift_points_expiry is '赠送积分过期时间';

comment on column accounts.last_checkin_date is '最后签到日期';

comment on column accounts.consecutive_checkin_days is '连续签到天数';

comment on column accounts.invite_code is '我的邀请码';

comment on column accounts.inviter_id is '邀请人ID';

comment on column accounts.total_invite_count is '累计邀请人数';

alter table accounts
    owner to postgres;

