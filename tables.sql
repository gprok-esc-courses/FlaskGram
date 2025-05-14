DROP TABLE IF EXISTS users;

DROP TABLE IF EXISTS posts;

DROP TABLE IF EXISTS likes;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    description TEXT, 
    created_at TIMESTAMP NOT NULL
); 

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    image TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL, 
    users_id INTEGER NOT NULL,
    FOREIGN KEY (users_id) REFERENCES users (id) 
);

CREATE TABLE likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    users_id INTEGER NOT NULL, 
    posts_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (users_id) REFERENCES users (id), 
    FOREIGN KEY (posts_id) REFERENCES posts (id), 
    UNIQUE (posts_id, users_id)
);