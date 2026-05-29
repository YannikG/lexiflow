CREATE TABLE IF NOT EXISTS texts (
    id TEXT PRIMARY KEY,
    lang TEXT NOT NULL,
    group_display_name TEXT NOT NULL,
    group_folder_slug TEXT NOT NULL,
    title TEXT NOT NULL,
    text_slug TEXT NOT NULL,
    native_language TEXT NOT NULL,
    source_url TEXT,
    variants TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_texts_lang ON texts(lang);
