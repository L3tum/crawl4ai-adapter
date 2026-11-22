from os import environ
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

CRAWL4AI_URL = environ.get("CRAWL4AI_URL", "http://owui-crawl4ai:11235")
CRAWL4AI_API_TOKEN = environ.get("CRAWL4AI_API_TOKEN")

app = FastAPI(title="crawl4ai-adapter")


class LoadRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)


def _pick_markdown(markdown_field: Any) -> str:
    if isinstance(markdown_field, str):
        return markdown_field.strip()

    if isinstance(markdown_field, dict):
        for key in (
            "fit_markdown",
            "raw_markdown",
            "markdown_with_citations",
            "references_markdown",
        ):
            value = markdown_field.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _pick_page_content(result: dict[str, Any]) -> str:
    content = _pick_markdown(result.get("markdown"))
    if content:
        return content

    extracted = result.get("extracted_content")
    if isinstance(extracted, str) and extracted.strip():
        return extracted.strip()

    cleaned_html = result.get("cleaned_html")
    if isinstance(cleaned_html, str) and cleaned_html.strip():
        return cleaned_html.strip()

    html = result.get("html")
    if isinstance(html, str) and html.strip():
        return html.strip()

    return ""


def _normalize_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list):
            return [r for r in payload["results"] if isinstance(r, dict)]
        if "url" in payload or "markdown" in payload or "html" in payload:
            return [payload]
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    return []


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/load")
def load(req: LoadRequest):
    if not req.urls:
        return []

    crawl_payload = {
        "urls": req.urls,
        "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"stream": False, "cache_mode": "bypass"},
        },
    }

    try:
        r = requests.post(
            f"{CRAWL4AI_URL}/crawl",
            json=crawl_payload,
            timeout=180,
            headers={"Authorization": f"Bearer {CRAWL4AI_API_TOKEN}"},
        )
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crawl4AI request failed: {e}")

    results = _normalize_results(raw)
    if not results:
        raise HTTPException(
            status_code=502, detail=f"Crawl4AI returned no usable results: {raw}"
        )

    out = []
    for result in results:
        page_content = _pick_page_content(result)
        url = result.get("url", "")

        metadata = (
            result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        )
        metadata["source"] = url
        metadata["url"] = url
        metadata["status_code"] = result.get("status_code")
        metadata["success"] = result.get("success")
        if result.get("error_message"):
            metadata["error_message"] = result.get("error_message")

        if page_content.strip():
            out.append(
                {
                    "page_content": page_content,
                    "metadata": metadata,
                }
            )

    if not out:
        raise HTTPException(
            status_code=502,
            detail=f"Crawl4AI crawled successfully but no text-like content was extracted: {raw}",
        )

    return out
