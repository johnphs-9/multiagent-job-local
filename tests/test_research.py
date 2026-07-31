from job_interviewer.research import collect_company_evidence


def test_company_research_deduplicates_sources() -> None:
    def text_search(*args, **kwargs):
        return [
            {"title": "About", "href": "https://example.com", "body": "Company information."},
            {"title": "Duplicate", "href": "https://example.com", "body": "Duplicate."},
        ]

    def news_search(*args, **kwargs):
        return [
            {
                "title": "News",
                "url": "https://news.example.com",
                "body": "A recent development.",
                "date": "2026-01-01",
            }
        ]

    bundle = collect_company_evidence(
        "Example",
        text_search=text_search,
        news_search=news_search,
    )

    assert [source.source_id for source in bundle.sources] == ["S1", "S2"]
    assert bundle.sources[1].published == "2026-01-01"


def test_unknown_company_skips_search() -> None:
    bundle = collect_company_evidence("Unknown company")
    assert bundle.sources == []
    assert "skipped" in bundle.warnings[0]

