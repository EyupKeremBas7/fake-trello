import re

import bleach

ALLOWED_TAGS = [
    "a", "abbr", "acronym", "b", "blockquote", "br", "code", "em",
    "i", "li", "ol", "p", "pre", "s", "span", "strike", "strong",
    "sub", "sup", "u", "ul"
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "abbr": ["title"],
    "acronym": ["title"],
    "*": ["class"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(value: str | None) -> str | None:
    if value is None:
        return None

    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )


def sanitize_plain_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = bleach.clean(value, tags=[], strip=True)

    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def sanitize_url(value: str | None) -> str | None:

    if not value:
        return None

    value = value.strip()

    if value.startswith(('http://', 'https://')):
        return value

    if value.startswith('data:image/'):
        return value

    return None


def sanitize_email(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = bleach.clean(value, tags=[], strip=True)

    return cleaned.lower().strip()


def escape_for_log(value: str | None, max_length: int = 500) -> str:
    if value is None:
        return "<None>"

    escaped = value.replace('\n', '\\n').replace('\r', '\\r')
    if len(escaped) > max_length:
        escaped = escaped[:max_length] + "...[truncated]"

    return escaped
