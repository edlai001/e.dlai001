-- Run once as the studybuddy user (adds direct messaging)
CREATE SEQUENCE direct_msg_seq START WITH 1 INCREMENT BY 1;
CREATE TABLE direct_messages (
    id           NUMBER DEFAULT direct_msg_seq.NEXTVAL PRIMARY KEY,
    from_user_id NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    to_user_id   NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body         VARCHAR2(2000) NOT NULL,
    sent_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_direct_msg_pair ON direct_messages (from_user_id, to_user_id);
