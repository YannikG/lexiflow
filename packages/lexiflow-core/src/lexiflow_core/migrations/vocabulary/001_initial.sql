CREATE VIRTUAL TABLE word_embeddings USING vec0(
  lemma TEXT PRIMARY KEY,
  embedding float[384]
);
