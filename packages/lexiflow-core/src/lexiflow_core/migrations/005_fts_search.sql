CREATE VIRTUAL TABLE IF NOT EXISTS text_search USING fts5(
    text_id UNINDEXED,
    lang UNINDEXED,
    variant UNINDEXED,
    title,
    body,
    tokenize='unicode61 remove_diacritics 2'
);
