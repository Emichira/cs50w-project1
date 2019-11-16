/*
To reset Serial id to 1:
ALTER SEQUENCE users_id_seq RESTART;
*/

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL
);