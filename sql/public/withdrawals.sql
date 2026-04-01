create table withdrawals
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

alter table withdrawals
    owner to postgres;

create index idx_withdrawals_user_id
    on withdrawals (user_id);

create index idx_withdrawals_status
    on withdrawals (status);

