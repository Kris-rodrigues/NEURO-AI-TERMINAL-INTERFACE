from __future__ import annotations

import httpx

from pls.providers import ProviderError


class OllamaProvider:
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen3.5:2b"):
        self.host = host.rstrip("/")
        self.model = model

    def generate(self, system_prompt: str, user_message: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        # Try up to 2 times — first attempt may be slow while the model loads
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = httpx.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=120.0,  # generous timeout for cold-start model loading
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"].strip()
            except httpx.ConnectError:
                raise ProviderError(
                    f"Cannot connect to Ollama at {self.host}. Is it running?\n"
                    "Start it with: ollama serve"
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ProviderError(
                        f"Model '{self.model}' not found. Pull it with: ollama pull {self.model}"
                    )
                raise ProviderError(f"Ollama error: {e.response.status_code} — {e.response.text}")
            except KeyError:
                raise ProviderError("Unexpected response format from Ollama")
            except httpx.TimeoutException as e:
                last_error = e
                # On first timeout, wait briefly and retry (model may still be loading)
                if attempt == 0:
                    import time
                    time.sleep(2)
                    continue
        raise ProviderError(
            "Ollama request timed out after 2 attempts. "
            "The model might be loading slowly — try again, or run: ollama pull "
            + self.model
        )
