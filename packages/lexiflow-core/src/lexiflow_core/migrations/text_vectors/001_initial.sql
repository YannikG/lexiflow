CREATE VIRTUAL TABLE text_embeddings USING vec0(
  text_id TEXT PRIMARY KEY,
  embedding float[384]
);
