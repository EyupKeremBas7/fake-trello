"""
Unit tests for the sanitization module.
"""
import pytest

from app.core.sanitization import (
    sanitize_html,
    sanitize_plain_text,
    sanitize_url,
    sanitize_email,
    escape_for_log,
)


class TestSanitizeHtml:
    """Tests for sanitize_html function."""

    def test_sanitize_html_strips_script_tags(self) -> None:
        """Test that script tags are removed."""
        input_text = "<script>alert('xss')</script>Hello"
        result = sanitize_html(input_text)
        assert result is not None
        assert "<script>" not in result
        assert "</script>" not in result
        assert "Hello" in result

    def test_sanitize_html_allows_safe_tags(self) -> None:
        """Test that safe HTML tags are preserved."""
        input_text = "<p>This is <strong>bold</strong> and <em>italic</em></p>"
        result = sanitize_html(input_text)
        assert result is not None
        assert "<p>" in result
        assert "<strong>" in result
        assert "<em>" in result

    def test_sanitize_html_allows_links(self) -> None:
        """Test that anchor tags are preserved."""
        input_text = '<a href="https://example.com">Link</a>'
        result = sanitize_html(input_text)
        assert result is not None
        assert "<a" in result
        assert 'href="https://example.com"' in result

    def test_sanitize_html_strips_onclick(self) -> None:
        """Test that event handlers are removed."""
        input_text = '<a href="#" onclick="evil()">Click me</a>'
        result = sanitize_html(input_text)
        assert result is not None
        assert "onclick" not in result

    def test_sanitize_html_strips_iframe(self) -> None:
        """Test that iframe tags are removed."""
        input_text = '<iframe src="https://evil.com"></iframe>Content'
        result = sanitize_html(input_text)
        assert result is not None
        assert "<iframe" not in result
        assert "Content" in result

    def test_sanitize_html_returns_none_for_none(self) -> None:
        """Test that None input returns None."""
        assert sanitize_html(None) is None

    def test_sanitize_html_handles_empty_string(self) -> None:
        """Test that empty string is handled."""
        result = sanitize_html("")
        assert result == ""


class TestSanitizePlainText:
    """Tests for sanitize_plain_text function."""

    def test_sanitize_plain_text_strips_all_html(self) -> None:
        """Test that all HTML is stripped."""
        input_text = "<p>Hello</p> <strong>World</strong>"
        result = sanitize_plain_text(input_text)
        assert result is not None
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_plain_text_strips_script(self) -> None:
        """Test that script tags and content are removed."""
        input_text = "<script>evil()</script>Safe text"
        result = sanitize_plain_text(input_text)
        assert result is not None
        assert "<script>" not in result
        assert "Safe text" in result

    def test_sanitize_plain_text_collapses_whitespace(self) -> None:
        """Test that multiple spaces are collapsed."""
        input_text = "Hello    World   Test"
        result = sanitize_plain_text(input_text)
        assert result is not None
        # Should have single spaces
        assert "  " not in result

    def test_sanitize_plain_text_strips_leading_trailing(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        input_text = "   Hello World   "
        result = sanitize_plain_text(input_text)
        assert result == "Hello World"

    def test_sanitize_plain_text_returns_none_for_none(self) -> None:
        """Test that None input returns None."""
        assert sanitize_plain_text(None) is None


class TestSanitizeUrl:
    """Tests for sanitize_url function."""

    def test_sanitize_url_allows_https(self) -> None:
        """Test that HTTPS URLs are allowed."""
        url = "https://example.com/image.jpg"
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_allows_http(self) -> None:
        """Test that HTTP URLs are allowed."""
        url = "http://example.com/image.jpg"
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_blocks_javascript(self) -> None:
        """Test that javascript: URLs are blocked."""
        url = "javascript:alert('xss')"
        result = sanitize_url(url)
        assert result is None

    def test_sanitize_url_blocks_data_non_image(self) -> None:
        """Test that non-image data URLs are blocked."""
        url = "data:text/html,<script>evil()</script>"
        result = sanitize_url(url)
        assert result is None

    def test_sanitize_url_allows_data_image(self) -> None:
        """Test that image data URLs are allowed."""
        url = "data:image/png;base64,iVBORw0KGgo..."
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_blocks_file(self) -> None:
        """Test that file: URLs are blocked."""
        url = "file:///etc/passwd"
        result = sanitize_url(url)
        assert result is None

    def test_sanitize_url_returns_none_for_none(self) -> None:
        """Test that None input returns None."""
        assert sanitize_url(None) is None

    def test_sanitize_url_returns_none_for_empty(self) -> None:
        """Test that empty string returns None."""
        assert sanitize_url("") is None


class TestSanitizeEmail:
    """Tests for sanitize_email function."""

    def test_sanitize_email_lowercases(self) -> None:
        """Test that email is lowercased."""
        email = "Test@Example.COM"
        result = sanitize_email(email)
        assert result == "test@example.com"

    def test_sanitize_email_strips_whitespace(self) -> None:
        """Test that whitespace is stripped."""
        email = "  test@example.com  "
        result = sanitize_email(email)
        assert result == "test@example.com"

    def test_sanitize_email_strips_html(self) -> None:
        """Test that HTML is stripped from email."""
        email = "<script>alert('xss')</script>test@example.com"
        result = sanitize_email(email)
        assert result is not None
        assert "<script>" not in result
        assert "test@example.com" in result

    def test_sanitize_email_returns_none_for_none(self) -> None:
        """Test that None input returns None."""
        assert sanitize_email(None) is None


class TestEscapeForLog:
    """Tests for escape_for_log function."""

    def test_escape_for_log_escapes_newlines(self) -> None:
        """Test that newlines are escaped."""
        text = "Line 1\nLine 2\rLine 3"
        result = escape_for_log(text)
        assert "\\n" in result
        assert "\\r" in result
        assert "\n" not in result
        assert "\r" not in result

    def test_escape_for_log_truncates_long_text(self) -> None:
        """Test that long text is truncated."""
        text = "x" * 1000
        result = escape_for_log(text)
        assert len(result) <= 520  # 500 + "...[truncated]"
        assert "[truncated]" in result

    def test_escape_for_log_handles_none(self) -> None:
        """Test that None returns <None>."""
        result = escape_for_log(None)
        assert result == "<None>"
