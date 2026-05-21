CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ===
-- RECORDINGS
-- ===

CREATE TABLE recordings (
    id_recording UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_recordings_dataset_title UNIQUE (dataset_name, title)
);

CREATE INDEX index_recordings_dataset_name
    ON recordings(dataset_name);

CREATE INDEX index_recordings_title
    ON recordings(title);


-- ===
-- GUTARSET METADATA
-- ===

CREATE TABLE guitarset_metadata (
    id_recording UUID PRIMARY KEY
        REFERENCES recordings(id_recording)
        ON DELETE CASCADE,

    duration DOUBLE PRECISION,
    guitarist_id INTEGER NOT NULL,
    style TEXT,
    tempo INTEGER,
    scale TEXT,
    mode TEXT,
    playing_version TEXT,
    pick_up_setting TEXT,

    CONSTRAINT duration_positive
        CHECK (duration IS NULL OR duration > 0),
    
    CONSTRAINT guitarset_tempo_positive
        CHECK (tempo IS NULL OR tempo > 0)
);

CREATE INDEX index_guitarset_guitarist_id
    ON guitarset_metadata(guitarist_id);

CREATE INDEX index_guitarset_style
    ON guitarset_metadata(style);

CREATE INDEX index_guitarset_scale
    ON guitarset_metadata(scale);

CREATE INDEX index_guitarset_mode
    ON guitarset_metadata(mode);


-- ===
-- IDMT-SMT-GUITAR METADATA
-- ===

CREATE TABLE idmt_smt_guitar_metadata (
    id_recording UUID PRIMARY KEY
        REFERENCES recordings(id_recording)
        ON DELETE CASCADE,

    instrument TEXT,
    instrument_model TEXT,
    pick_up_setting TEXT,
    instrument_tuning TEXT,
    audio_effects TEXT,
    recording_date DATE,
    recording_artist TEXT,
    instrument_body_material TEXT,
    instrument_string_material TEXT,
    composer TEXT,
    recording_source TEXT
);

CREATE INDEX index_idmt_instrument_model
    ON idmt_smt_guitar_metadata(instrument_model);

CREATE INDEX index_idmt_recording_artist
    ON idmt_smt_guitar_metadata(recording_artist);


-- ===
-- AUDIO FILES (MINIO)
-- ===

CREATE TABLE audio_files (
    id_audio UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    id_recording UUID NOT NULL
        REFERENCES recordings(id_recording)
        ON DELETE CASCADE,

    audio_type TEXT NOT NULL,
    uri TEXT NOT NULL UNIQUE,

    sample_rate INTEGER,
    channels INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT sample_rate_positive
        CHECK (sample_rate IS NULL OR sample_rate > 0),

    CONSTRAINT channels_valid
        CHECK (channels IS NULL OR channels > 0)
);

CREATE INDEX index_audio_files_recording
    ON audio_files(id_recording);

CREATE INDEX index_audio_files_type
    ON audio_files(audio_type);


-- ===
-- ANNOTATION FILES (MINIO)
-- ===

CREATE TABLE annotation_files (
    id_annotation UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    id_recording UUID NOT NULL
        REFERENCES recordings(id_recording)
        ON DELETE CASCADE,

    annotation_type TEXT NOT NULL,
    uri TEXT NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX index_annotation_files_recording
    ON annotation_files(id_recording);

CREATE INDEX index_annotation_files_type
    ON annotation_files(annotation_type);