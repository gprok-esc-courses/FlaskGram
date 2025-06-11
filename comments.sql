DROP TABLE IF EXISTS comments;

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    users_id INTEGER NOT NULL, 
    posts_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (users_id) REFERENCES users (id), 
    FOREIGN KEY (posts_id) REFERENCES posts (id)
);
