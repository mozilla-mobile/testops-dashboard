def adf_to_plain_text(adf):
    """
    Minimal ADF -> text flattener for Jira Cloud v3 comments.
    Handles paragraphs, text nodes, and hard breaks.
    """
    if not isinstance(adf, dict):
        return (adf or "") if isinstance(adf, str) else ""

    def walk(node):
        t = node.get("type")
        if t == "text":
            return node.get("text", "")
        if t in ("paragraph", "doc"):
            return "".join(walk(c) for c in node.get("content", []))
            + ("\n" if t == "paragraph" else "")
        if t == "hardBreak":
            return "\n"
        # fallback: recurse through content if present
        return "".join(walk(c) for c in node.get("content", []))
    text = walk(adf).strip()
    # collapse excessive newlines/spaces if you want:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()
