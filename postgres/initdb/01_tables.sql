CREATE TABLE IF NOT EXISTS metadata (
    id_metadata SERIAL PRIMARY KEY,
    dataset_name VARCHAR(255),
    guitarist_id INTEGER,
    title VARCHAR(255) NOT NULL UNIQUE,
    style VARCHAR(255),
    tempo INTEGER,
    scale VARCHAR(15),
    mode VARCHAR(63),
    playing_version VARCHAR(255),
    duration FLOAT
);