"""
Tests for NotebookLM search query building.
"""

import pytest
import os
from unittest.mock import patch

class TestDynamicSearchQuery:
    """Test the dynamic search query builder."""

    @pytest.fixture
    def mock_trusted_domains(self):
        """Mock the TRUSTED_DOMAINS constant."""
        with patch('contracts.source_policy.TRUSTED_DOMAINS', {"byjus.com", "vedantu.com", "khanacademy.org"}):
            yield

    def test_includes_all_trusted_domains(self, mock_trusted_domains):
        """Verify all trusted domains are in the query."""
        from ai_pipeline.notebooklm import _build_dynamic_search_query

        context = {
            "topic": "Gravity",
            "grade": "Grade 8",
            "subtopics": ["mass", "weight"]
        }

        query = _build_dynamic_search_query(context)

        # Should include all trusted domains
        assert "site:byjus.com" in query
        assert "site:vedantu.com" in query
        assert "site:khanacademy.org" in query

        # Should use OR between sites
        assert "OR" in query

    def test_includes_topic_and_grade(self, mock_trusted_domains):
        """Verify topic and grade are in query."""
        from ai_pipeline.notebooklm import _build_dynamic_search_query

        context = {
            "topic": "Force and Pressure",
            "grade": "Grade 8",
            "subtopics": []
        }

        query = _build_dynamic_search_query(context)

        assert "Force and Pressure" in query
        assert "Grade 8" in query

    def test_handles_empty_context(self, mock_trusted_domains):
        """Verify empty context doesn't crash."""
        from ai_pipeline.notebooklm import _build_dynamic_search_query

        query = _build_dynamic_search_query({})

        # Should still have site filters
        assert "site:" in query
        assert isinstance(query, str)

    def test_handles_list_subtopics(self, mock_trusted_domains):
        """Verify list subtopics are joined."""
        from ai_pipeline.notebooklm import _build_dynamic_search_query

        context = {
            "topic": "Physics",
            "subtopics": ["momentum", "velocity", "acceleration"]
        }

        query = _build_dynamic_search_query(context)

        assert "momentum" in query
        assert "velocity" in query

    def test_handles_string_subtopics(self, mock_trusted_domains):
        """Verify string subtopics work."""
        from ai_pipeline.notebooklm import _build_dynamic_search_query

        context = {
            "topic": "Chemistry",
            "subtopics": "atoms molecules"
        }

        query = _build_dynamic_search_query(context)

        assert "atoms molecules" in query

    def test_respects_custom_trusted_domains(self):
        """Verify it uses the specific domains present in TRUSTED_DOMAINS at runtime."""
        # Patch TRUSTED_DOMAINS with a custom set
        with patch('contracts.source_policy.TRUSTED_DOMAINS', {"custom-school.org"}):
            from ai_pipeline.notebooklm import _build_dynamic_search_query

            query = _build_dynamic_search_query({"topic": "Test"})

            assert "site:custom-school.org" in query
            assert "site:byjus.com" not in query

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
