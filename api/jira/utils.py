from datetime import datetime, timezone


def _parse_adf_node(node):
    """Recursively extract readable text from an ADF node."""
    if not isinstance(node, dict):
        return ''
    node_type = node.get('type', '')
    if node_type == 'text':
        return node.get('text', '').strip()
    if node_type == 'date':
        ts = node.get('attrs', {}).get('timestamp')
        if ts:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d')
        return ''
    if node_type == 'status':
        return node.get('attrs', {}).get('text', '')
    parts = [_parse_adf_node(c) for c in node.get('content', [])]
    parts = [p for p in parts if p]
    if node_type == 'listItem':
        return '• ' + ' '.join(parts)
    return ' '.join(parts)


def extract_adf_text(nodes):
    """Extract readable text from an ADF content list."""
    if not isinstance(nodes, list) or not nodes:
        return None
    results = [_parse_adf_node(n) for n in nodes]
    results = [r for r in results if r]
    return ' | '.join(results)


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
