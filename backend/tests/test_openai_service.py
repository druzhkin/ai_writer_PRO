"""
Tests for OpenAI service functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.openai_service import OpenAIService


class TestOpenAIService:
    """Test OpenAI service operations."""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance."""
        return OpenAIService()
    
    @pytest.fixture
    def sample_texts(self):
        """Sample texts for testing."""
        return [
            "This is the first sample text for style analysis. It contains multiple sentences and demonstrates a particular writing style.",
            "Here is another sample text. This one has a different tone and structure, but maintains consistency in certain aspects.",
            "The third sample text completes our collection. It shows how the writing style evolves while maintaining core characteristics."
        ]
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "overall_style": {
                                "tone": "professional and informative",
                                "formality": "formal",
                                "voice": "authoritative and clear",
                                "personality": "confident and structured"
                            },
                            "language_characteristics": {
                                "vocabulary_level": "intermediate",
                                "sentence_structure": "mixed",
                                "paragraph_structure": "well-organized",
                                "word_choice": "precise and clear"
                            },
                            "writing_patterns": {
                                "sentence_length": "mixed",
                                "punctuation_usage": "standard",
                                "transition_usage": "effective",
                                "repetition_patterns": "minimal"
                            },
                            "content_organization": {
                                "structure_approach": "logical and sequential",
                                "introduction_style": "direct and clear",
                                "conclusion_style": "summarizing",
                                "argumentation_style": "evidence-based"
                            },
                            "unique_elements": {
                                "distinctive_features": ["clear structure", "professional tone"],
                                "common_phrases": ["for example", "in addition"],
                                "writing_quirks": ["consistent formatting"]
                            },
                            "readability_metrics": {
                                "complexity_level": "moderate",
                                "target_audience": "general professional",
                                "clarity_score": "high"
                            },
                            "style_recommendations": {
                                "strengths": ["clarity", "organization"],
                                "areas_for_improvement": ["variety in sentence structure"],
                                "consistency_notes": "maintains consistent professional tone"
                            }
                        })
                    }
                }
            ]
        }
    
    @patch('app.services.openai_service.openai.OpenAI')
    @pytest.mark.asyncio
    async def test_analyze_writing_style_success(self, mock_openai_class, openai_service, sample_texts, mock_openai_response):
        """Test successful writing style analysis."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client
        openai_service.client = mock_client
        
        success, message, analysis_result = await openai_service.analyze_writing_style(
            sample_texts, "Test Style", "Additional context"
        )
        
        assert success is True
        assert "completed successfully" in message
        assert analysis_result is not None
        assert "analysis_timestamp" in analysis_result
        assert "model_used" in analysis_result
        assert "texts_analyzed" in analysis_result
        assert "ai_analysis" in analysis_result
        assert "technical_analysis" in analysis_result
        assert "confidence_score" in analysis_result
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_writing_style_no_client(self, openai_service, sample_texts):
        """Test writing style analysis when client is not initialized."""
        openai_service.client = None
        
        success, message, analysis_result = await openai_service.analyze_writing_style(
            sample_texts, "Test Style"
        )
        
        assert success is False
        assert "not initialized" in message
        assert analysis_result is None
    
    @pytest.mark.asyncio
    async def test_analyze_writing_style_empty_texts(self, openai_service):
        """Test writing style analysis with empty texts."""
        openai_service.client = Mock()  # Mock client exists
        
        success, message, analysis_result = await openai_service.analyze_writing_style(
            [], "Test Style"
        )
        
        assert success is False
        assert "No valid texts" in message
        assert analysis_result is None
    
    @patch('app.services.openai_service.openai.OpenAI')
    @pytest.mark.asyncio
    async def test_analyze_writing_style_api_error(self, mock_openai_class, openai_service, sample_texts):
        """Test writing style analysis with API error."""
        # Mock OpenAI client with error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        openai_service.client = mock_client
        
        success, message, analysis_result = await openai_service.analyze_writing_style(
            sample_texts, "Test Style"
        )
        
        assert success is False
        assert "failed" in message
        assert analysis_result is None
    
    def test_extract_json_from_response_valid(self, openai_service, mock_openai_response):
        """Test JSON extraction from valid response."""
        response_text = mock_openai_response["choices"][0]["message"]["content"]
        
        result = openai_service._extract_json_from_response(response_text)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "overall_style" in result
        assert "language_characteristics" in result
    
    def test_extract_json_from_response_invalid(self, openai_service):
        """Test JSON extraction from invalid response."""
        response_text = "This is not valid JSON content."
        
        result = openai_service._extract_json_from_response(response_text)
        
        assert result is None
    
    def test_extract_json_from_response_markdown(self, openai_service):
        """Test JSON extraction from markdown-wrapped response."""
        json_content = '{"test": "value", "nested": {"key": "value"}}'
        response_text = f"```json\n{json_content}\n```"
        
        result = openai_service._extract_json_from_response(response_text)
        
        assert result is not None
        assert result["test"] == "value"
        assert result["nested"]["key"] == "value"
    
    def test_enhance_analysis(self, openai_service, sample_texts):
        """Test analysis enhancement."""
        analysis_data = {
            "overall_style": {"tone": "professional"},
            "language_characteristics": {"vocabulary_level": "intermediate"}
        }
        
        enhanced = openai_service._enhance_analysis(analysis_data, sample_texts)
        
        assert "analysis_timestamp" in enhanced
        assert "model_used" in enhanced
        assert "texts_analyzed" in enhanced
        assert "total_characters" in enhanced
        assert "technical_analysis" in enhanced
        assert "ai_analysis" in enhanced
        assert "confidence_score" in enhanced
        
        assert enhanced["texts_analyzed"] == len(sample_texts)
        assert enhanced["total_characters"] == sum(len(text) for text in sample_texts)
        assert enhanced["ai_analysis"] == analysis_data
    
    def test_calculate_confidence_score(self, openai_service, sample_texts):
        """Test confidence score calculation."""
        # Test with complete analysis
        complete_analysis = {
            "overall_style": {"tone": "professional"},
            "language_characteristics": {"vocabulary_level": "intermediate"},
            "writing_patterns": {"sentence_length": "mixed"},
            "content_organization": {"structure_approach": "logical"},
            "unique_elements": {"distinctive_features": ["clarity"]}
        }
        
        confidence = openai_service._calculate_confidence_score(complete_analysis, sample_texts)
        
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be high for complete analysis with good text length
    
    def test_calculate_confidence_score_incomplete(self, openai_service):
        """Test confidence score calculation with incomplete analysis."""
        incomplete_analysis = {
            "overall_style": {"tone": "professional"}
        }
        
        short_texts = ["Short text."]
        
        confidence = openai_service._calculate_confidence_score(incomplete_analysis, short_texts)
        
        assert 0 <= confidence <= 1
        assert confidence < 0.5  # Should be lower for incomplete analysis
    
    @patch('app.services.openai_service.openai.OpenAI')
    @pytest.mark.asyncio
    async def test_generate_style_guidelines_success(self, mock_openai_class, openai_service):
        """Test successful style guidelines generation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = {
            "choices": [{"message": {"content": "# Writing Guidelines\n\n## Tone and Voice\n- Maintain professional tone"}}]
        }
        mock_openai_class.return_value = mock_client
        openai_service.client = mock_client
        
        analysis_data = {
            "overall_style": {"tone": "professional"},
            "language_characteristics": {"vocabulary_level": "intermediate"}
        }
        
        success, message, guidelines = await openai_service.generate_style_guidelines(
            analysis_data, "Test Style"
        )
        
        assert success is True
        assert "generated successfully" in message
        assert guidelines is not None
        assert "Writing Guidelines" in guidelines
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_style_guidelines_no_client(self, openai_service):
        """Test style guidelines generation when client is not initialized."""
        openai_service.client = None
        
        analysis_data = {"overall_style": {"tone": "professional"}}
        
        success, message, guidelines = await openai_service.generate_style_guidelines(
            analysis_data, "Test Style"
        )
        
        assert success is False
        assert "not initialized" in message
        assert guidelines is None
    
    @patch('app.services.openai_service.openai.OpenAI')
    @pytest.mark.asyncio
    async def test_compare_styles_success(self, mock_openai_class, openai_service):
        """Test successful style comparison."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "similarities": {"tone": "both professional"},
                "differences": {"structure": "different approaches"},
                "key_distinguishing_features": {
                    "style1_unique": ["feature1"],
                    "style2_unique": ["feature2"]
                },
                "compatibility_score": 0.7,
                "recommendations": {
                    "when_to_use_style1": "formal contexts",
                    "when_to_use_style2": "casual contexts"
                }
            })}}]
        }
        mock_openai_class.return_value = mock_client
        openai_service.client = mock_client
        
        style1_data = {"overall_style": {"tone": "professional"}}
        style2_data = {"overall_style": {"tone": "casual"}}
        
        success, message, comparison = await openai_service.compare_styles(
            style1_data, style2_data, "Style 1", "Style 2"
        )
        
        assert success is True
        assert "completed successfully" in message
        assert comparison is not None
        assert "similarities" in comparison
        assert "differences" in comparison
        assert "compatibility_score" in comparison
        
        # Verify OpenAI API was called
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compare_styles_no_client(self, openai_service):
        """Test style comparison when client is not initialized."""
        openai_service.client = None
        
        style1_data = {"overall_style": {"tone": "professional"}}
        style2_data = {"overall_style": {"tone": "casual"}}
        
        success, message, comparison = await openai_service.compare_styles(
            style1_data, style2_data, "Style 1", "Style 2"
        )
        
        assert success is False
        assert "not initialized" in message
        assert comparison is None


class TestOpenAIServiceIntegration:
    """Integration tests for OpenAI service."""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        openai_service = OpenAIService()
        
        # Skip if OpenAI is not configured
        if not openai_service.client:
            pytest.skip("OpenAI client not configured")
        
        sample_texts = [
            "This is a professional document. It demonstrates clear structure and formal language.",
            "The writing maintains consistency throughout. Each paragraph builds upon the previous one.",
            "Technical terminology is used appropriately. The tone remains authoritative yet accessible."
        ]
        
        success, message, analysis_result = await openai_service.analyze_writing_style(
            sample_texts, "Professional Style", "Business documentation"
        )
        
        if success:
            assert analysis_result is not None
            assert "ai_analysis" in analysis_result
            assert "technical_analysis" in analysis_result
            assert "confidence_score" in analysis_result
        else:
            # If it fails, it should be due to API issues, not code issues
            assert "API" in message or "rate limit" in message or "timeout" in message
