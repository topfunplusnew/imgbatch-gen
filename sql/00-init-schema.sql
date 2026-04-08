-- 幂等的数据库初始化脚本
-- 可以安全地多次执行而不会报错

-- ==================== user_requests ====================

create table if not exists user_requests
(
    user_id       varchar(100),
    user_ip       varchar(50),
    user_agent    varchar(500),
    request_type  varchar(50),
    request_data  json,
    status        varchar(50),
    error_message text,
    id            varchar(36) not null
        primary key,
    created_at    timestamp   not null,
    updated_at    timestamp   not null
);

comment on column user_requests.user_id is '用户ID';

comment on column user_requests.user_ip is '用户IP';

comment on column user_requests.user_agent is '用户代理';

comment on column user_requests.request_type is '请求类型: image_generation, chat, etc';

comment on column user_requests.request_data is '请求参数';

comment on column user_requests.status is '状态: pending, processing, completed, failed';

comment on column user_requests.error_message is '错误信息';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'user_requests' and tableowner = 'postgres'
    ) then
        alter table user_requests owner to postgres;
    end if;
end $$;

create index if not exists ix_user_requests_user_id
    on user_requests (user_id);

create index if not exists ix_user_requests_request_type
    on user_requests (request_type);

-- ==================== conversation_sessions ====================

create table if not exists conversation_sessions
(
    session_id    varchar(100) not null,
    client_id     varchar(100),
    title         varchar(200),
    model         varchar(100),
    provider      varchar(100),
    status        varchar(20),
    message_count integer,
    image_count   integer,
    file_count    integer,
    created_at    timestamp,
    updated_at    timestamp,
    id            varchar(36)  not null
        primary key
);

comment on column conversation_sessions.session_id is '会话ID';

comment on column conversation_sessions.client_id is '客户端Cookie ID，用于区分不同客户端';

comment on column conversation_sessions.title is '对话标题';

comment on column conversation_sessions.model is '使用的模型';

comment on column conversation_sessions.provider is 'Provider名称';

comment on column conversation_sessions.status is '状态: active, completed, deleted';

comment on column conversation_sessions.message_count is '消息数量';

comment on column conversation_sessions.image_count is '图片数量';

comment on column conversation_sessions.file_count is '文件数量';

comment on column conversation_sessions.created_at is '创建时间';

comment on column conversation_sessions.updated_at is '更新时间';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'conversation_sessions' and tableowner = 'postgres'
    ) then
        alter table conversation_sessions owner to postgres;
    end if;
end $$;

create unique index if not exists ix_conversation_sessions_session_id
    on conversation_sessions (session_id);

create index if not exists ix_conversation_sessions_client_id
    on conversation_sessions (client_id);

-- ==================== stored_credentials ====================

create table if not exists stored_credentials
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'stored_credentials' and tableowner = 'postgres'
    ) then
        alter table stored_credentials owner to postgres;
    end if;
end $$;

create index if not exists ix_stored_credentials_user_id
    on stored_credentials (user_id);

create index if not exists ix_stored_credentials_provider
    on stored_credentials (provider);

create index if not exists ix_stored_credentials_status
    on stored_credentials (status);

create index if not exists ix_stored_credentials_session_id
    on stored_credentials (session_id);

-- ==================== uploaded_files ====================

create table if not exists uploaded_files
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'uploaded_files' and tableowner = 'postgres'
    ) then
        alter table uploaded_files owner to postgres;
    end if;
end $$;

create index if not exists ix_uploaded_files_message_id
    on uploaded_files (message_id);

create index if not exists ix_uploaded_files_conversation_id
    on uploaded_files (conversation_id);

-- ==================== users ====================

create table if not exists users
(
    username              varchar(50)  not null,
    email                 varchar(255)
        unique,
    phone                 varchar(20)
        unique,
    password_hash         varchar(255) not null,
    status                varchar(20),
    role                  varchar(20),
    last_login_at         timestamp,
    last_login_ip         varchar(50),
    id                    varchar(36)  not null
        primary key,
    created_at            timestamp    not null,
    updated_at            timestamp    not null,
    force_password_change boolean default false
);

comment on column users.username is '用户名';

comment on column users.phone is '手机号(可选)';

comment on column users.password_hash is '密码哈希';

comment on column users.status is '状态: active, suspended, deleted';

comment on column users.role is '角色: user, admin';

comment on column users.last_login_at is '最后登录时间';

comment on column users.last_login_ip is '最后登录IP';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'users' and tableowner = 'postgres'
    ) then
        alter table users owner to postgres;
    end if;
end $$;

create index if not exists ix_users_username
    on users (username);

-- 迁移: 添加 email 列（如果不存在）
do $$
begin
    if not exists (
        select 1 from information_schema.columns
        where table_name = 'users' and column_name = 'email'
    ) then
        alter table users add column email varchar(255) unique;
        comment on column users.email is '邮箱(可选)';
    end if;
end $$;

create index if not exists ix_users_email
    on users (email);

-- ==================== billing_plans ====================

create table if not exists billing_plans
(
    plan_id          varchar(50)  not null
        unique,
    name             varchar(100) not null,
    description      text,
    price            integer      not null,
    original_price   integer,
    duration_days    integer,
    points_included  integer,
    generation_quota integer,
    daily_quota      integer,
    features         json,
    is_active        boolean,
    sort_order       integer,
    badge_text       varchar(50),
    id               varchar(36)  not null
        primary key,
    created_at       timestamp    not null,
    updated_at       timestamp    not null
);

comment on column billing_plans.plan_id is '套餐ID';

comment on column billing_plans.name is '套餐名称';

comment on column billing_plans.description is '套餐描述';

comment on column billing_plans.price is '价格(分)';

comment on column billing_plans.original_price is '原价(分)，用于显示折扣';

comment on column billing_plans.duration_days is '有效天数(NULL表示永久)';

comment on column billing_plans.points_included is '包含积分';

comment on column billing_plans.generation_quota is '生成次数额度(0表示无限制)';

comment on column billing_plans.daily_quota is '每日生成次数额度(0表示无限制)';

comment on column billing_plans.features is '特权列表(JSON数组)';

comment on column billing_plans.is_active is '是否启用';

comment on column billing_plans.sort_order is '排序序号';

comment on column billing_plans.badge_text is '徽章文字(如''热门'')';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'billing_plans' and tableowner = 'postgres'
    ) then
        alter table billing_plans owner to postgres;
    end if;
end $$;

-- ==================== image_generation_records ====================

create table if not exists image_generation_records
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'image_generation_records' and tableowner = 'postgres'
    ) then
        alter table image_generation_records owner to postgres;
    end if;
end $$;

-- ==================== chat_messages ====================

create table if not exists chat_messages
(
    user_request_id   varchar(36)
        references user_requests (id),
    session_id        varchar(100) not null
        references conversation_sessions (session_id),
    role              varchar(50),
    content           text,
    model             varchar(100),
    provider          varchar(100),
    prompt_tokens     integer,
    completion_tokens integer,
    total_tokens      integer,
    temperature       double precision,
    max_tokens        integer,
    top_p             double precision,
    images            text,
    files             text,
    id                varchar(36) not null
        primary key,
    created_at        timestamp    not null,
    updated_at        timestamp    not null
);

comment on column chat_messages.user_request_id is '关联的用户请求ID';

comment on column chat_messages.session_id is '会话ID';

comment on column chat_messages.role is '角色: system, user, assistant';

comment on column chat_messages.content is '对话内容';

comment on column chat_messages.model is '使用的模型';

comment on column chat_messages.provider is 'Provider名称';

comment on column chat_messages.prompt_tokens is '提示词Token数';

comment on column chat_messages.completion_tokens is '完成Token数';

comment on column chat_messages.total_tokens is '总Token数';

comment on column chat_messages.temperature is '温度参数';

comment on column chat_messages.max_tokens is '最大Token数';

comment on column chat_messages.top_p is 'top_p参数';

comment on column chat_messages.images is '图片URL列表(JSON)';

comment on column chat_messages.files is '文件信息列表(JSON)';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'chat_messages' and tableowner = 'postgres'
    ) then
        alter table chat_messages owner to postgres;
    end if;
end $$;

-- ==================== system_logs ====================

create table if not exists system_logs
(
    level             varchar(20),
    module            varchar(100),
    function          varchar(100),
    message           text,
    details           json,
    user_id           varchar(100),
    request_id        varchar(36)
        references user_requests,
    exception_type    varchar(100),
    exception_message text,
    traceback         text,
    id                varchar(36) not null
        primary key,
    created_at        timestamp   not null,
    updated_at        timestamp   not null
);

comment on column system_logs.level is '日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL';

comment on column system_logs.module is '模块名称';

comment on column system_logs.function is '函数名称';

comment on column system_logs.message is '日志消息';

comment on column system_logs.details is '详细信息';

comment on column system_logs.user_id is '关联的用户ID';

comment on column system_logs.request_id is '关联的请求ID';

comment on column system_logs.exception_type is '异常类型';

comment on column system_logs.exception_message is '异常消息';

comment on column system_logs.traceback is '异常堆栈';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'system_logs' and tableowner = 'postgres'
    ) then
        alter table system_logs owner to postgres;
    end if;
end $$;

create index if not exists ix_system_logs_level
    on system_logs (level);

create index if not exists ix_system_logs_user_id
    on system_logs (user_id);

create index if not exists ix_system_logs_module
    on system_logs (module);

-- ==================== user_auth ====================

create table if not exists user_auth
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'user_auth' and tableowner = 'postgres'
    ) then
        alter table user_auth owner to postgres;
    end if;
end $$;

create index if not exists ix_user_auth_type_identifier
    on user_auth (auth_type, auth_identifier);

-- ==================== login_logs ====================

create table if not exists login_logs
(
    user_id        varchar(100)
        references users,
    login_type     varchar(20),
    login_ip       varchar(50),
    login_location varchar(100),
    user_agent     varchar(500),
    status         varchar(20),
    fail_reason    varchar(255),
    logout_at      timestamp,
    id             varchar(36) not null
        primary key,
    created_at     timestamp   not null,
    updated_at     timestamp   not null
);

comment on column login_logs.user_id is '用户ID(游客为NULL)';

comment on column login_logs.login_type is '登录类型: email, phone, oauth';

comment on column login_logs.login_ip is '登录IP';

comment on column login_logs.login_location is '登录地点(可选)';

comment on column login_logs.user_agent is '用户代理';

comment on column login_logs.status is '状态: success, failed';

comment on column login_logs.fail_reason is '失败原因';

comment on column login_logs.logout_at is '登出时间';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'login_logs' and tableowner = 'postgres'
    ) then
        alter table login_logs owner to postgres;
    end if;
end $$;

-- ==================== accounts ====================

create table if not exists accounts
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'accounts' and tableowner = 'postgres'
    ) then
        alter table accounts owner to postgres;
    end if;
end $$;

-- ==================== transactions ====================

create table if not exists transactions
(
    user_id            varchar(100) not null
        references users,
    transaction_type   varchar(50)  not null,
    amount             integer,
    points_change      integer,
    balance_after      integer,
    points_after       integer,
    related_order_id   varchar(100),
    related_request_id varchar(100),
    description        varchar(255),
    status             varchar(20),
    extra_data         json,
    id                 varchar(36)  not null
        primary key,
    created_at         timestamp    not null,
    updated_at         timestamp    not null
);

comment on column transactions.user_id is '用户ID';

comment on column transactions.transaction_type is '交易类型: recharge, consumption, refund, subscription, gift, system_adjust';

comment on column transactions.amount is '金额变化(分，正为增加，负为减少)';

comment on column transactions.points_change is '积分变化(正为增加，负为减少)';

comment on column transactions.balance_after is '交易后余额';

comment on column transactions.points_after is '交易后积分';

comment on column transactions.related_order_id is '关联订单ID';

comment on column transactions.related_request_id is '关联请求ID';

comment on column transactions.description is '交易描述';

comment on column transactions.status is '状态: pending, success, failed, cancelled';

comment on column transactions.extra_data is '额外信息(JSON)';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'transactions' and tableowner = 'postgres'
    ) then
        alter table transactions owner to postgres;
    end if;
end $$;

create index if not exists ix_transactions_user_id
    on transactions (user_id);

-- ==================== consumption_records ====================

create table if not exists consumption_records
(
    user_id      varchar(100) not null
        references users,
    request_id   varchar(100),
    model_name   varchar(100),
    provider     varchar(50),
    cost_type    varchar(20)  not null,
    points_used  integer,
    amount       integer,
    prompt       text,
    image_count  integer,
    image_urls   json,
    status       varchar(20),
    error_reason text,
    created_at   timestamp,
    id           varchar(36)  not null
        primary key,
    updated_at   timestamp    not null
);

comment on column consumption_records.user_id is '用户ID';

comment on column consumption_records.request_id is '关联的生成请求ID';

comment on column consumption_records.model_name is '使用的模型名称';

comment on column consumption_records.provider is 'Provider名称';

comment on column consumption_records.cost_type is '计费类型: free, subscription, points, balance';

comment on column consumption_records.points_used is '消耗积分';

comment on column consumption_records.amount is '消耗金额(分)';

comment on column consumption_records.prompt is '提示词';

comment on column consumption_records.image_count is '生成图片数量';

comment on column consumption_records.image_urls is '生成的图片URL列表';

comment on column consumption_records.status is '状态: success, failed';

comment on column consumption_records.error_reason is '失败原因';

comment on column consumption_records.created_at is '创建时间';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'consumption_records' and tableowner = 'postgres'
    ) then
        alter table consumption_records owner to postgres;
    end if;
end $$;

create index if not exists ix_consumption_records_user_id
    on consumption_records (user_id);

-- ==================== payment_orders ====================

create table if not exists payment_orders
(
    order_id        varchar(100) not null
        unique,
    user_id         varchar(100) not null
        references users,
    order_type      varchar(20)  not null,
    amount          integer      not null,
    plan_id         varchar(50),
    payment_method  varchar(20)  not null,
    payment_channel varchar(50),
    status          varchar(20),
    transaction_id  varchar(100),
    prepay_id       varchar(100),
    qr_code_url     text,
    pay_url         text,
    notify_time     timestamp,
    notify_data     json,
    expire_time     timestamp,
    paid_at         timestamp,
    subject         varchar(255),
    body            text,
    attach          json,
    client_ip       varchar(50),
    user_agent      varchar(500),
    id              varchar(36)  not null
        primary key,
    created_at      timestamp    not null,
    updated_at      timestamp    not null
);

comment on column payment_orders.order_id is '订单号';

comment on column payment_orders.user_id is '用户ID';

comment on column payment_orders.order_type is '订单类型: recharge, subscription';

comment on column payment_orders.amount is '订单金额(分)';

comment on column payment_orders.plan_id is '关联的套餐ID';

comment on column payment_orders.payment_method is '支付方式: wechat, alipay';

comment on column payment_orders.payment_channel is '支付渠道: native, h5, jsapi';

comment on column payment_orders.status is '状态: pending, paid, failed, cancelled, refunded, timeout';

comment on column payment_orders.transaction_id is '第三方交易ID';

comment on column payment_orders.prepay_id is '预支付ID';

comment on column payment_orders.qr_code_url is '支付二维码URL';

comment on column payment_orders.pay_url is '支付跳转URL(H5支付用)';

comment on column payment_orders.notify_time is '支付回调时间';

comment on column payment_orders.notify_data is '回调原始数据';

comment on column payment_orders.expire_time is '订单过期时间';

comment on column payment_orders.paid_at is '支付完成时间';

comment on column payment_orders.subject is '订单标题';

comment on column payment_orders.body is '订单描述';

comment on column payment_orders.attach is '附加数据(JSON)';

comment on column payment_orders.client_ip is '客户端IP';

comment on column payment_orders.user_agent is '用户代理';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'payment_orders' and tableowner = 'postgres'
    ) then
        alter table payment_orders owner to postgres;
    end if;
end $$;

create index if not exists ix_payment_orders_user_id
    on payment_orders (user_id);

-- ==================== payment_refunds ====================

create table if not exists payment_refunds
(
    payment_order_id      varchar(100) not null
        references payment_orders (order_id),
    refund_id             varchar(100) not null
        unique,
    refund_amount         integer      not null,
    refund_reason         varchar(255),
    status                varchar(20),
    refund_transaction_id varchar(100),
    refund_time           timestamp,
    created_at            timestamp,
    id                    varchar(36)  not null
        primary key,
    updated_at            timestamp    not null
);

comment on column payment_refunds.payment_order_id is '原支付订单ID';

comment on column payment_refunds.refund_id is '退款单号';

comment on column payment_refunds.refund_amount is '退款金额(分)';

comment on column payment_refunds.refund_reason is '退款原因';

comment on column payment_refunds.status is '状态: pending, success, failed, cancelled';

comment on column payment_refunds.refund_transaction_id is '第三方退款交易ID';

comment on column payment_refunds.refund_time is '退款完成时间';

comment on column payment_refunds.created_at is '创建时间';

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'payment_refunds' and tableowner = 'postgres'
    ) then
        alter table payment_refunds owner to postgres;
    end if;
end $$;

-- ==================== download_records ====================

create table if not exists download_records
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'download_records' and tableowner = 'postgres'
    ) then
        alter table download_records owner to postgres;
    end if;
end $$;

create index if not exists ix_download_records_user_id
    on download_records (user_id);

-- ==================== system_configs ====================

create table if not exists system_configs
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'system_configs' and tableowner = 'postgres'
    ) then
        alter table system_configs owner to postgres;
    end if;
end $$;

create index if not exists ix_system_configs_config_key
    on system_configs (config_key);

-- ==================== withdrawals ====================

create table if not exists withdrawals
(
    id                 serial
        primary key,
    withdrawal_id      varchar(100) not null
        unique,
    user_id            varchar(100) not null
        references users,
    amount             integer      not null,
    withdrawal_method  varchar(20)  not null,
    withdrawal_account varchar(200),
    withdrawal_name    varchar(100),
    status             varchar(20) default 'pending'::character varying,
    admin_id           varchar(100),
    review_note        varchar(500),
    reviewed_at        timestamp,
    payment_proof      varchar(500),
    completed_at       timestamp,
    user_note          varchar(500),
    created_at         timestamp   default CURRENT_TIMESTAMP,
    updated_at         timestamp   default CURRENT_TIMESTAMP
);

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'withdrawals' and tableowner = 'postgres'
    ) then
        alter table withdrawals owner to postgres;
    end if;
end $$;

create index if not exists idx_withdrawals_user_id
    on withdrawals (user_id);

create index if not exists idx_withdrawals_status
    on withdrawals (status);

-- ==================== cases ====================

create table if not exists cases
(
    id              varchar(36)  not null
        primary key,
    created_at      timestamp default CURRENT_TIMESTAMP,
    updated_at      timestamp default CURRENT_TIMESTAMP,
    title           varchar(200) not null,
    description     text,
    category        varchar(50)  not null,
    tags            json,
    thumbnail_url   varchar(500),
    image_url       varchar(500),
    image_path      varchar(500),
    prompt          text         not null,
    negative_prompt text,
    parameters      json,
    provider        varchar(100),
    model           varchar(100),
    is_published    boolean   default true,
    sort_order      integer   default 0,
    view_count      integer   default 0,
    use_count       integer   default 0,
    created_by      varchar(100)
);

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'cases' and tableowner = 'postgres'
    ) then
        alter table cases owner to postgres;
    end if;
end $$;

create index if not exists idx_cases_category
    on cases (category);

create index if not exists idx_cases_is_published
    on cases (is_published);

create index if not exists idx_cases_sort_order
    on cases (sort_order);

create index if not exists idx_cases_created_at
    on cases (created_at);

-- ==================== announcements ====================

create table if not exists announcements
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'announcements' and tableowner = 'postgres'
    ) then
        alter table announcements owner to postgres;
    end if;
end $$;

create index if not exists ix_announcements_priority
    on announcements (priority);

create index if not exists ix_announcements_is_published
    on announcements (is_published);

create index if not exists ix_announcements_priority_pinned
    on announcements (priority, is_pinned);

create index if not exists ix_announcements_published_expires
    on announcements (is_published, expires_at);

create index if not exists ix_announcements_is_pinned
    on announcements (is_pinned);

create index if not exists ix_announcements_expires_at
    on announcements (expires_at);

-- ==================== user_notifications ====================

create table if not exists user_notifications
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

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'user_notifications' and tableowner = 'postgres'
    ) then
        alter table user_notifications owner to postgres;
    end if;
end $$;

create index if not exists ix_user_notifications_user_read
    on user_notifications (user_id, is_read);

create index if not exists ix_user_notifications_announcement_id
    on user_notifications (announcement_id);

create index if not exists ix_user_notifications_is_read
    on user_notifications (is_read);

create index if not exists ix_user_notifications_user_id
    on user_notifications (user_id);

create index if not exists ix_user_notifications_announcement_read
    on user_notifications (announcement_id, is_read);

-- ==================== cleanup_history ====================

create table if not exists cleanup_history
(
    id                          varchar(36) not null
        primary key,
    created_at                  timestamp   default CURRENT_TIMESTAMP,
    updated_at                  timestamp   default CURRENT_TIMESTAMP,
    retention_days              integer,
    cutoff_date                 timestamp,
    dry_run                     boolean     default false,
    total_image_records_deleted integer     default 0,
    total_chat_records_deleted  integer     default 0,
    total_user_requests_deleted integer     default 0,
    total_image_files_deleted   integer     default 0,
    total_storage_freed_bytes   bigint      default 0,
    error_count                 integer     default 0,
    errors                      json,
    failed_image_deletions      json,
    triggered_by                varchar(100),
    started_at                  timestamp,
    completed_at                timestamp,
    duration_seconds            double precision,
    status                      varchar(20) default 'running'::character varying
);

do $$
begin
    if not exists (
        select 1 from pg_tables where tablename = 'cleanup_history' and tableowner = 'postgres'
    ) then
        alter table cleanup_history owner to postgres;
    end if;
end $$;

create index if not exists idx_cleanup_history_started_at
    on cleanup_history (started_at);

create index if not exists idx_cleanup_history_status
    on cleanup_history (status);

create index if not exists idx_cleanup_history_triggered_by
    on cleanup_history (triggered_by);

-- ==================== 迁移: conversation_sessions 添加 user_id ====================
do $$
begin
    if not exists (
        select 1 from information_schema.columns
        where table_name = 'conversation_sessions' and column_name = 'user_id'
    ) then
        alter table conversation_sessions add column user_id varchar(100);
        create index ix_conversation_sessions_user_id on conversation_sessions (user_id);
        comment on column conversation_sessions.user_id is '登录用户ID';
    end if;
end $$;
