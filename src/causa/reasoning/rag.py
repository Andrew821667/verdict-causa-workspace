from causa.core.models import LegalSource


def retrieve_sources(query: str, sources: list[LegalSource], limit: int = 5) -> list[LegalSource]:
    query_lower = query.lower()
    matches = [source for source in sources if query_lower in source.text.lower()]
    return matches[:limit]
