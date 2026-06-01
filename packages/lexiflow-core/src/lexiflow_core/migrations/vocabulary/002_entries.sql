CREATE TABLE vocabulary_entries (
  lemma TEXT PRIMARY KEY NOT NULL,
  translation TEXT NOT NULL,
  explanation TEXT NOT NULL DEFAULT '',
  level_when_learned TEXT NOT NULL,
  difficulty_rating TEXT NOT NULL DEFAULT 'hard',
  surface_form TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
