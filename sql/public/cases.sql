create table cases
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

alter table cases
    owner to postgres;

create index idx_cases_category
    on cases (category);

create index idx_cases_is_published
    on cases (is_published);

create index idx_cases_sort_order
    on cases (sort_order);

create index idx_cases_created_at
    on cases (created_at);

