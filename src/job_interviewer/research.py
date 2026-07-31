"""Deterministic web retrieval used as evidence by the company research agent."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from job_interviewer.schemas import SearchBundle, SearchSource

SearchCallable = Callable[..., list[dict[str, Any]]]


def _normalize_result(item: dict[str, Any]) -> tuple[str, str, str, str]:
    title = str(item.get("title") or "Untitled source").strip()
    url = str(item.get("href") or item.get("url") or "").strip()
    snippet = str(item.get("body") or item.get("snippet") or "").strip()
    published = str(item.get("date") or item.get("published") or "").strip()
    return title, url, snippet, published


def collect_company_evidence(
    company_name: str,
    *,
    region: str = "sg-en",
    max_sources: int = 12,
    text_search: SearchCallable | None = None,
    news_search: SearchCallable | None = None,
) -> SearchBundle:
    """Collect and deduplicate snippets; synthesis remains the agent's responsibility."""
    company_name = company_name.strip()
    if not company_name or company_name.lower() in {"unknown", "unknown company", "confidential"}:
        return SearchBundle(
            company_name=company_name or "Unknown company",
            warnings=["Company could not be identified, so web research was skipped."],
        )

    if text_search is None or news_search is None:
        from ddgs import DDGS

        client = DDGS(timeout=12)
        text_search = client.text
        news_search = client.news

    queries = (
        f'"{company_name}" official company products services about',
        f'"{company_name}" careers values culture',
        f'"{company_name}" competitors industry strategy',
    )
    raw_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for query in queries:
        try:
            raw_results.extend(
                text_search(
                    query,
                    region=region,
                    safesearch="moderate",
                    max_results=4,
                )
                or []
            )
        except Exception as exc:
            warnings.append(f"Text search failed for one query: {exc}")

    try:
        raw_results.extend(
            news_search(
                f'"{company_name}"',
                region=region,
                safesearch="moderate",
                timelimit="y",
                max_results=5,
            )
            or []
        )
    except Exception as exc:
        warnings.append(f"News search failed: {exc}")

    sources: list[SearchSource] = []
    seen_urls: set[str] = set()
    for item in raw_results:
        title, url, snippet, published = _normalize_result(item)
        if not url or url in seen_urls or not snippet:
            continue
        seen_urls.add(url)
        sources.append(
            SearchSource(
                source_id=f"S{len(sources) + 1}",
                title=title,
                url=url,
                snippet=snippet[:1000],
                published=published,
            )
        )
        if len(sources) >= max_sources:
            break

    if not sources:
        warnings.append("No usable web results were returned; research will use only the JD.")
    return SearchBundle(company_name=company_name, sources=sources, warnings=warnings)

