"""
Development script for initializing content generation test data.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.core.database import get_async_session
from app.models.generated_content import GeneratedContent
from app.models.content_iteration import ContentIteration
from app.models.api_usage import APIUsage
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.models.organization import Organization


async def create_sample_organizations(db_session) -> List[Organization]:
    """Create sample organizations."""
    organizations = []
    
    # Create test organization
    org = Organization(
        name="Test Content Organization",
        slug="test-content-org",
        owner_id=uuid.uuid4(),
        subscription_plan="pro",
        subscription_status="active"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    organizations.append(org)
    
    return organizations


async def create_sample_users(db_session, organization: Organization) -> List[User]:
    """Create sample users."""
    users = []
    
    # Create test user
    user = User(
        email="content.test@example.com",
        username="contenttester",
        first_name="Content",
        last_name="Tester",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    users.append(user)
    
    return users


async def create_sample_style_profiles(db_session, organization: Organization, user: User) -> List[StyleProfile]:
    """Create sample style profiles."""
    style_profiles = []
    
    # Professional style
    professional_style = StyleProfile(
        name="Professional Business Style",
        description="Formal, authoritative writing style for business communications",
        organization_id=organization.id,
        created_by_id=user.id,
        analysis={
            "ai_analysis": {
                "overall_style": {
                    "tone": "professional and authoritative",
                    "formality": "formal",
                    "voice": "confident and knowledgeable"
                },
                "language_characteristics": {
                    "vocabulary_level": "advanced",
                    "sentence_structure": "complex",
                    "word_choice": "precise and technical"
                },
                "writing_patterns": {
                    "sentence_length": "long",
                    "punctuation_usage": "formal",
                    "transition_usage": "sophisticated"
                }
            },
            "technical_analysis": {
                "avg_sentence_length": 25.5,
                "avg_word_length": 6.2,
                "readability_score": 12.3
            }
        },
        tags=["business", "professional", "formal"],
        is_active=True
    )
    db_session.add(professional_style)
    
    # Casual style
    casual_style = StyleProfile(
        name="Casual Blog Style",
        description="Friendly, conversational writing style for blog posts",
        organization_id=organization.id,
        created_by_id=user.id,
        analysis={
            "ai_analysis": {
                "overall_style": {
                    "tone": "friendly and conversational",
                    "formality": "informal",
                    "voice": "approachable and relatable"
                },
                "language_characteristics": {
                    "vocabulary_level": "intermediate",
                    "sentence_structure": "simple",
                    "word_choice": "everyday and accessible"
                },
                "writing_patterns": {
                    "sentence_length": "short",
                    "punctuation_usage": "casual",
                    "transition_usage": "natural"
                }
            },
            "technical_analysis": {
                "avg_sentence_length": 15.2,
                "avg_word_length": 4.8,
                "readability_score": 8.1
            }
        },
        tags=["blog", "casual", "friendly"],
        is_active=True
    )
    db_session.add(casual_style)
    
    await db_session.commit()
    await db_session.refresh(professional_style)
    await db_session.refresh(casual_style)
    
    style_profiles.extend([professional_style, casual_style])
    return style_profiles


async def create_sample_content(
    db_session, 
    organization: Organization, 
    user: User, 
    style_profiles: List[StyleProfile]
) -> List[GeneratedContent]:
    """Create sample generated content."""
    content_list = []
    
    # Sample content data
    content_data = [
        {
            "title": "The Future of Artificial Intelligence in Healthcare",
            "brief": "Explore how AI is revolutionizing healthcare, from diagnostic tools to personalized treatment plans.",
            "content_type": "article",
            "generated_text": """Artificial intelligence is transforming healthcare in unprecedented ways. From diagnostic imaging to drug discovery, AI technologies are enabling healthcare professionals to provide more accurate diagnoses and personalized treatments.

The integration of AI in medical imaging has been particularly revolutionary. Machine learning algorithms can now detect anomalies in X-rays, MRIs, and CT scans with accuracy rates that often exceed human radiologists. This not only speeds up the diagnostic process but also reduces the likelihood of missed diagnoses.

Personalized medicine represents another significant advancement. AI systems can analyze vast amounts of patient data, including genetic information, medical history, and lifestyle factors, to recommend tailored treatment plans. This approach is particularly promising for cancer treatment, where AI can help identify the most effective therapies for individual patients.

However, the implementation of AI in healthcare is not without challenges. Data privacy concerns, regulatory compliance, and the need for extensive validation are significant hurdles that must be addressed. Additionally, there's a growing need for healthcare professionals to be trained in AI technologies to effectively utilize these tools.

Looking ahead, the future of AI in healthcare is bright. Emerging technologies like natural language processing for medical records, predictive analytics for disease prevention, and robotic surgery assistance are just the beginning. As these technologies mature, we can expect even more innovative applications that will continue to improve patient outcomes and healthcare efficiency.""",
            "word_count": 250,
            "character_count": 1500,
            "style_profile_id": style_profiles[0].id
        },
        {
            "title": "5 Tips for Remote Work Productivity",
            "brief": "Share practical advice for staying productive while working from home.",
            "content_type": "blog_post",
            "generated_text": """Working from home can be both a blessing and a challenge. While the flexibility is amazing, staying productive requires some intentional strategies. Here are five tips that have helped me maintain focus and efficiency while working remotely.

First, create a dedicated workspace. Even if you don't have a separate room, designate a specific area for work. This helps your brain associate that space with productivity and makes it easier to focus when you're there.

Second, establish a consistent routine. Start your day at the same time, get dressed (yes, even if you're not leaving the house), and follow a structured schedule. This creates a sense of normalcy and helps maintain work-life boundaries.

Third, take regular breaks. It's easy to get caught up in tasks and forget to step away from your computer. Set reminders to take short breaks every hour or so. A quick walk around the house or a few minutes of stretching can do wonders for your energy and focus.

Fourth, minimize distractions. Turn off notifications on your phone, close unnecessary browser tabs, and let family members know when you need uninterrupted time. Consider using noise-canceling headphones if you're in a noisy environment.

Finally, stay connected with your team. Regular check-ins, virtual coffee chats, and collaborative tools help maintain relationships and ensure you're aligned with team goals. Don't underestimate the power of human connection, even in a digital world.

Remember, remote work is a skill that takes time to master. Be patient with yourself and don't be afraid to experiment with different strategies until you find what works best for you.""",
            "word_count": 280,
            "character_count": 1700,
            "style_profile_id": style_profiles[1].id
        },
        {
            "title": "Revolutionary Smart Home Security System",
            "brief": "Create compelling marketing copy for a new AI-powered home security system.",
            "content_type": "marketing_copy",
            "generated_text": """Protect What Matters Most with AI-Powered Security

Your family's safety is priceless. That's why we've developed the most advanced smart home security system that combines cutting-edge artificial intelligence with user-friendly technology to give you peace of mind like never before.

Our revolutionary facial recognition technology instantly identifies family members and trusted visitors, sending you real-time alerts only when it matters. No more false alarms from the mail carrier or neighborhood cat – just intelligent protection that works around the clock.

Key Features:
• Advanced AI facial recognition with 99.7% accuracy
• 24/7 professional monitoring with instant response
• Mobile app with live video streaming
• Smart doorbell with two-way communication
• Motion detection with customizable zones
• Easy DIY installation in under 30 minutes

Don't wait for something to happen. Take control of your home's security today with our 30-day risk-free trial. Join over 100,000 families who trust our system to keep their loved ones safe.

Call now and get your first month FREE plus free professional installation. Limited time offer – secure your home before it's too late.""",
            "word_count": 180,
            "character_count": 1100,
            "style_profile_id": style_profiles[0].id
        }
    ]
    
    for i, data in enumerate(content_data):
        content = GeneratedContent(
            organization_id=organization.id,
            created_by_id=user.id,
            style_profile_id=data.get("style_profile_id"),
            title=data["title"],
            brief=data["brief"],
            content_type=data["content_type"],
            generated_text=data["generated_text"],
            word_count=data["word_count"],
            character_count=data["character_count"],
            input_tokens=500 + (i * 100),
            output_tokens=300 + (i * 50),
            total_tokens=800 + (i * 150),
            estimated_cost=0.02 + (i * 0.01),
            model_used="gpt-4-turbo-preview",
            generation_prompt=f"Generated content for {data['title']}",
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)
        content_list.append(content)
    
    return content_list


async def create_sample_iterations(
    db_session, 
    content_list: List[GeneratedContent], 
    user: User
) -> List[ContentIteration]:
    """Create sample content iterations."""
    iterations = []
    
    # Create iterations for the first content piece
    if content_list:
        content = content_list[0]
        
        iteration = ContentIteration(
            generated_content_id=content.id,
            edited_by_id=user.id,
            iteration_number=1,
            edit_prompt="Make the introduction more engaging and add more specific examples",
            edit_type="general",
            previous_text=content.generated_text,
            new_text=content.generated_text + "\n\nFor example, Google's DeepMind has developed AI systems that can detect over 50 eye diseases with accuracy comparable to world-leading experts.",
            previous_word_count=content.word_count,
            new_word_count=content.word_count + 25,
            word_count_change=25,
            previous_character_count=content.character_count,
            new_character_count=content.character_count + 150,
            character_count_change=150,
            diff_summary="Content expanded by 25 words with specific example",
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
            estimated_cost=0.01,
            model_used="gpt-4-turbo-preview",
            generation_prompt="Edit request for more engaging introduction",
            status="completed",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        db_session.add(iteration)
        await db_session.commit()
        await db_session.refresh(iteration)
        iterations.append(iteration)
    
    return iterations


async def create_sample_usage_data(
    db_session, 
    organization: Organization, 
    user: User
) -> List[APIUsage]:
    """Create sample API usage data."""
    usage_records = []
    
    # Create usage records for the last 30 days
    for i in range(30):
        usage_date = datetime.utcnow().date() - timedelta(days=i)
        
        # Vary the usage data
        base_tokens = 1000 + (i % 5) * 200
        base_cost = 0.02 + (i % 5) * 0.005
        
        usage = APIUsage(
            organization_id=organization.id,
            user_id=user.id,
            service_type="content_generation" if i % 3 == 0 else "content_editing",
            operation_type="generate" if i % 3 == 0 else "edit",
            input_tokens=base_tokens,
            output_tokens=base_tokens // 2,
            total_tokens=base_tokens + (base_tokens // 2),
            input_cost=base_cost * 0.6,
            output_cost=base_cost * 0.4,
            total_cost=base_cost,
            model_used="gpt-4-turbo-preview",
            input_cost_per_1k=0.01,
            output_cost_per_1k=0.03,
            success="true" if i % 10 != 0 else "false",  # 10% failure rate
            usage_date=usage_date,
            usage_hour=9 + (i % 8),  # Business hours
            response_time_ms=1500 + (i % 5) * 200,
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        db_session.add(usage)
        await db_session.commit()
        await db_session.refresh(usage)
        usage_records.append(usage)
    
    return usage_records


async def main():
    """Main function to initialize all sample data."""
    print("Initializing content generation test data...")
    
    async with get_async_session() as db_session:
        try:
            # Create organizations
            print("Creating sample organizations...")
            organizations = await create_sample_organizations(db_session)
            
            # Create users
            print("Creating sample users...")
            users = await create_sample_users(db_session, organizations[0])
            
            # Create style profiles
            print("Creating sample style profiles...")
            style_profiles = await create_sample_style_profiles(db_session, organizations[0], users[0])
            
            # Create content
            print("Creating sample content...")
            content_list = await create_sample_content(db_session, organizations[0], users[0], style_profiles)
            
            # Create iterations
            print("Creating sample iterations...")
            iterations = await create_sample_iterations(db_session, content_list, users[0])
            
            # Create usage data
            print("Creating sample usage data...")
            usage_records = await create_sample_usage_data(db_session, organizations[0], users[0])
            
            print(f"Successfully created:")
            print(f"- {len(organizations)} organizations")
            print(f"- {len(users)} users")
            print(f"- {len(style_profiles)} style profiles")
            print(f"- {len(content_list)} content pieces")
            print(f"- {len(iterations)} iterations")
            print(f"- {len(usage_records)} usage records")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            await db_session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
