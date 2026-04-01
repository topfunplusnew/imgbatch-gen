create table cleanup_history
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

alter table cleanup_history
    owner to postgres;

create index idx_cleanup_history_started_at
    on cleanup_history (started_at);

create index idx_cleanup_history_status
    on cleanup_history (status);

create index idx_cleanup_history_triggered_by
    on cleanup_history (triggered_by);

