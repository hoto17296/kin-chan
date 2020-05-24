CREATE TABLE users (
    id text PRIMARY KEY,
    t_begin text,
    t_end text,
    active boolean NOT NULL DEFAULT false
);