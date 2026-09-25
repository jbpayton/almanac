"""A minimal client for OpenAI-compatible servers (LM Studio, llama-server, vLLM): chat, tools and embeddings."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class LLM:
    def __init__(self, url: str = "http://127.0.0.1:1234", reader: str = "", judge: str = "", embed: str = "",
                 reasoning_off: str = "lmstudio"):
        self.url, self.reader, self.judge_model, self.embed_model = url.rstrip("/"), reader, judge, embed
        self.reasoning_off = reasoning_off            # lmstudio: reasoning_effort; openai: chat_template_kwargs

    def _post(self, path: str, body: dict, timeout: float = 300.0) -> dict:
        for attempt in range(3):                      # servers under load fail now and then
            try:
                req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(),
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code < 500 or attempt == 2:
                    raise RuntimeError(f"{path} HTTP {e.code}: {e.read()[:300]!r}") from e
            except Exception:
                if attempt == 2:
                    raise
            time.sleep(5 * (attempt + 1))
        raise RuntimeError("unreachable")

    def chat(self, model: str, messages: List[Dict[str, Any]], max_tokens: int = 800,
             tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        body = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.0}
        if self.reasoning_off == "lmstudio":
            body["reasoning_effort"] = "none"
        else:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        if tools:
            body["tools"], body["tool_choice"] = tools, "auto"
        return self._post("/v1/chat/completions", body)["choices"][0]["message"]

    def embed(self, texts: List[str]) -> List[List[float]]:
        out = []
        for i in range(0, len(texts), 64):
            r = self._post("/v1/embeddings", {"model": self.embed_model, "input": texts[i:i + 64]})
            out += [d["embedding"] for d in sorted(r["data"], key=lambda d: d["index"])]
        return out
