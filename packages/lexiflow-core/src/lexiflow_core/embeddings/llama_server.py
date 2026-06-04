"""Built-in llama-server embedding provider."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from lexiflow_core.llm.llama_server import HTTPResponse, UrlOpener, _DefaultOpener
from lexiflow_core.vectors.models import EMBEDDING_DIM

_DEFAULT_EMBED_SERVER_URL = "http://127.0.0.1:8081"


class LlamaServerEmbedError(Exception):
    """Raised when llama-server embedding fails."""


def _embeddings_request_body(*, model: str, text: str) -> dict[str, object]:
    return {
        "model": model,
        "input": text,
        "encoding_format": "float",
    }


def _parse_embeddings_payload(payload: dict[str, object]) -> list[float]:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise LlamaServerEmbedError("llama-server response missing 'data'")
    first = data[0]
    if not isinstance(first, dict):
        raise LlamaServerEmbedError("llama-server response has invalid 'data' entry")
    embedding = first.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise LlamaServerEmbedError("llama-server returned empty embedding")
    if not all(isinstance(value, (int, float)) for value in embedding):
        raise LlamaServerEmbedError("llama-server returned invalid embedding values")
    vector = [float(value) for value in embedding]
    if len(vector) != EMBEDDING_DIM:
        msg = f"expected {EMBEDDING_DIM} dimensions, got {len(vector)}"
        raise LlamaServerEmbedError(msg)
    return vector


class LlamaServerEmbedder:
    """Call a managed llama-server instance for text embeddings."""

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_EMBED_SERVER_URL,
        model: str | None = None,
        opener: UrlOpener | None = None,
        timeout: float = 300.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        if model is None:
            from lexiflow_core.embeddings.pins import pinned_embedding_hf_model

            model = pinned_embedding_hf_model()
        self._model = model
        self._opener = opener if opener is not None else _DefaultOpener()
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def model(self) -> str:
        return self._model

    def embed(self, text: str) -> list[float]:
        body = json.dumps(
            _embeddings_request_body(model=self._model, text=text)
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/v1/embeddings",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        response: HTTPResponse | None = None
        try:
            response = self._opener.open(request, timeout=self._timeout)
            status = getattr(response, "status", None)
            if status is not None and not (200 <= status < 300):
                raise LlamaServerEmbedError(f"llama-server returned HTTP {status}")
            raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            raise LlamaServerEmbedError(
                f"llama-server request failed: HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise LlamaServerEmbedError(
                f"llama-server request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise LlamaServerEmbedError("llama-server request timed out") from exc
        except OSError as exc:
            raise LlamaServerEmbedError(f"llama-server request failed: {exc}") from exc
        finally:
            if response is not None:
                response.close()

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LlamaServerEmbedError("llama-server returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise LlamaServerEmbedError("llama-server returned invalid JSON")
        return _parse_embeddings_payload(payload)
