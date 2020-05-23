CREATE TABLE users (
    id text PRIMARY KEY,
    email text NOT NULL,
    t_begin text,
    t_end text,
    active boolean NOT NULL DEFAULT false
);