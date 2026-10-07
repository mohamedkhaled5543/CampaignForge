def format_knowledge_sources(docs, excerpt_chars=240):
    """Turn retrieved chunks into small dicts the UI can show."""
    sources = []
    for doc in docs:
        lines = [l.strip() for l in doc.page_content.splitlines() if l.strip()]
        first = lines[0] if lines else ""
        page = doc.metadata.get("page")
        page_no = page + 1 if isinstance(page, int) else None
        is_heading = 3 <= len(first) <= 70 and not first.endswith((".", ",", ";"))
        if is_heading:
            label = first.rstrip(":")
        else:
            label = f"Knowledge base, page {page_no}" if page_no else "Knowledge base"
        text = " ".join(doc.page_content.split())
        sources.append({"section": label, "page": page_no,
                        "excerpt": text[:excerpt_chars] + ("..." if len(text) > excerpt_chars else "")})
    return sources
