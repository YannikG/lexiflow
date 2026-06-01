"""Child-process entry for official google/gemma-4-E2B-it inference.

Run via ``python -m lexiflow_core.llm.gemma_inference``. The worker parent sets
``LEXIFLOW_GEMMA_MODEL_DIR`` and passes the prompt on stdin; completion is stdout.
Heavy imports stay in this subprocess only (ADR 0003 crash isolation).
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

_MODEL_DIR_ENV = "LEXIFLOW_GEMMA_MODEL_DIR"


def generate_completion(model_dir: Path, prompt: str) -> str:
    """Load the pinned Hub snapshot and return generated text."""
    transformers = importlib.import_module("transformers")
    tokenizer_cls: Any = transformers.AutoTokenizer
    model_cls: Any = transformers.AutoModelForCausalLM
    tokenizer = tokenizer_cls.from_pretrained(model_dir)
    model = model_cls.from_pretrained(
        model_dir,
        device_map="auto",
        torch_dtype="auto",
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=4096)
    input_len = inputs["input_ids"].shape[1]
    generated = outputs[0][input_len:]
    text: str = tokenizer.decode(generated, skip_special_tokens=True)
    return text


def main() -> None:
    raw_dir = os.environ.get(_MODEL_DIR_ENV)
    if not raw_dir:
        print(
            f"missing {_MODEL_DIR_ENV}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    model_dir = Path(raw_dir)
    prompt = sys.stdin.read()
    sys.stdout.write(generate_completion(model_dir, prompt))


if __name__ == "__main__":
    main()
