"""
OpenAI service for style analysis using GPT models.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.utils.style_utils import extract_style_signatures, preprocess_text
from app.templates.prompts.content_generation import ContentGenerationPrompts


class OpenAIService:
    """Service for OpenAI API interactions and style analysis."""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client."""
        if settings.OPENAI_API_KEY:
            try:
                self.client = openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=settings.CONTENT_GENERATION_TIMEOUT
                )
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    async def analyze_writing_style(
        self, 
        texts: List[str], 
        style_profile_name: str,
        additional_context: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Analyze writing style from multiple texts.
        
        Args:
            texts: List of texts to analyze
            style_profile_name: Name of the style profile
            additional_context: Additional context for analysis
            
        Returns:
            Tuple of (success, error_message, analysis_result)
        """
        if not self.client:
            return False, "OpenAI client not initialized", None
        
        try:
            # Preprocess texts and handle edge cases
            processed_texts = []
            for text in texts:
                if text and text.strip():
                    processed = preprocess_text(text)
                    # Skip texts that are too short to be meaningful
                    if len(processed.strip()) >= 50:  # Minimum meaningful length
                        processed_texts.append(processed)
            
            if not processed_texts:
                return False, "No valid texts provided for analysis (minimum 50 characters required)", None
            
            # Handle edge case: too many texts
            if len(processed_texts) > 20:
                processed_texts = processed_texts[:20]  # Limit to first 20 texts
            
            # Combine texts for analysis
            combined_text = "\n\n---\n\n".join(processed_texts)
            
            # Truncate if too long (GPT-4 has token limits)
            max_chars = 50000  # Conservative limit
            if len(combined_text) > max_chars:
                # Try to truncate more intelligently by keeping complete texts
                truncated_texts = []
                current_length = 0
                for text in processed_texts:
                    if current_length + len(text) + 10 <= max_chars:  # +10 for separator
                        truncated_texts.append(text)
                        current_length += len(text) + 10
                    else:
                        break
                
                if truncated_texts:
                    combined_text = "\n\n---\n\n".join(truncated_texts)
                else:
                    # Fallback: truncate the first text
                    combined_text = processed_texts[0][:max_chars-3] + "..."
            
            # Create analysis prompt
            prompt = self._create_style_analysis_prompt(
                combined_text, 
                style_profile_name, 
                additional_context
            )
            
            # Make API call (retry logic handled by @retry decorator)
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert writing style analyst. Analyze the provided texts and return a comprehensive style analysis in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            # Parse response
            if not response or not response.choices:
                return False, "Empty response from OpenAI API", None
            
            analysis_text = response.choices[0].message.content
            
            if not analysis_text:
                return False, "No content in OpenAI API response", None
            
            # Extract JSON from response
            analysis_data = self._extract_json_from_response(analysis_text)
            
            if not analysis_data:
                return False, "Failed to parse analysis response as valid JSON", None
            
            # Validate analysis data structure
            if not self._validate_analysis_data(analysis_data):
                return False, "Analysis response does not contain required fields", None
            
            # Validate and enhance analysis
            enhanced_analysis = self._enhance_analysis(analysis_data, processed_texts)
            
            return True, "Style analysis completed successfully", enhanced_analysis
            
        except openai.RateLimitError:
            return False, "OpenAI API rate limit exceeded", None
        except openai.APITimeoutError:
            return False, "OpenAI API request timed out", None
        except openai.APIError as e:
            return False, f"OpenAI API error: {str(e)}", None
        except Exception as e:
            return False, f"Style analysis failed: {str(e)}", None
    
    def _create_style_analysis_prompt(
        self, 
        text: str, 
        style_profile_name: str, 
        additional_context: Optional[str] = None
    ) -> str:
        """Create prompt for style analysis."""
        
        context_part = ""
        if additional_context:
            context_part = f"\n\nAdditional Context: {additional_context}"
        
        prompt = f"""
Analyze the writing style of the following texts for the style profile "{style_profile_name}".

Texts to analyze:
{text}
{context_part}

Please provide a comprehensive style analysis in the following JSON format:

{{
    "overall_style": {{
        "tone": "description of the overall tone",
        "formality": "formal/informal/mixed",
        "voice": "description of the author's voice",
        "personality": "description of the writing personality"
    }},
    "language_characteristics": {{
        "vocabulary_level": "basic/intermediate/advanced",
        "sentence_structure": "simple/complex/mixed",
        "paragraph_structure": "description of paragraph organization",
        "word_choice": "description of word choice patterns"
    }},
    "writing_patterns": {{
        "sentence_length": "short/medium/long/mixed",
        "punctuation_usage": "description of punctuation patterns",
        "transition_usage": "description of how transitions are used",
        "repetition_patterns": "description of any repetition patterns"
    }},
    "content_organization": {{
        "structure_approach": "description of how content is organized",
        "introduction_style": "description of how topics are introduced",
        "conclusion_style": "description of how topics are concluded",
        "argumentation_style": "description of how arguments are presented"
    }},
    "unique_elements": {{
        "distinctive_features": ["list of distinctive writing features"],
        "common_phrases": ["list of commonly used phrases"],
        "writing_quirks": ["list of unique writing quirks"]
    }},
    "readability_metrics": {{
        "complexity_level": "simple/moderate/complex",
        "target_audience": "description of target audience",
        "clarity_score": "high/medium/low"
    }},
    "style_recommendations": {{
        "strengths": ["list of writing strengths"],
        "areas_for_improvement": ["list of areas for improvement"],
        "consistency_notes": "notes about style consistency"
    }}
}}

Please ensure the response is valid JSON and focuses on the distinctive elements that make this writing style unique.
"""
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from OpenAI response."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return None
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            try:
                # Remove markdown code blocks
                json_text = response_text.replace('```json', '').replace('```', '')
                json_text = json_text.strip()
                
                # Try parsing again
                return json.loads(json_text)
            except json.JSONDecodeError:
                return None
        except Exception:
            return None
    
    def _enhance_analysis(
        self, 
        analysis_data: Dict[str, Any], 
        texts: List[str]
    ) -> Dict[str, Any]:
        """Enhance analysis with additional metrics."""
        
        # Add technical analysis
        technical_analysis = {}
        for text in texts:
            if text.strip():
                style_signature = extract_style_signatures(text)
                technical_analysis.update(style_signature)
        
        # Add metadata
        enhanced_analysis = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "model_used": settings.OPENAI_MODEL,
            "texts_analyzed": len(texts),
            "total_characters": sum(len(text) for text in texts),
            "technical_analysis": technical_analysis,
            "ai_analysis": analysis_data,
            "confidence_score": self._calculate_confidence_score(analysis_data, texts)
        }
        
        return enhanced_analysis
    
    def _validate_analysis_data(self, analysis_data: Dict[str, Any]) -> bool:
        """Validate that analysis data contains required fields."""
        try:
            required_fields = [
                "overall_style", "language_characteristics", "writing_patterns",
                "content_organization", "unique_elements"
            ]
            
            for field in required_fields:
                if field not in analysis_data:
                    return False
                
                if not isinstance(analysis_data[field], dict):
                    return False
            
            # Check that required sub-fields exist
            if "tone" not in analysis_data.get("overall_style", {}):
                return False
            
            if "vocabulary_level" not in analysis_data.get("language_characteristics", {}):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_confidence_score(
        self, 
        analysis_data: Dict[str, Any], 
        texts: List[str]
    ) -> float:
        """Calculate confidence score for the analysis."""
        try:
            # Base confidence on text length and analysis completeness
            total_chars = sum(len(text) for text in texts)
            text_confidence = min(1.0, total_chars / 10000)  # More text = higher confidence
            
            # Check analysis completeness
            required_fields = [
                "overall_style", "language_characteristics", "writing_patterns",
                "content_organization", "unique_elements"
            ]
            completeness = sum(1 for field in required_fields if field in analysis_data) / len(required_fields)
            
            # Combine scores
            confidence = (text_confidence * 0.6) + (completeness * 0.4)
            return round(confidence, 3)
            
        except Exception:
            return 0.5  # Default confidence
    
    async def generate_style_guidelines(
        self, 
        analysis_data: Dict[str, Any], 
        style_profile_name: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate style guidelines from analysis.
        
        Args:
            analysis_data: Style analysis data
            style_profile_name: Name of the style profile
            
        Returns:
            Tuple of (success, error_message, guidelines)
        """
        if not self.client:
            return False, "OpenAI client not initialized", None
        
        try:
            # Create guidelines prompt
            prompt = f"""
Based on the following style analysis for "{style_profile_name}", generate practical writing guidelines that someone could follow to write in this style.

Style Analysis:
{json.dumps(analysis_data, indent=2)}

Please provide clear, actionable guidelines in the following format:

# Writing Guidelines for {style_profile_name}

## Tone and Voice
- [Guidelines for maintaining the appropriate tone]

## Language and Vocabulary
- [Guidelines for word choice and vocabulary level]

## Sentence Structure
- [Guidelines for sentence construction]

## Content Organization
- [Guidelines for structuring content]

## Key Elements to Include
- [Important elements that define this style]

## Common Pitfalls to Avoid
- [Things to avoid when writing in this style]

Make the guidelines practical and specific, with examples where helpful.
"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert writing coach. Create clear, actionable guidelines for writing in specific styles."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            guidelines = response.choices[0].message.content
            return True, "Style guidelines generated successfully", guidelines
            
        except Exception as e:
            return False, f"Failed to generate guidelines: {str(e)}", None
    
    async def compare_styles(
        self, 
        style1_data: Dict[str, Any], 
        style2_data: Dict[str, Any],
        style1_name: str,
        style2_name: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Compare two writing styles.
        
        Args:
            style1_data: First style analysis data
            style2_data: Second style analysis data
            style1_name: Name of first style
            style2_name: Name of second style
            
        Returns:
            Tuple of (success, error_message, comparison_result)
        """
        if not self.client:
            return False, "OpenAI client not initialized", None
        
        try:
            prompt = f"""
Compare the following two writing styles and provide a detailed comparison:

Style 1: {style1_name}
{json.dumps(style1_data, indent=2)}

Style 2: {style2_name}
{json.dumps(style2_data, indent=2)}

Please provide a comparison in the following JSON format:

{{
    "similarities": {{
        "tone": "description of tone similarities",
        "structure": "description of structural similarities",
        "language": "description of language similarities"
    }},
    "differences": {{
        "tone": "description of tone differences",
        "structure": "description of structural differences",
        "language": "description of language differences"
    }},
    "key_distinguishing_features": {{
        "style1_unique": ["unique features of style 1"],
        "style2_unique": ["unique features of style 2"]
    }},
    "compatibility_score": 0.0-1.0,
    "recommendations": {{
        "when_to_use_style1": "description of when to use style 1",
        "when_to_use_style2": "description of when to use style 2",
        "blending_possibilities": "description of how styles could be blended"
    }}
}}
"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert writing style analyst. Compare writing styles objectively and provide actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            comparison_text = response.choices[0].message.content
            comparison_data = self._extract_json_from_response(comparison_text)
            
            if not comparison_data:
                return False, "Failed to parse comparison response", None
            
            return True, "Style comparison completed successfully", comparison_data
            
        except Exception as e:
            return False, f"Style comparison failed: {str(e)}", None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    async def generate_content(
        self,
        title: str,
        brief: Optional[str] = None,
        content_type: str = "article",
        style_analysis: Optional[Dict[str, Any]] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None,
        model: str = "gpt-4-turbo-preview"
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate content using OpenAI GPT models.
        
        Args:
            title: Content title
            brief: Content brief or outline
            content_type: Type of content to generate
            style_analysis: Style analysis data to apply
            target_length: Target word count
            additional_instructions: Additional generation instructions
            model: OpenAI model to use
            
        Returns:
            Tuple of (success, error_message, generation_result)
        """
        if not self.client:
            return False, "OpenAI client not initialized", None
        
        try:
            # Create content generation prompt using templates
            style_guidance = self._extract_style_guidance(style_analysis) if style_analysis else None
            prompt = self._get_content_generation_prompt(
                content_type, title, brief, style_guidance, 
                target_length, additional_instructions
            )
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content writer. Generate high-quality, engaging content that matches the specified style and requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            if not response or not response.choices:
                return False, "Empty response from OpenAI API", None
            
            generated_text = response.choices[0].message.content
            if not generated_text:
                return False, "No content generated", None
            
            # Calculate token usage
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Calculate cost
            estimated_cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            # Calculate text metrics
            word_count = len(generated_text.split())
            character_count = len(generated_text)
            
            result = {
                "generated_text": generated_text,
                "word_count": word_count,
                "character_count": character_count,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": estimated_cost,
                "model_used": model,
                "generation_prompt": prompt
            }
            
            return True, "Content generated successfully", result
            
        except openai.RateLimitError:
            return False, "OpenAI API rate limit exceeded", None
        except openai.APITimeoutError:
            return False, "OpenAI API request timed out", None
        except openai.APIError as e:
            return False, f"OpenAI API error: {str(e)}", None
        except Exception as e:
            return False, f"Content generation failed: {str(e)}", None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError))
    )
    async def edit_content(
        self,
        current_text: str,
        edit_prompt: str,
        edit_type: str = "general",
        model: str = "gpt-4-turbo-preview"
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Edit existing content using OpenAI GPT models.
        
        Args:
            current_text: Current content text
            edit_prompt: Instructions for the edit
            edit_type: Type of edit being requested
            model: OpenAI model to use
            
        Returns:
            Tuple of (success, error_message, edit_result)
        """
        if not self.client:
            return False, "OpenAI client not initialized", None
        
        try:
            # Create content editing prompt using templates
            prompt = ContentGenerationPrompts.get_edit_prompt(current_text, edit_prompt, edit_type)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content editor. Make precise edits to content based on the provided instructions while maintaining quality and coherence."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            if not response or not response.choices:
                return False, "Empty response from OpenAI API", None
            
            edited_text = response.choices[0].message.content
            if not edited_text:
                return False, "No edited content generated", None
            
            # Calculate token usage
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            # Calculate cost
            estimated_cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            # Calculate text metrics
            previous_word_count = len(current_text.split())
            new_word_count = len(edited_text.split())
            word_count_change = new_word_count - previous_word_count
            
            previous_character_count = len(current_text)
            new_character_count = len(edited_text)
            character_count_change = new_character_count - previous_character_count
            
            # Generate detailed diff using utility
            from app.utils.content_utils import calculate_text_diff
            import json
            diff_result = calculate_text_diff(current_text, edited_text)
            diff_summary = diff_result["summary"]
            diff_lines = json.dumps(diff_result["diff_lines"]) if diff_result["diff_lines"] else None
            
            result = {
                "previous_text": current_text,
                "new_text": edited_text,
                "previous_word_count": previous_word_count,
                "new_word_count": new_word_count,
                "word_count_change": word_count_change,
                "previous_character_count": previous_character_count,
                "new_character_count": new_character_count,
                "character_count_change": character_count_change,
                "diff_summary": diff_summary,
                "diff_lines": diff_lines,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": estimated_cost,
                "model_used": model,
                "generation_prompt": prompt
            }
            
            return True, "Content edited successfully", result
            
        except openai.RateLimitError:
            return False, "OpenAI API rate limit exceeded", None
        except openai.APITimeoutError:
            return False, "OpenAI API request timed out", None
        except openai.APIError as e:
            return False, f"OpenAI API error: {str(e)}", None
        except Exception as e:
            return False, f"Content editing failed: {str(e)}", None
    
    def _get_content_generation_prompt(
        self,
        content_type: str,
        title: str,
        brief: Optional[str],
        style_guidance: Optional[str],
        target_length: Optional[int],
        additional_instructions: Optional[str]
    ) -> str:
        """Get content generation prompt using templates."""
        
        # Map content types to prompt methods
        prompt_methods = {
            "article": ContentGenerationPrompts.get_article_prompt,
            "blog_post": ContentGenerationPrompts.get_blog_post_prompt,
            "marketing_copy": ContentGenerationPrompts.get_marketing_copy_prompt,
            "product_description": ContentGenerationPrompts.get_product_description_prompt,
            "email": ContentGenerationPrompts.get_email_prompt,
            "social_media": ContentGenerationPrompts.get_social_media_prompt,
            "press_release": ContentGenerationPrompts.get_press_release_prompt,
            "white_paper": ContentGenerationPrompts.get_white_paper_prompt,
            "case_study": ContentGenerationPrompts.get_case_study_prompt,
            "news_letter": ContentGenerationPrompts.get_newsletter_prompt
        }
        
        # Get the appropriate prompt method
        prompt_method = prompt_methods.get(content_type, ContentGenerationPrompts.get_article_prompt)
        
        # Generate prompt with style guidance if available
        if style_guidance:
            base_prompt = prompt_method(title, brief, None, target_length, additional_instructions)
            return ContentGenerationPrompts.get_style_application_prompt(content_type, {"ai_analysis": {"overall_style": {"tone": style_guidance}}}, base_prompt)
        else:
            return prompt_method(title, brief, style_guidance, target_length, additional_instructions)
    
# Removed _create_content_editing_prompt - now using ContentGenerationPrompts.get_edit_prompt
    
    def _extract_style_guidance(self, style_analysis: Dict[str, Any]) -> str:
        """Extract style guidance from analysis data."""
        guidance_parts = []
        
        # Extract from AI analysis if available
        ai_analysis = style_analysis.get("ai_analysis", {})
        
        if "overall_style" in ai_analysis:
            style = ai_analysis["overall_style"]
            if "tone" in style:
                guidance_parts.append(f"Tone: {style['tone']}")
            if "formality" in style:
                guidance_parts.append(f"Formality Level: {style['formality']}")
            if "voice" in style:
                guidance_parts.append(f"Voice: {style['voice']}")
        
        if "language_characteristics" in ai_analysis:
            lang = ai_analysis["language_characteristics"]
            if "vocabulary_level" in lang:
                guidance_parts.append(f"Vocabulary Level: {lang['vocabulary_level']}")
            if "sentence_structure" in lang:
                guidance_parts.append(f"Sentence Structure: {lang['sentence_structure']}")
        
        if "writing_patterns" in ai_analysis:
            patterns = ai_analysis["writing_patterns"]
            if "sentence_length" in patterns:
                guidance_parts.append(f"Sentence Length: {patterns['sentence_length']}")
        
        return "\n".join(guidance_parts) if guidance_parts else "Follow the established writing style patterns."
    
# Removed _get_content_type_instructions - now using ContentGenerationPrompts templates
    
# Removed _generate_diff_summary - now using calculate_text_diff utility
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for API usage."""
        # Get pricing based on model
        if "gpt-4" in model.lower():
            if "turbo" in model.lower():
                input_cost_per_1k = settings.OPENAI_GPT4_TURBO_INPUT_COST_PER_1K
                output_cost_per_1k = settings.OPENAI_GPT4_TURBO_OUTPUT_COST_PER_1K
            else:
                input_cost_per_1k = settings.OPENAI_GPT4_INPUT_COST_PER_1K
                output_cost_per_1k = settings.OPENAI_GPT4_OUTPUT_COST_PER_1K
        else:
            # Default to GPT-4 pricing for unknown models
            input_cost_per_1k = settings.OPENAI_GPT4_INPUT_COST_PER_1K
            output_cost_per_1k = settings.OPENAI_GPT4_OUTPUT_COST_PER_1K
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return round(input_cost + output_cost, 6)
    
    def calculate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough approximation: 1 token ≈ 4 characters for English text
        return max(1, len(text) // 4)