ALTER TABLE texts ADD COLUMN content_fingerprint TEXT;

CREATE INDEX IF NOT EXISTS idx_texts_lang_fingerprint
    ON texts(lang, content_fingerprint);
