"""
Prompt templates for content generation scenarios.
"""

from typing import Dict, Any, Optional


class ContentGenerationPrompts:
    """Collection of prompt templates for content generation."""
    
    @staticmethod
    def get_article_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for article creation."""
        prompt_parts = [
            f"Write a comprehensive article with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Article Requirements:
- Write a comprehensive, informative article with clear structure
- Include an engaging introduction that hooks the reader
- Develop well-structured body sections with supporting details
- Provide a strong conclusion that summarizes key points
- Use clear and concise language throughout
- Ensure proper grammar and spelling
- Make the content informative and valuable to readers
- Maintain consistency in tone and style
- Include appropriate transitions between sections
- Use subheadings to organize content effectively
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_blog_post_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for blog post creation."""
        prompt_parts = [
            f"Write an engaging blog post with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Blog Post Requirements:
- Write an engaging blog post that's conversational and relatable
- Include personal insights and opinions where appropriate
- Use a friendly, approachable tone
- Encourage reader interaction and engagement
- Include relevant examples and anecdotes
- Use shorter paragraphs for better readability
- Include a compelling call-to-action
- Make it shareable and valuable to the target audience
- Use subheadings to break up content
- End with questions or prompts for reader engagement
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_marketing_copy_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for marketing copy creation."""
        prompt_parts = [
            f"Write persuasive marketing copy with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Marketing Copy Requirements:
- Write persuasive marketing copy that highlights benefits
- Focus on customer pain points and solutions
- Include compelling calls-to-action
- Use power words and emotional triggers
- Create urgency and scarcity where appropriate
- Highlight unique value propositions
- Use social proof and testimonials if relevant
- Make it conversion-focused
- Use clear, benefit-driven headlines
- Include multiple touchpoints for engagement
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_product_description_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for product description creation."""
        prompt_parts = [
            f"Write a detailed product description with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Product Description Requirements:
- Write clear, detailed product descriptions
- Highlight key features and benefits
- Focus on customer value propositions
- Use descriptive and compelling language
- Include technical specifications if relevant
- Address common customer questions
- Use bullet points for easy scanning
- Include usage scenarios and applications
- Make it SEO-friendly with relevant keywords
- End with a clear call-to-action
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_email_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for email content creation."""
        prompt_parts = [
            f"Write professional email content with the subject: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Email Content Requirements:
- Write professional email content with clear subject line
- Start with an engaging opening that captures attention
- Use clear, concise language throughout
- Structure content with proper paragraphs
- Include relevant details and information
- Use appropriate tone for the audience
- Include clear next steps or call-to-action
- End with professional closing
- Keep it scannable and easy to read
- Ensure mobile-friendly formatting
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_social_media_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for social media content creation."""
        prompt_parts = [
            f"Write engaging social media content with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Social Media Content Requirements:
- Write engaging social media content that's concise and shareable
- Use attention-grabbing headlines and hooks
- Include relevant hashtags where appropriate
- Encourage interaction and engagement
- Use conversational and relatable tone
- Include visual elements suggestions if relevant
- Make it platform-appropriate
- Include clear call-to-action
- Use emojis strategically to enhance engagement
- Keep it authentic and brand-consistent
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_press_release_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for press release creation."""
        prompt_parts = [
            f"Write a professional press release with the headline: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Press Release Requirements:
- Write a professional press release following standard format
- Include compelling headline and subheadline
- Start with strong lead paragraph (who, what, when, where, why)
- Provide supporting details and quotes
- Use third-person, objective tone
- Include relevant background information
- End with company boilerplate
- Use proper press release structure
- Include contact information section
- Make it newsworthy and media-friendly
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_white_paper_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for white paper creation."""
        prompt_parts = [
            f"Write a comprehensive white paper with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
White Paper Requirements:
- Write a comprehensive white paper with executive summary
- Include detailed analysis and research findings
- Provide actionable insights and recommendations
- Use authoritative and professional tone
- Include data, statistics, and evidence
- Structure with clear sections and subsections
- Include methodology and sources
- Provide practical applications
- End with conclusions and next steps
- Make it valuable for decision-makers
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_case_study_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for case study creation."""
        prompt_parts = [
            f"Write a detailed case study with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Case Study Requirements:
- Write a detailed case study with clear problem statement
- Describe the solution approach and implementation
- Include specific details and metrics
- Show before and after scenarios
- Include quotes and testimonials
- Provide lessons learned and insights
- Use storytelling techniques
- Include relevant background context
- Highlight key success factors
- End with actionable takeaways
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_newsletter_prompt(
        title: str,
        brief: Optional[str] = None,
        style_guidance: Optional[str] = None,
        target_length: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Generate prompt for newsletter creation."""
        prompt_parts = [
            f"Write an engaging newsletter with the title: '{title}'"
        ]
        
        if brief:
            prompt_parts.append(f"Brief/Outline: {brief}")
        
        if target_length:
            prompt_parts.append(f"Target length: approximately {target_length} words")
        
        if style_guidance:
            prompt_parts.append(f"Writing Style Guidelines:\n{style_guidance}")
        
        if additional_instructions:
            prompt_parts.append(f"Additional Instructions: {additional_instructions}")
        
        prompt_parts.extend([
            """
Newsletter Requirements:
- Write an engaging newsletter with multiple sections
- Include clear formatting and structure
- Provide valuable content for subscribers
- Use conversational and friendly tone
- Include relevant updates and news
- Add personal touches and insights
- Include calls-to-action
- Make it scannable with subheadings
- Include links and resources
- End with subscription management info
"""
        ])
        
        return "\n\n".join(prompt_parts)
    
    @staticmethod
    def get_edit_prompt(
        current_text: str,
        edit_instruction: str,
        edit_type: str = "general"
    ) -> str:
        """Generate prompt for content editing."""
        
        edit_type_guidance = {
            "style": "Focus on adjusting the writing style, tone, and voice while maintaining the core content.",
            "tone": "Adjust the tone of the content (formal/informal, serious/light, etc.) while keeping the message intact.",
            "length": "Modify the length of the content (expand or condense) while preserving key information.",
            "structure": "Reorganize the structure and flow of the content for better readability.",
            "grammar": "Fix grammar, spelling, and punctuation errors while maintaining the original meaning.",
            "clarity": "Improve clarity and readability without changing the core message.",
            "general": "Make the requested changes while maintaining content quality and coherence."
        }
        
        guidance = edit_type_guidance.get(edit_type, edit_type_guidance["general"])
        
        prompt = f"""
Please edit the following content based on these instructions:

Edit Request: {edit_instruction}
Edit Type: {edit_type}
Guidance: {guidance}

Current Content:
{current_text}

Please provide the edited version that incorporates the requested changes while maintaining high quality and coherence.
"""
        return prompt
    
    @staticmethod
    def get_style_application_prompt(
        content_type: str,
        style_analysis: Dict[str, Any],
        base_prompt: str
    ) -> str:
        """Generate prompt with style application."""
        
        # Extract style guidance from analysis
        style_guidance_parts = []
        
        if "ai_analysis" in style_analysis:
            ai_analysis = style_analysis["ai_analysis"]
            
            if "overall_style" in ai_analysis:
                style = ai_analysis["overall_style"]
                if "tone" in style:
                    style_guidance_parts.append(f"Tone: {style['tone']}")
                if "formality" in style:
                    style_guidance_parts.append(f"Formality Level: {style['formality']}")
                if "voice" in style:
                    style_guidance_parts.append(f"Voice: {style['voice']}")
            
            if "language_characteristics" in ai_analysis:
                lang = ai_analysis["language_characteristics"]
                if "vocabulary_level" in lang:
                    style_guidance_parts.append(f"Vocabulary Level: {lang['vocabulary_level']}")
                if "sentence_structure" in lang:
                    style_guidance_parts.append(f"Sentence Structure: {lang['sentence_structure']}")
            
            if "writing_patterns" in ai_analysis:
                patterns = ai_analysis["writing_patterns"]
                if "sentence_length" in patterns:
                    style_guidance_parts.append(f"Sentence Length: {patterns['sentence_length']}")
        
        style_guidance = "\n".join(style_guidance_parts) if style_guidance_parts else "Follow the established writing style patterns."
        
        # Combine base prompt with style guidance
        enhanced_prompt = f"{base_prompt}\n\nWriting Style Guidelines:\n{style_guidance}"
        
        return enhanced_prompt
