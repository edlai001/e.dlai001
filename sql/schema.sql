-- Run as studybuddy user in Oracle XE

CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE users (
    id            NUMBER DEFAULT users_seq.NEXTVAL PRIMARY KEY,
    email         VARCHAR2(255) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    role          VARCHAR2(20) DEFAULT 'student' NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
    user_id      NUMBER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR2(100),
    major        VARCHAR2(100),
    bio          VARCHAR2(1000),
    language     VARCHAR2(50) DEFAULT 'English'
);

CREATE SEQUENCE subjects_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE subjects (
    id   NUMBER DEFAULT subjects_seq.NEXTVAL PRIMARY KEY,
    name VARCHAR2(100) UNIQUE NOT NULL
);

CREATE SEQUENCE user_subjects_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE user_subjects (
    id         NUMBER DEFAULT user_subjects_seq.NEXTVAL PRIMARY KEY,
    user_id    NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id NUMBER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    skill_level VARCHAR2(20) DEFAULT 'beginner',
    study_goal  VARCHAR2(50) DEFAULT 'general',
    CONSTRAINT uq_user_subject UNIQUE (user_id, subject_id)
);

CREATE SEQUENCE availability_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE availability_slots (
    id          NUMBER DEFAULT availability_seq.NEXTVAL PRIMARY KEY,
    user_id     NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day_of_week NUMBER(1) NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time  VARCHAR2(5) NOT NULL,
    end_time    VARCHAR2(5) NOT NULL
);

CREATE SEQUENCE match_req_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE match_requests (
    id           NUMBER DEFAULT match_req_seq.NEXTVAL PRIMARY KEY,
    from_user_id NUMBER NOT NULL REFERENCES users(id),
    to_user_id   NUMBER NOT NULL REFERENCES users(id),
    status       VARCHAR2(20) DEFAULT 'pending',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_match_pair UNIQUE (from_user_id, to_user_id)
);

CREATE SEQUENCE groups_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE groups (
    id          NUMBER DEFAULT groups_seq.NEXTVAL PRIMARY KEY,
    name        VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    created_by  NUMBER NOT NULL REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE group_members (
    group_id    NUMBER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id     NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_role VARCHAR2(20) DEFAULT 'member',
    joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id)
);

CREATE SEQUENCE sessions_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE study_sessions (
    id               NUMBER DEFAULT sessions_seq.NEXTVAL PRIMARY KEY,
    group_id         NUMBER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    start_datetime   TIMESTAMP NOT NULL,
    end_datetime     TIMESTAMP NOT NULL,
    location_or_link VARCHAR2(300)
);

CREATE SEQUENCE messages_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE messages (
    id        NUMBER DEFAULT messages_seq.NEXTVAL PRIMARY KEY,
    group_id  NUMBER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    sender_id NUMBER NOT NULL REFERENCES users(id),
    body      VARCHAR2(2000) NOT NULL,
    sent_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE ratings_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE ratings (
    id           NUMBER DEFAULT ratings_seq.NEXTVAL PRIMARY KEY,
    from_user_id NUMBER NOT NULL REFERENCES users(id),
    to_user_id   NUMBER NOT NULL REFERENCES users(id),
    session_id   NUMBER NOT NULL REFERENCES study_sessions(id),
    stars        NUMBER(1) CHECK (stars BETWEEN 1 AND 5),
    rating_comment VARCHAR2(500)
);

-- Seed some subjects
INSERT INTO subjects (name) VALUES ('Mathematics');
INSERT INTO subjects (name) VALUES ('Algorithms');
INSERT INTO subjects (name) VALUES ('Databases');
INSERT INTO subjects (name) VALUES ('Data Structures');
INSERT INTO subjects (name) VALUES ('Operating Systems');
INSERT INTO subjects (name) VALUES ('Computer Networks');
INSERT INTO subjects (name) VALUES ('Python Programming');
INSERT INTO subjects (name) VALUES ('Java Programming');
INSERT INTO subjects (name) VALUES ('Web Development');
INSERT INTO subjects (name) VALUES ('Machine Learning');
INSERT INTO subjects (name) VALUES ('Linear Algebra');
INSERT INTO subjects (name) VALUES ('Statistics');
COMMIT;
