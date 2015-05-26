-- SQL Schema

-- Table Definitions
CREATE TABLE reserve (
    id TEXT PRIMARY KEY,
    course_code TEXT,
    instructor TEXT,
    bookbag_id INTEGER
);
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT,
    expiry TIMESTAMP DEFAULT NOW() + '02:00:00'::interval
);

-- View Definitions
CREATE VIEW get_users
    AS SELECT * from users
    WHERE expiry > NOW();
