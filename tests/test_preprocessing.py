"""Tests for the data_preprocessing module."""

import sys
import os

# Ensure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_preprocessing import transform_text


class TestTransformText:
    """Unit tests for transform_text."""

    def test_basic_text(self):
        result = transform_text("Hello World, this is a Test!")
        assert isinstance(result, str)
        assert len(result) > 0
        # Should be lowered and stemmed
        assert "hello" in result or "world" in result or "test" in result

    def test_empty_string(self):
        result = transform_text("")
        assert result == ""

    def test_special_characters_only(self):
        result = transform_text("!@#$%^&*()")
        assert result == ""

    def test_stopwords_removed(self):
        result = transform_text("I am going to the store")
        # Common stop-words like 'i', 'am', 'to', 'the' should be removed
        tokens = result.split()
        assert "i" not in tokens
        assert "am" not in tokens
        assert "the" not in tokens

    def test_stemming(self):
        result = transform_text("running runs")
        tokens = result.split()
        # Both 'running' and 'runs' should stem to 'run'
        assert all(t == "run" for t in tokens)

    def test_long_text(self):
        long_text = "hello world " * 500
        result = transform_text(long_text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_numeric_input(self):
        result = transform_text("Call 12345 now")
        tokens = result.split()
        assert "12345" in tokens or "call" in tokens

    def test_non_string_input(self):
        result = transform_text(12345)
        assert isinstance(result, str)
