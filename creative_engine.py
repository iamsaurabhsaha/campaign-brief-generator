"""
Creative Engine Module for the Campaign Brief Generator.

Generates creative concepts, creative briefs, and email sequences
from campaign briefs using the Claude API. Includes demo mode with
sample data when no API key is configured.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import llm_provider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Demo data — used when ANTHROPIC_API_KEY is not set
# ---------------------------------------------------------------------------

DEMO_CONCEPTS: list[dict[str, Any]] = [
    {
        "concept_name": "The Listing Whisperer",
        "theme": "AI that understands your products better than you do, turning a single photo into a story that sells.",
        "visual_direction": (
            "Clean, minimalist design with a warm gradient from soft white to light gold. "
            "Hero imagery shows a split-screen: a raw product photo on the left transforming "
            "into a polished, fully-written listing on the right with sparkle particle effects. "
            "Typography is modern sans-serif (Inter or similar), with the headline in bold navy "
            "and accent text in eBay blue (#0064D2)."
        ),
        "headline": "One Photo. One Click. One Perfect Listing.",
        "tagline": "Let AI do the writing. You do the selling.",
        "tone": (
            "Confident but approachable. Speaks like a knowledgeable friend who happens to be "
            "an e-commerce expert. Avoids jargon. Uses short, punchy sentences with occasional "
            "humor. Think: smart, not stiff."
        ),
        "sample_copy": (
            "You took the photo. That's it. That's your whole job.\n\n"
            "Our AI-Powered Listing Generator handles the rest — title, description, item "
            "specifics, pricing suggestions, even SEO keywords. It analyzes your image, "
            "identifies the product, and writes a listing that converts. In seconds, not hours.\n\n"
            "Over 10 million sellers already use it. The ones who don't? They're still typing "
            "descriptions at 2 AM."
        ),
        "primary_channel": "Email marketing",
        "secondary_channels": ["Social media (LinkedIn, Instagram)", "Blog/content marketing", "In-app notifications"],
        "estimated_appeal": {
            "score": 8,
            "reasoning": (
                "Strong product-benefit alignment with a relatable pain point (tedious listing creation). "
                "The split-screen visual concept is immediately understandable. The tone strikes "
                "a good balance between professional and accessible."
            ),
        },
    },
    {
        "concept_name": "Listings at the Speed of Light",
        "theme": "Speed and efficiency as a competitive superpower — because in e-commerce, time is literally money.",
        "visual_direction": (
            "Dynamic, high-energy design using motion blur and speed lines. Primary palette: "
            "deep navy background with electric blue (#0064D2) and bright yellow (#F5AF02) accents. "
            "Photography style is action-oriented — hands in motion, screens with glowing AI interfaces. "
            "Infographic elements show time savings (stopwatch graphics, before/after timelines). "
            "Bold, condensed typography for headlines."
        ),
        "headline": "5 Minutes to List What Used to Take 50",
        "tagline": "Stop listing. Start selling.",
        "tone": (
            "Urgent and energetic. Creates a sense of momentum and FOMO. Data-driven — leans on "
            "statistics and time-saved metrics. Direct address ('you') to make it personal. "
            "Short paragraphs, bold claims backed by numbers."
        ),
        "sample_copy": (
            "Every minute you spend writing a listing is a minute you're not making a sale.\n\n"
            "The AI-Powered Listing Generator cuts your listing time by 90%. Upload a photo, "
            "and in under 10 seconds you get a complete, optimized listing — title, description, "
            "category, item specifics, and a suggested price based on real market data. "
            "Sellers using the tool list 5x more inventory in the same time.\n\n"
            "Your competitors are already moving faster. The question isn't whether you can "
            "afford to use AI — it's whether you can afford not to."
        ),
        "primary_channel": "Paid social (Facebook/Instagram ads)",
        "secondary_channels": ["Search ads (Google)", "YouTube pre-roll", "Seller community forums"],
        "estimated_appeal": {
            "score": 9,
            "reasoning": (
                "Speed and efficiency are the #1 concern for high-volume sellers. The 90% time "
                "savings claim is concrete and compelling. The urgency/FOMO angle drives action. "
                "Strong fit for paid channels where you need to stop the scroll."
            ),
        },
    },
    {
        "concept_name": "Your AI Business Partner",
        "theme": "Repositioning the AI tool not as software but as a tireless team member who handles the grunt work so sellers can focus on growth.",
        "visual_direction": (
            "Warm, people-centric photography showing real sellers in their workspaces — garages, "
            "home offices, small warehouses — smiling and relaxed while screens in the background "
            "show the AI at work. Color palette is warm neutrals with eBay green (#86B817) "
            "accents suggesting growth and prosperity. Illustrations blend human and AI elements "
            "(e.g., a hand and a robot hand high-fiving). Rounded, friendly typography."
        ),
        "headline": "Meet the Team Member Who Never Sleeps",
        "tagline": "AI that works as hard as you do.",
        "tone": (
            "Warm, empathetic, and empowering. Focuses on the seller's ambition and work ethic, "
            "positioning AI as a deserved upgrade, not a replacement. Storytelling-driven — uses "
            "mini-narratives about real seller types (the side-hustler, the growing business, "
            "the established retailer). Inclusive and encouraging."
        ),
        "sample_copy": (
            "You started this business with a dream and a spare room full of inventory. "
            "You've done every job — photographer, copywriter, shipping clerk, customer service rep. "
            "But you didn't become a seller to spend your nights writing product descriptions.\n\n"
            "The AI-Powered Listing Generator is like hiring an expert copywriter who knows your "
            "products, your market, and what buyers search for — except it works 24/7 and never "
            "asks for a raise. Upload a photo, and it delivers a professional, SEO-optimized listing "
            "in seconds.\n\n"
            "You built this business. Let AI help you scale it."
        ),
        "primary_channel": "Content marketing (blog + organic social)",
        "secondary_channels": ["Email nurture sequence", "Podcast sponsorship", "Seller success stories / case studies"],
        "estimated_appeal": {
            "score": 7,
            "reasoning": (
                "Strong emotional resonance with small-to-medium sellers who identify with the "
                "'wearing every hat' narrative. The partnership framing reduces AI anxiety. "
                "Slightly lower score because emotional appeals convert slower than speed/ROI "
                "messaging in paid channels, but excellent for long-form content and nurture flows."
            ),
        },
    },
]

DEMO_CREATIVE_BRIEF: dict[str, Any] = {
    "project_name": "AI-Powered Listing Generator — Q2 Campaign",
    "objective": (
        "Drive a 25% increase in AI Listing Generator adoption among active sellers "
        "who list 10+ items/month but have not yet tried the tool, within 60 days of campaign launch."
    ),
    "target_audience": (
        "Mid-volume eBay sellers (10-100 listings/month) who currently write listings manually. "
        "They are time-poor, digitally comfortable but not tech-early-adopters, and motivated "
        "primarily by efficiency gains and revenue growth."
    ),
    "single_minded_proposition": (
        "The AI-Powered Listing Generator turns one product photo into a complete, optimized "
        "listing in seconds — so sellers spend less time writing and more time selling."
    ),
    "tone_and_manner": (
        "Confident but not arrogant. Energetic but not breathless. We speak like a smart, "
        "helpful colleague — not a corporate brand. Use 'you' and 'your' liberally. "
        "Keep sentences short. Lead with benefits, follow with proof. Humor is welcome "
        "when it comes naturally (never forced). Avoid: jargon, buzzword soup, "
        "'revolutionary/game-changing' cliches."
    ),
    "mandatories": [
        "eBay logo in approved placement (see brand guidelines v4.2)",
        "Legal disclaimer: 'Results may vary. AI-generated content should be reviewed before publishing.'",
        "Primary CTA: 'Try It Free' (links to /ai-listing-generator)",
        "Secondary CTA: 'See How It Works' (links to demo video)",
        "Accessibility: All images need alt text, minimum 4.5:1 contrast ratio",
    ],
    "deliverables": [
        {"asset": "Hero email", "specs": "600px wide, responsive HTML, < 100KB images", "word_count": "150-200 words"},
        {"asset": "Email drip sequence (5 emails)", "specs": "Responsive HTML", "word_count": "100-150 words each"},
        {"asset": "Social static (Facebook/Instagram)", "specs": "1080x1080px, 1200x628px", "word_count": "< 30 words overlay"},
        {"asset": "Social video (15s + 30s)", "specs": "1080x1080 + 9:16, MP4, < 15MB", "word_count": "N/A"},
        {"asset": "Blog post", "specs": "WordPress, SEO-optimized", "word_count": "800-1200 words"},
        {"asset": "Landing page", "specs": "Responsive web, above-fold CTA", "word_count": "300-500 words"},
        {"asset": "In-app banner", "specs": "728x90px, 300x250px", "word_count": "< 15 words"},
    ],
    "inspiration_references": [
        "Canva's 'What Will You Design Today?' campaign — clean, benefit-led, empowering tone",
        "Shopify's 'Let's Make You a Business' — warm, founder-focused storytelling",
        "Grammarly's product demos — simple before/after format showing AI value",
        "Apple's product launch pages — minimal copy, maximum clarity",
    ],
    "do_nots": [
        "Do not use 'revolutionary', 'game-changing', or 'cutting-edge' — these are overused and meaningless",
        "Do not imply AI replaces human judgment — always position as 'assists' or 'helps'",
        "Do not show competitor logos or name competitors directly",
        "Do not use stock photography of people — use real seller imagery or illustrated characters",
        "Do not make speed claims without the asterisk/disclaimer",
        "Do not use dark patterns or misleading urgency ('Only 2 spots left!')",
    ],
}

DEMO_EMAIL_SEQUENCE: list[dict[str, Any]] = [
    {
        "email_number": 1,
        "send_day": "Day 0",
        "purpose": "Introduction and awareness — let the seller know the tool exists and what it does.",
        "subject_line": {
            "primary": "You're still writing listings by hand?",
            "alternatives": [
                "There's a faster way to list on eBay",
                "What if one photo could create your whole listing?",
            ],
        },
        "preview_text": "Our AI tool turns a single photo into a complete listing in seconds.",
        "body_copy": (
            "Hi {{first_name}},\n\n"
            "We noticed you've been listing some great products lately — and writing every title, "
            "description, and item specific by hand. That takes dedication.\n\n"
            "But what if you didn't have to?\n\n"
            "**The AI-Powered Listing Generator** creates a complete, optimized listing from a single "
            "product photo. Title, description, category, item specifics, even a suggested price — "
            "all in under 10 seconds.\n\n"
            "Over 10 million sellers are already using it. Here's what they're saying:\n\n"
            "> *\"I listed my entire garage sale inventory in 20 minutes. It used to take me a full weekend.\"* "
            "— Sarah T., eBay seller since 2019\n\n"
            "**[Try It Free →]({{cta_url}})**\n\n"
            "Happy selling,\n"
            "The eBay Team"
        ),
        "cta_text": "Try It Free",
        "cta_url_placeholder": "{{ai_listing_generator_url}}",
    },
    {
        "email_number": 2,
        "send_day": "Day 3",
        "purpose": "Education — show how the tool works with a concrete example.",
        "subject_line": {
            "primary": "Watch: from photo to listing in 8 seconds",
            "alternatives": [
                "See the AI Listing Generator in action",
                "Here's exactly how it works (quick demo)",
            ],
        },
        "preview_text": "A 30-second demo that might save you 30 hours this month.",
        "body_copy": (
            "Hi {{first_name}},\n\n"
            "Curious how the AI-Powered Listing Generator actually works? Here's the short version:\n\n"
            "1. **Snap a photo** of your product\n"
            "2. **Upload it** to the listing tool\n"
            "3. **Review the AI-generated listing** — title, description, category, item specifics, "
            "and suggested price are all filled in\n"
            "4. **Edit if you want** (or don't — it's that good)\n"
            "5. **Publish** and move on to your next item\n\n"
            "The whole process takes under 10 seconds. [Watch the 30-second demo →]({{demo_video_url}})\n\n"
            "Sellers who switch to AI-assisted listings report:\n"
            "- **90% less time** spent on listing creation\n"
            "- **5x more inventory** listed per week\n"
            "- **12% higher sell-through rate** (because AI optimizes for search)\n\n"
            "**[Create Your First AI Listing →]({{cta_url}})**\n\n"
            "Happy selling,\n"
            "The eBay Team"
        ),
        "cta_text": "Create Your First AI Listing",
        "cta_url_placeholder": "{{ai_listing_generator_url}}",
    },
    {
        "email_number": 3,
        "send_day": "Day 7",
        "purpose": "Social proof — highlight seller success stories to build trust.",
        "subject_line": {
            "primary": "How Maria listed 200 items in one afternoon",
            "alternatives": [
                "Real sellers, real results with AI listings",
                "\"I wish I'd started using this sooner\"",
            ],
        },
        "preview_text": "Three sellers share how AI changed their listing workflow.",
        "body_copy": (
            "Hi {{first_name}},\n\n"
            "Don't just take our word for it. Here's what real sellers are saying about the "
            "AI-Powered Listing Generator:\n\n"
            "---\n\n"
            "**Maria R. — Vintage clothing seller, 500+ listings/month**\n"
            "> \"I used to spend 4-5 hours a day just writing descriptions. Now I photograph a batch "
            "of items, upload the photos, and the AI does the rest. I listed 200 items last Saturday "
            "afternoon and still had time for dinner.\"\n\n"
            "**James K. — Electronics reseller, side hustle**\n"
            "> \"I only have evenings and weekends to work on my eBay store. The AI listing tool "
            "basically doubled my inventory without adding any hours. My sales are up 40% this quarter.\"\n\n"
            "**Priya S. — Small business owner, handmade jewelry**\n"
            "> \"I was skeptical — how could AI describe my handmade pieces? But it actually picks up "
            "on details I might miss, like the clasp type and stone setting. I just tweak the tone "
            "to match my brand and hit publish.\"\n\n"
            "---\n\n"
            "Ready to write your own success story?\n\n"
            "**[Start Listing with AI →]({{cta_url}})**\n\n"
            "Happy selling,\n"
            "The eBay Team"
        ),
        "cta_text": "Start Listing with AI",
        "cta_url_placeholder": "{{ai_listing_generator_url}}",
    },
    {
        "email_number": 4,
        "send_day": "Day 12",
        "purpose": "Overcome objections — address common concerns about AI-generated content.",
        "subject_line": {
            "primary": "\"But will AI listings sound like... me?\"",
            "alternatives": [
                "Your top 3 questions about AI listings, answered",
                "AI listings: what sellers actually want to know",
            ],
        },
        "preview_text": "We answer the most common questions about AI-generated listings.",
        "body_copy": (
            "Hi {{first_name}},\n\n"
            "We hear you — handing your listings over to AI feels like a big step. "
            "Here are the questions sellers ask most:\n\n"
            "**Q: Will my listings sound generic?**\n"
            "A: The AI analyzes your specific product photo and generates unique content tailored to "
            "what it sees. No templates, no cookie-cutter descriptions. And you can always edit "
            "the output to add your personal touch.\n\n"
            "**Q: What if the AI gets something wrong?**\n"
            "A: You always have the final say. The AI generates a draft — you review, edit, and "
            "approve before anything goes live. Think of it as a first draft from a very fast assistant.\n\n"
            "**Q: Does it work for [my category]?**\n"
            "A: The AI has been trained across all major eBay categories — electronics, fashion, "
            "collectibles, home goods, auto parts, and more. It recognizes thousands of product types "
            "and adapts its descriptions accordingly.\n\n"
            "**Q: Is it really free?**\n"
            "A: Yes. The AI-Powered Listing Generator is included for all eBay sellers at no extra cost.\n\n"
            "Still have questions? [Visit our FAQ →]({{faq_url}})\n\n"
            "Or just try it — the best way to see is to do:\n\n"
            "**[Try It Now →]({{cta_url}})**\n\n"
            "Happy selling,\n"
            "The eBay Team"
        ),
        "cta_text": "Try It Now",
        "cta_url_placeholder": "{{ai_listing_generator_url}}",
    },
    {
        "email_number": 5,
        "send_day": "Day 18",
        "purpose": "Final nudge — create gentle urgency and restate the core value proposition.",
        "subject_line": {
            "primary": "Your competitors listed 47 items while you read this subject line",
            "alternatives": [
                "Still on the fence? Here's what you're missing",
                "The sellers who list fastest, sell most",
            ],
        },
        "preview_text": "One photo. Ten seconds. A complete listing. What are you waiting for?",
        "body_copy": (
            "Hi {{first_name}},\n\n"
            "Let's do some quick math.\n\n"
            "If you list 20 items a week and each listing takes 15 minutes to write manually, "
            "that's **5 hours a week** spent on listing creation alone. Over a year, that's "
            "**260 hours** — more than six full work weeks.\n\n"
            "With the AI-Powered Listing Generator, those same 20 listings take about **15 minutes total**.\n\n"
            "That's 250+ hours back. Hours you could spend sourcing better inventory, optimizing "
            "pricing, improving customer service, or — radical idea — taking a day off.\n\n"
            "Here's all it takes to start:\n\n"
            "1. Go to your listing tool\n"
            "2. Upload a product photo\n"
            "3. Let AI generate the listing\n"
            "4. Review and publish\n\n"
            "That's it. No setup, no subscription, no learning curve.\n\n"
            "**[Create Your First AI Listing →]({{cta_url}})**\n\n"
            "Happy selling,\n"
            "The eBay Team\n\n"
            "*P.S. — Over 10 million sellers have already made the switch. "
            "[See their stories →]({{success_stories_url}})*"
        ),
        "cta_text": "Create Your First AI Listing",
        "cta_url_placeholder": "{{ai_listing_generator_url}}",
    },
]


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

CREATIVE_CONCEPTS_SYSTEM_PROMPT = """You are an award-winning creative director at a top advertising agency.
You specialize in technology and e-commerce marketing campaigns.

Given a campaign brief, generate creative concepts that are:
- Strategically sound (tied to the brief's objectives and audience)
- Creatively distinctive (not generic or predictable)
- Practically executable (can be produced within typical marketing budgets)
- Channel-appropriate (optimized for the recommended channels)

Return ONLY valid JSON — an array of concept objects. Each object must have exactly these fields:
- "concept_name": string — a memorable, creative name for the concept
- "theme": string — the overarching theme in one sentence
- "visual_direction": string — detailed description of visual style, colors, imagery, photography/illustration style
- "headline": string — the primary headline
- "tagline": string — a short, memorable tagline
- "tone": string — detailed description of the tone of voice
- "sample_copy": string — 2-3 paragraphs of sample ad or email copy
- "primary_channel": string — the single channel this concept works best for
- "secondary_channels": array of strings — other channels it can adapt to
- "estimated_appeal": object with "score" (integer 1-10) and "reasoning" (string explaining the score)
"""

CREATIVE_BRIEF_SYSTEM_PROMPT = """You are a senior creative strategist who writes creative briefs for design and agency teams.

A creative brief is the execution document that translates a campaign brief (the strategic "what and why")
into actionable guidance for designers, copywriters, and agencies (the "how").

Given a campaign brief, generate a creative brief as a single JSON object with exactly these fields:
- "project_name": string
- "objective": string — what the creative should achieve (specific, measurable)
- "target_audience": string — simplified audience description for the creative team
- "single_minded_proposition": string — the ONE key message the creative must communicate
- "tone_and_manner": string — detailed tone guidance (voice, style, feel)
- "mandatories": array of strings — must-include elements (logos, disclaimers, CTAs, legal)
- "deliverables": array of objects, each with "asset" (string), "specs" (string), "word_count" (string)
- "inspiration_references": array of strings — suggested style/campaign references for inspiration
- "do_nots": array of strings — things to explicitly avoid
"""

EMAIL_SEQUENCE_SYSTEM_PROMPT = """You are an expert email marketing strategist who creates high-converting drip campaigns.

Given a campaign brief, generate an email drip sequence. Each email should build on the previous one,
following a classic nurture arc: Awareness -> Education -> Social Proof -> Objection Handling -> Conversion.

Return ONLY valid JSON — an array of email objects. Each object must have exactly these fields:
- "email_number": integer (1-based)
- "send_day": string (e.g., "Day 0", "Day 3", "Day 7")
- "purpose": string — what this email achieves in the nurture journey
- "subject_line": object with "primary" (string) and "alternatives" (array of 2 strings)
- "preview_text": string — the preview/preheader text
- "body_copy": string — full email body in markdown format (use {{first_name}} for personalization)
- "cta_text": string — call-to-action button text
- "cta_url_placeholder": string — placeholder URL for the CTA (e.g., "{{landing_page_url}}")
"""


# ---------------------------------------------------------------------------
# Helper: parse JSON from Claude responses
# ---------------------------------------------------------------------------

def _parse_json_response(raw_text: str) -> Any:
    """Parse JSON from a Claude response, stripping markdown fences if present.

    Args:
        raw_text: The raw response text from Claude.

    Returns:
        Parsed JSON as a Python object (dict or list).

    Raises:
        json.JSONDecodeError: If the text cannot be parsed as JSON.
    """
    text = raw_text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)

    return json.loads(text)


# ---------------------------------------------------------------------------
# Helper: format brief dict as a prompt string
# ---------------------------------------------------------------------------

def _brief_to_prompt_text(brief: dict[str, Any]) -> str:
    """Convert a campaign brief dict into a readable prompt string.

    Args:
        brief: A campaign brief dictionary.

    Returns:
        A formatted string representation of the brief.
    """
    sections: list[str] = []
    for key, value in brief.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            items = "\n".join(f"  - {item}" for item in value)
            sections.append(f"{label}:\n{items}")
        elif isinstance(value, dict):
            items = "\n".join(f"  {k}: {v}" for k, v in value.items())
            sections.append(f"{label}:\n{items}")
        else:
            sections.append(f"{label}: {value}")
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# CreativeEngine class
# ---------------------------------------------------------------------------

class CreativeEngine:
    """Generates creative concepts, creative briefs, and email sequences from campaign briefs."""

    def __init__(self) -> None:
        """Initialize the LLM provider.

        If the LLM provider is not configured, the engine runs in demo mode
        and returns sample data instead of making API calls.
        """
        self.demo_mode: bool = not llm_provider.is_configured()

        if self.demo_mode:
            logger.info("CreativeEngine initialized in DEMO mode (LLM provider not configured)")
        else:
            logger.info("CreativeEngine initialized with %s", llm_provider.provider_display_name())

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def generate_concepts(self, brief: dict[str, Any], num_concepts: int = 3) -> list[dict[str, Any]]:
        """Generate creative concepts from a campaign brief.

        Args:
            brief: A campaign brief dictionary with keys like campaign_name,
                   objective, target_audience, key_messages, etc.
            num_concepts: Number of concepts to generate (default 3).

        Returns:
            A list of concept dicts, each containing concept_name, theme,
            visual_direction, headline, tagline, tone, sample_copy,
            primary_channel, secondary_channels, and estimated_appeal.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning %d sample concepts", num_concepts)
            return DEMO_CONCEPTS[:num_concepts]

        brief_text = _brief_to_prompt_text(brief)
        user_prompt = (
            f"Campaign Brief:\n\n{brief_text}\n\n"
            f"Generate exactly {num_concepts} creative concepts for this campaign. "
            f"Return them as a JSON array."
        )

        logger.info("Generating %d creative concepts via Claude API", num_concepts)

        raw_text = llm_provider.generate(
            system=CREATIVE_CONCEPTS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4096,
        )
        try:
            concepts = _parse_json_response(raw_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse concepts JSON: %s", raw_text[:500])
            raise

        logger.info("Generated %d creative concepts", len(concepts))
        return concepts

    def generate_creative_brief(self, campaign_brief: dict[str, Any]) -> dict[str, Any]:
        """Generate a creative brief (execution doc) from a campaign brief.

        The creative brief translates strategic direction into actionable
        guidance for designers, copywriters, and agencies.

        Args:
            campaign_brief: A campaign brief dictionary.

        Returns:
            A creative brief dict with project_name, objective,
            target_audience, single_minded_proposition, tone_and_manner,
            mandatories, deliverables, inspiration_references, and do_nots.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning sample creative brief")
            return DEMO_CREATIVE_BRIEF

        brief_text = _brief_to_prompt_text(campaign_brief)
        user_prompt = (
            f"Campaign Brief:\n\n{brief_text}\n\n"
            "Generate a creative brief for the design/agency team based on this campaign brief. "
            "Return it as a single JSON object."
        )

        logger.info("Generating creative brief via Claude API")

        raw_text = llm_provider.generate(
            system=CREATIVE_BRIEF_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=3072,
        )
        try:
            creative_brief = _parse_json_response(raw_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse creative brief JSON: %s", raw_text[:500])
            raise

        logger.info("Creative brief generated: %s", creative_brief.get("project_name", "N/A"))
        return creative_brief

    def generate_email_sequence(self, brief: dict[str, Any], num_emails: int = 5) -> list[dict[str, Any]]:
        """Generate an email drip campaign sequence from a campaign brief.

        Args:
            brief: A campaign brief dictionary.
            num_emails: Number of emails in the sequence (default 5).

        Returns:
            A list of email dicts, each containing email_number, send_day,
            purpose, subject_line (with primary and alternatives),
            preview_text, body_copy, cta_text, and cta_url_placeholder.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning %d sample emails", num_emails)
            return DEMO_EMAIL_SEQUENCE[:num_emails]

        brief_text = _brief_to_prompt_text(brief)
        user_prompt = (
            f"Campaign Brief:\n\n{brief_text}\n\n"
            f"Generate a {num_emails}-email drip campaign sequence for this campaign. "
            f"Space the emails naturally (e.g., Day 0, Day 3, Day 7, Day 12, Day 18). "
            f"Return them as a JSON array."
        )

        logger.info("Generating %d-email sequence via Claude API", num_emails)

        raw_text = llm_provider.generate(
            system=EMAIL_SEQUENCE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=6144,
        )
        try:
            emails = _parse_json_response(raw_text)
        except json.JSONDecodeError:
            logger.error("Failed to parse email sequence JSON: %s", raw_text[:500])
            raise

        logger.info("Generated %d-email sequence", len(emails))
        return emails

    def render_concept_markdown(self, concept: dict[str, Any]) -> str:
        """Render a single creative concept as formatted markdown.

        Args:
            concept: A concept dict as returned by generate_concepts().

        Returns:
            A markdown-formatted string suitable for display in Streamlit.
        """
        appeal = concept.get("estimated_appeal", {})
        if isinstance(appeal, dict):
            score = appeal.get("score", "N/A")
            reasoning = appeal.get("reasoning", "")
        else:
            score = appeal
            reasoning = ""

        secondary = concept.get("secondary_channels", [])
        if isinstance(secondary, list):
            secondary_str = ", ".join(secondary)
        else:
            secondary_str = str(secondary)

        lines: list[str] = [
            f"# {concept.get('concept_name', 'Untitled Concept')}",
            "",
            f"**Theme:** {concept.get('theme', 'N/A')}",
            "",
            "---",
            "",
            "## Headline & Tagline",
            f"### \"{concept.get('headline', '')}\"",
            f"*{concept.get('tagline', '')}*",
            "",
            "---",
            "",
            "## Visual Direction",
            concept.get("visual_direction", "N/A"),
            "",
            "## Tone of Voice",
            concept.get("tone", "N/A"),
            "",
            "---",
            "",
            "## Sample Copy",
            concept.get("sample_copy", "N/A"),
            "",
            "---",
            "",
            "## Channel Strategy",
            f"**Primary Channel:** {concept.get('primary_channel', 'N/A')}",
            f"**Secondary Channels:** {secondary_str}",
            "",
            "---",
            "",
            "## Estimated Appeal",
            f"**Score:** {score}/10",
            "",
        ]

        if reasoning:
            lines.append(f"**Reasoning:** {reasoning}")
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    engine = CreativeEngine()

    # Sample campaign brief for testing
    sample_brief: dict[str, Any] = {
        "campaign_name": "AI-Powered Listing Generator Launch",
        "objective": "Drive 25% increase in AI listing tool adoption among mid-volume sellers within 60 days.",
        "target_audience": (
            "Mid-volume eBay sellers (10-100 listings/month) who currently write listings manually. "
            "Time-poor, digitally comfortable, motivated by efficiency and revenue growth."
        ),
        "key_insight": "Sellers didn't start a business to spend their nights writing product descriptions.",
        "positioning_statement": (
            "The AI-Powered Listing Generator turns one product photo into a complete, optimized "
            "listing in seconds — so sellers spend less time writing and more time selling."
        ),
        "key_messages": [
            "One photo creates a complete listing in under 10 seconds",
            "AI optimizes titles and descriptions for search visibility",
            "Over 10 million sellers already use it",
            "Always free, no subscription required",
        ],
        "channels": ["Email", "Social media", "Blog/content", "In-app notifications"],
        "budget": "$50,000",
        "timeline": "Q2 2026 (April-June)",
    }

    # --- Test 1: Generate concepts ---
    print("\n" + "=" * 70)
    print("CREATIVE CONCEPTS")
    print("=" * 70)

    concepts = engine.generate_concepts(sample_brief, num_concepts=3)
    for i, concept in enumerate(concepts, 1):
        print(f"\n--- Concept {i} ---")
        md = engine.render_concept_markdown(concept)
        print(md)

    # --- Test 2: Generate creative brief ---
    print("\n" + "=" * 70)
    print("CREATIVE BRIEF")
    print("=" * 70)

    creative_brief = engine.generate_creative_brief(sample_brief)
    print(json.dumps(creative_brief, indent=2))

    # --- Test 3: Generate email sequence ---
    print("\n" + "=" * 70)
    print("EMAIL SEQUENCE")
    print("=" * 70)

    emails = engine.generate_email_sequence(sample_brief, num_emails=5)
    for email in emails:
        subj = email.get("subject_line", {})
        if isinstance(subj, dict):
            subject = subj.get("primary", "N/A")
        else:
            subject = str(subj)
        print(f"\nEmail {email.get('email_number', '?')} ({email.get('send_day', '?')}): {subject}")
        print(f"  Purpose: {email.get('purpose', 'N/A')}")
        print(f"  CTA: {email.get('cta_text', 'N/A')}")

    print(f"\nMode: {'DEMO' if engine.demo_mode else 'LIVE'}")
    print("All tests passed.")
