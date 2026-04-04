"""
Campaign Brief Generator — Core Module

AI-powered campaign brief generation using the Anthropic Claude API.
Generates professional 14-section campaign briefs section by section,
following industry best practices from HubSpot, Asana, Product Marketing
Alliance, BetterBriefs, and real-world examples (Apple, McDonald's, Barbie).

Classes:
    BriefGenerator  — Claude API integration for brief generation.
    BriefStore      — JSON-based persistence for briefs.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — establishes the AI persona and brief framework
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior Product Marketing Manager (PMM) with 15+ years of \
experience crafting award-winning campaign briefs for Fortune 500 companies and \
high-growth tech startups. You have deep expertise in the 14-section campaign brief \
framework used by Apple, Google, HubSpot, and other top marketing organizations.

Your briefs are:
- Strategically rigorous yet concise (fit on 1-2 pages)
- Actionable — any marketing team can execute from your brief alone
- Audience-obsessed — every section ties back to the target human
- Insight-driven — rooted in a genuine human truth, not just data
- Measurable — every objective has SMART criteria

The 14-section campaign brief framework:
1. Campaign Name — memorable, internal-facing
2. Background/Context — the "why now" with market triggers
3. Objective — SMART-formatted (Specific, Measurable, Achievable, Relevant, Time-bound)
4. Target Audience — demographics, psychographics, pain points, motivations
5. Key Insight — the human truth that drives the campaign
6. Positioning Statement — short (25 words) and detailed (100 words)
7. Key Messages — 3-5 ranked by priority
8. Single-Minded Proposition (SMP) — the ONE thing (fails if it says two things)
9. Channel Plan — channel, tactic, rationale, budget allocation
10. Content Deliverables — assets with specs (dimensions, format, quantity)
11. Success Metrics/KPIs — measurable targets with measurement method
12. Timeline — phased (Awareness, Launch, Sustain, Optimize)
13. Budget Breakdown — allocation across channels
14. Approvals/RACI — who decides what

Launch tier classification (Product Marketing Alliance):
- Tier 0: Company-defining (new platform) — full brief + war room
- Tier 1: Major feature launch — full brief
- Tier 2: Feature enhancement — light brief
- Tier 3: Bug fix / minor update — no brief needed

Top mistakes to catch:
1. Too long (>2 pages)
2. Multiple objectives (should be ONE primary)
3. Vague audience ("everyone")
4. No insight (just data, no human truth)
5. "And/also" in the SMP (not single-minded)
6. No success metrics
7. No competitive context
8. Skipping the "why now"
9. Brief changes after kickoff without sign-off

Always return valid JSON. Never include markdown code fences or extra text outside the JSON."""

import llm_provider

# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------


def _parse_json_response(raw_text: str) -> Any:
    """Strip markdown code fences and parse JSON from a Claude response.

    Attempts multiple strategies: direct parse, code-fence stripping,
    and brace extraction.

    Args:
        raw_text: Raw text from the Claude API response.

    Returns:
        Parsed JSON as a Python object.

    Raises:
        json.JSONDecodeError: If all parsing strategies fail.
    """
    text = raw_text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip code fences
    for fence in ("```json", "```"):
        if fence in text:
            try:
                start = text.index(fence) + len(fence)
                end = text.index("```", start)
                return json.loads(text[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

    # Strategy 3: extract first { ... } or [ ... ] block
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        first = text.find(open_ch)
        last = text.rfind(close_ch)
        if first != -1 and last != -1 and last > first:
            try:
                return json.loads(text[first : last + 1])
            except json.JSONDecodeError:
                pass

    logger.error("All JSON parsing strategies failed for: %s", text[:300])
    raise json.JSONDecodeError("Could not extract JSON from response", text, 0)


# ---------------------------------------------------------------------------
# Demo / sample data
# ---------------------------------------------------------------------------


def _demo_full_brief(campaign_name: str, launch_tier: str) -> dict[str, Any]:
    """Return a realistic sample brief for demo mode."""
    return {
        "campaign_name": campaign_name or "AI Listing Magic",
        "launch_tier": launch_tier or "Tier 1",
        "background_context": (
            "Online sellers spend an average of 15 minutes per listing, with professional "
            "sellers managing 500+ active listings. Recent competitor launches (Mercari AI "
            "Listings, Amazon AI Descriptions) have raised the bar. Our AI-Powered Listing "
            "Generator reduces listing time by 80%, and we need to capture mindshare before "
            "competitors establish dominance in this space."
        ),
        "objective_smart": (
            "Increase AI-Powered Listing Generator adoption among professional sellers "
            "(50+ listings/month) by 30% within 90 days of launch (Q2 2026), measured "
            "by unique active users in Seller Hub analytics."
        ),
        "target_audience": {
            "demographics": "Professional sellers aged 28-55, SMB owners, 60% US-based",
            "psychographics": "Efficiency-obsessed, early tech adopters, value time over cost",
            "pain_points": [
                "Listing creation is tedious and repetitive",
                "Photo editing takes too long",
                "Descriptions don't convert well",
                "Hard to scale beyond current volume",
            ],
            "motivations": [
                "Grow their business faster",
                "Spend less time on admin, more on sourcing",
                "Look professional without hiring help",
            ],
            "media_habits": [
                "YouTube tutorials", "Seller forums", "Email newsletters",
                "Instagram/TikTok for trends",
            ],
            "objections": [
                "AI won't understand my niche products",
                "I've tried AI tools before and they were generic",
                "Will it change my brand voice?",
            ],
        },
        "key_insight": (
            "Professional sellers don't want to be content creators — they want to be "
            "business owners. Every minute spent writing listings is a minute not spent "
            "finding inventory and growing their business."
        ),
        "positioning_short": (
            "AI-Powered Listing Generator turns a single photo into a complete, "
            "optimized listing in seconds — so sellers can focus on growing their business."
        ),
        "positioning_detailed": (
            "For professional online sellers who struggle with the time-consuming process "
            "of creating compelling product listings, our AI-Powered Listing Generator "
            "automatically creates complete, SEO-optimized listings from a single product "
            "photo. Unlike manual listing tools or basic templates, our AI understands "
            "product categories, buyer search behavior, and conversion best practices "
            "to generate listings that sell — reducing creation time by 80% while "
            "improving listing quality scores by 25%."
        ),
        "key_messages": [
            "One photo. One click. One complete listing — ready to sell.",
            "Spend 80% less time listing, and redirect that time to growing your business.",
            "AI that understands your products as well as you do — trained on millions of successful listings.",
            "Professional-quality listings without the professional price tag.",
            "Join 10,000+ sellers who've already transformed their listing workflow.",
        ],
        "single_minded_proposition": {
            "smp": "List faster, sell more.",
            "quality_check": "pass",
            "quality_reason": "Single-focused on the speed-to-sales benefit without trying to communicate multiple ideas.",
        },
        "channel_plan": [
            {"channel": "Email", "tactic": "Segmented drip campaign to sellers with 50+ listings", "rationale": "Highest ROI channel for existing seller base", "budget_pct": 25},
            {"channel": "In-App", "tactic": "Seller Hub banner + contextual tooltip on listing page", "rationale": "Catches sellers at the moment of need", "budget_pct": 10},
            {"channel": "Social Media", "tactic": "Before/after listing demos on TikTok and Instagram Reels", "rationale": "Visual proof of speed and quality drives sharing", "budget_pct": 20},
            {"channel": "Blog", "tactic": "SEO-optimized how-to guides and seller success stories", "rationale": "Long-tail organic traffic from seller search queries", "budget_pct": 10},
            {"channel": "Video", "tactic": "YouTube tutorial series: '60-Second Listings'", "rationale": "Sellers prefer video tutorials for tool adoption", "budget_pct": 15},
            {"channel": "Paid Search", "tactic": "Google Ads targeting 'AI listing tools' and 'sell faster online'", "rationale": "Capture high-intent competitor-research traffic", "budget_pct": 15},
            {"channel": "PR", "tactic": "Tech press embargo + seller community influencer outreach", "rationale": "Third-party credibility drives trust with skeptical sellers", "budget_pct": 5},
        ],
        "content_deliverables": [
            {"asset": "Launch Email Sequence", "specs": "3-email drip, responsive HTML", "quantity": 3},
            {"asset": "Seller Hub Banner", "specs": "1200x300px, desktop + mobile variants", "quantity": 2},
            {"asset": "Social Media Videos", "specs": "9:16, 15-30 seconds, subtitled", "quantity": 6},
            {"asset": "Blog Posts", "specs": "1000-1500 words, SEO-optimized", "quantity": 4},
            {"asset": "YouTube Tutorial", "specs": "3-5 minutes, screen recording + talking head", "quantity": 2},
            {"asset": "Press Release", "specs": "AP style, 500 words", "quantity": 1},
            {"asset": "Landing Page", "specs": "Responsive, A/B test ready, with demo video", "quantity": 1},
        ],
        "success_metrics": [
            {"kpi": "Feature Adoption Rate", "target": "+30% unique active users", "measurement": "Seller Hub analytics"},
            {"kpi": "Listing Creation Time", "target": "-80% avg time per listing", "measurement": "Product analytics"},
            {"kpi": "Email CTR", "target": ">4.5%", "measurement": "Email platform"},
            {"kpi": "Video Views", "target": "500K total views in 90 days", "measurement": "YouTube + social analytics"},
            {"kpi": "Organic Search Traffic", "target": "+40% to listing tool pages", "measurement": "Google Analytics"},
            {"kpi": "NPS from users", "target": ">50", "measurement": "In-app survey"},
        ],
        "timeline": [
            {"phase": "Awareness", "dates": "Weeks 1-2", "actions": ["Press embargo + PR outreach", "Teaser emails to top sellers", "Social media countdown posts"]},
            {"phase": "Launch", "dates": "Weeks 3-4", "actions": ["Full email drip activation", "In-app banners go live", "YouTube tutorial series premiere", "Blog posts publish"]},
            {"phase": "Sustain", "dates": "Weeks 5-8", "actions": ["Paid search campaigns ramp up", "User success story content", "Community forum engagement", "Retargeting ads"]},
            {"phase": "Optimize", "dates": "Weeks 9-12", "actions": ["A/B test top-performing channels", "Scale winning creatives", "KPI review and report", "Plan phase 2 features"]},
        ],
        "budget_breakdown": {
            "Email": 18750,
            "In-App": 7500,
            "Social Media": 15000,
            "Blog/Content": 7500,
            "Video Production": 11250,
            "Paid Search": 11250,
            "PR": 3750,
        },
        "raci_matrix": {
            "PMM": "Accountable — owns the brief, messaging, and campaign strategy",
            "Product": "Consulted — feature details, roadmap alignment, beta feedback",
            "Engineering": "Informed — launch readiness, known issues, capacity constraints",
            "Design": "Responsible — creative assets, landing page, email templates",
            "Sales": "Consulted — seller objections, enablement needs, field feedback",
            "Support": "Informed — FAQ preparation, ticket deflection plan, training",
            "Legal": "Consulted — claims review, compliance, terms of service updates",
            "Exec": "Informed — launch status, KPI dashboard, escalations only",
        },
        "approvals_needed": [
            {"stakeholder": "VP of Marketing", "approves": "Campaign strategy, budget, and timeline"},
            {"stakeholder": "Product Lead", "approves": "Feature claims, positioning accuracy"},
            {"stakeholder": "Legal", "approves": "Marketing claims, promotions compliance"},
            {"stakeholder": "Brand", "approves": "Creative assets, tone, visual identity"},
            {"stakeholder": "Finance", "approves": "Budget allocation and spend authorization"},
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _demo_campaign_names() -> list[str]:
    """Return sample campaign name suggestions for demo mode."""
    return [
        "List Like Magic",
        "The 60-Second Listing",
        "Snap. List. Sell.",
        "Listing Unleashed",
        "SmartList AI Launch",
    ]


def _demo_audience_profile() -> dict[str, Any]:
    """Return a sample audience profile for demo mode."""
    return {
        "demographics": "Professional online sellers aged 28-55, 60% male, primarily US-based, managing 50-500+ SKUs",
        "psychographics": "Efficiency-driven, tech-curious, growth-minded. Values tools that save time and scale output. Skeptical of hype but open to proven solutions.",
        "pain_points": [
            "Listing creation is the most time-consuming part of their workflow",
            "Writing compelling descriptions is not their strength",
            "Photo editing requires skills they lack or software they can't afford",
            "Scaling beyond current volume feels impossible without hiring",
        ],
        "motivations": [
            "Grow revenue without growing headcount",
            "Spend more time sourcing and less time on admin",
            "Look as professional as large retailers",
            "Stay competitive as AI tools reshape e-commerce",
        ],
        "media_habits": [
            "YouTube (tutorials, reviews)",
            "Reddit (r/Flipping, r/eBaySellers)",
            "Email newsletters (eCommerceFuel, Seller Updates)",
            "Facebook Groups (seller communities)",
            "TikTok (trending product research)",
        ],
        "objections": [
            "AI-generated content feels generic and won't match my brand",
            "I've tried listing tools before and they never work for my niche",
            "What if the AI makes errors that hurt my seller metrics?",
            "I don't want to depend on a tool that could change or get expensive",
        ],
    }


def _demo_smp() -> dict[str, str]:
    """Return a sample SMP result for demo mode."""
    return {
        "smp": "List faster, sell more.",
        "quality_check": "pass",
        "quality_reason": "Communicates a single benefit chain (speed leads to sales) without 'and/also' or dual propositions.",
    }


def _demo_channel_plan() -> list[dict[str, Any]]:
    """Return a sample channel plan for demo mode."""
    return [
        {"channel": "Email", "tactic": "3-part drip campaign to professional sellers", "rationale": "Highest ROI for existing user base", "budget_pct": 25},
        {"channel": "In-App", "tactic": "Seller Hub banner and listing page tooltip", "rationale": "Reaches sellers at the point of need", "budget_pct": 10},
        {"channel": "Social Media", "tactic": "Short-form video demos on TikTok and Instagram", "rationale": "Visual proof of speed and quality", "budget_pct": 20},
        {"channel": "Blog", "tactic": "SEO how-to guides and success stories", "rationale": "Captures organic search traffic", "budget_pct": 10},
        {"channel": "Video", "tactic": "YouTube tutorial: 60-Second Listings", "rationale": "Sellers prefer video for tool learning", "budget_pct": 15},
        {"channel": "Paid Search", "tactic": "Google Ads on 'AI listing tool' keywords", "rationale": "Captures high-intent traffic", "budget_pct": 15},
        {"channel": "PR", "tactic": "Press embargo and influencer outreach", "rationale": "Third-party credibility", "budget_pct": 5},
    ]


def _demo_raci_matrix() -> dict[str, str]:
    """Return a sample RACI matrix for demo mode."""
    return {
        "PMM": "Accountable — owns campaign strategy, messaging, brief",
        "Product": "Consulted — feature details, roadmap, beta feedback",
        "Engineering": "Informed — launch readiness, known issues, capacity",
        "Design": "Responsible — creative assets, landing pages, templates",
        "Sales": "Consulted — seller objections, enablement, field feedback",
        "Support": "Informed — FAQ prep, ticket deflection, agent training",
        "Legal": "Consulted — claims review, compliance, terms",
        "Exec": "Informed — launch status, KPI dashboard, escalations",
    }


def _demo_launch_tier() -> dict[str, str]:
    """Return a sample launch tier classification for demo mode."""
    return {
        "tier": "Tier 1",
        "reasoning": "This is a major new AI-powered feature that changes the core listing workflow for sellers. It has competitive implications and affects a large portion of the seller base, warranting a full campaign brief and cross-functional launch coordination.",
        "brief_depth": "Full 14-section brief with detailed channel plan, RACI matrix, and phased timeline.",
    }


# ---------------------------------------------------------------------------
# BriefGenerator class
# ---------------------------------------------------------------------------


class BriefGenerator:
    """Generates campaign briefs using the Anthropic Claude API.

    Supports full brief generation and individual section generation.
    Falls back to demo data when no API key is configured.
    """

    def __init__(self) -> None:
        """Initialize the LLM provider and set demo mode if not configured."""
        self.demo_mode: bool = not llm_provider.is_configured()

        if self.demo_mode:
            logger.warning(
                "LLM provider not configured. Running in DEMO MODE with sample data."
            )
        else:
            logger.info("BriefGenerator initialized with %s", llm_provider.provider_display_name())

        self.system_prompt: str = SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rate_limit(self):
        """Simple rate limiter."""
        import time
        time.sleep(0.5)

    def _call_claude(self, user_prompt: str, max_tokens: int = 4096) -> dict[str, Any]:
        """Send a prompt to the configured LLM and return parsed JSON.

        Args:
            user_prompt: The user message to send.
            max_tokens: Maximum tokens in the response.

        Returns:
            Parsed JSON response as a Python dict or list.

        Raises:
            json.JSONDecodeError: If response cannot be parsed.
        """
        logger.info("Calling LLM API (%d max tokens)...", max_tokens)

        raw_text = llm_provider.generate(
            system=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

        raw_text = raw_text.strip()
        logger.debug("Raw API response length: %d chars", len(raw_text))

        result = _parse_json_response(raw_text)
        return result

    # ------------------------------------------------------------------
    # 1. generate_full_brief
    # ------------------------------------------------------------------

    def generate_full_brief(
        self,
        campaign_name: str,
        background: str,
        objective: str,
        target_audience: str,
        feature_description: str,
        launch_tier: str = "Tier 1",
        budget: Optional[float] = None,
    ) -> dict[str, Any]:
        """Generate a complete 14-section campaign brief.

        Args:
            campaign_name: Working name for the campaign.
            background: Context and market situation (the "why now").
            objective: What the campaign aims to achieve.
            target_audience: Description of the target audience.
            feature_description: The product/feature being marketed.
            launch_tier: Tier 0-3 classification (default Tier 1).
            budget: Optional total budget in dollars.

        Returns:
            Dict containing all 14 sections of the campaign brief.
        """
        if self.demo_mode:
            logger.info("DEMO MODE: Returning sample full brief")
            return _demo_full_brief(campaign_name, launch_tier)

        budget_instruction = ""
        if budget:
            budget_instruction = f"Total budget: ${budget:,.0f}. Allocate across channels with specific dollar amounts."
        else:
            budget_instruction = "No specific budget provided. Provide percentage-based allocation recommendations."

        user_prompt = f"""Generate a complete 14-section campaign brief as JSON.

INPUTS:
- Campaign Name: {campaign_name}
- Launch Tier: {launch_tier}
- Background/Context: {background}
- Objective: {objective}
- Target Audience: {target_audience}
- Feature/Product: {feature_description}
- {budget_instruction}

Return a JSON object with exactly these keys:
- "campaign_name": string
- "launch_tier": string
- "background_context": string (the "why now" with market triggers, 2-3 sentences)
- "objective_smart": string (reformat the objective as SMART)
- "target_audience": object with keys "demographics", "psychographics", "pain_points" (list), "motivations" (list), "media_habits" (list), "objections" (list)
- "key_insight": string (the human truth, not just data)
- "positioning_short": string (25 words max)
- "positioning_detailed": string (100 words max)
- "key_messages": list of 3-5 strings, ranked by priority
- "single_minded_proposition": object with "smp" (string), "quality_check" ("pass"/"fail"), "quality_reason" (string)
- "channel_plan": list of objects with "channel", "tactic", "rationale", "budget_pct"
- "content_deliverables": list of objects with "asset", "specs", "quantity"
- "success_metrics": list of objects with "kpi", "target", "measurement"
- "timeline": list of objects with "phase" (Awareness/Launch/Sustain/Optimize), "dates", "actions" (list)
- "budget_breakdown": object mapping channel name to dollar amount (or null if no budget)
- "raci_matrix": object mapping role to responsibility description (PMM, Product, Engineering, Design, Sales, Support, Legal, Exec)
- "approvals_needed": list of objects with "stakeholder" and "approves"

The SMP must be single-minded. If it contains "and", "also", "plus", or communicates two distinct benefits, mark quality_check as "fail"."""

        logger.info("Generating full brief for campaign: %s", campaign_name)
        brief = self._call_claude(user_prompt, max_tokens=6000)

        # Attach metadata
        brief["generated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("Full brief generated for: %s", brief.get("campaign_name"))
        return brief

    # ------------------------------------------------------------------
    # 2. make_objective_smart
    # ------------------------------------------------------------------

    def make_objective_smart(self, raw_objective: str) -> str:
        """Reformat a vague objective into SMART format.

        Args:
            raw_objective: The original, possibly vague objective.

        Returns:
            A SMART-formatted objective string.
        """
        if self.demo_mode:
            return (
                f"Achieve the following: {raw_objective} — specifically, increase the "
                "target metric by 30% within 90 days (Q2 2026), measured through "
                "platform analytics, with weekly progress check-ins against baseline."
            )

        user_prompt = f"""Take this campaign objective and reformat it as a SMART goal.

Original objective: {raw_objective}

SMART criteria:
- Specific: What exactly will be accomplished?
- Measurable: How will success be measured? What's the metric?
- Achievable: Is it realistic given typical resources?
- Relevant: Does it tie to a business outcome?
- Time-bound: What's the deadline?

Return a JSON object with one key:
- "smart_objective": string (the reformatted objective, 2-3 sentences max)"""

        result = self._call_claude(user_prompt, max_tokens=500)
        return result.get("smart_objective", raw_objective)

    # ------------------------------------------------------------------
    # 3. generate_campaign_names
    # ------------------------------------------------------------------

    def generate_campaign_names(
        self,
        feature_description: str,
        audience: str,
        count: int = 5,
    ) -> list[str]:
        """Suggest creative campaign names.

        Args:
            feature_description: What the product/feature does.
            audience: Who the campaign is for.
            count: Number of name suggestions (default 5).

        Returns:
            List of campaign name suggestions.
        """
        if self.demo_mode:
            return _demo_campaign_names()[:count]

        user_prompt = f"""Generate exactly {count} creative campaign name ideas.

Feature/Product: {feature_description}
Target Audience: {audience}

Requirements:
- Memorable and catchy for internal use
- Mix of styles: punchy, descriptive, aspirational
- 2-5 words each
- No generic names like "Campaign 2026"

Return a JSON object with one key:
- "names": list of {count} strings"""

        result = self._call_claude(user_prompt, max_tokens=500)
        return result.get("names", _demo_campaign_names()[:count])

    # ------------------------------------------------------------------
    # 4. generate_smp
    # ------------------------------------------------------------------

    def generate_smp(self, brief_context: dict[str, Any]) -> dict[str, str]:
        """Generate a Single-Minded Proposition with quality check.

        Args:
            brief_context: Dict with keys like campaign_name, objective,
                target_audience, key_insight, feature_description.

        Returns:
            Dict with "smp", "quality_check" (pass/fail), "quality_reason".
        """
        if self.demo_mode:
            return _demo_smp()

        user_prompt = f"""Generate a Single-Minded Proposition (SMP) for this campaign.

Context:
- Campaign: {brief_context.get('campaign_name', 'N/A')}
- Objective: {brief_context.get('objective', 'N/A')}
- Audience: {brief_context.get('target_audience', 'N/A')}
- Key Insight: {brief_context.get('key_insight', 'N/A')}
- Feature: {brief_context.get('feature_description', 'N/A')}

An SMP is the ONE thing the audience should take away. It must be:
- Single-focused (ONE benefit, ONE idea)
- Emotionally resonant
- Brief (under 10 words)
- Impossible to misunderstand

CRITICAL QUALITY CHECK: The SMP FAILS if it:
- Contains "and", "also", "plus"
- Tries to communicate two distinct benefits
- Is a compound sentence with two independent ideas

Return a JSON object:
- "smp": string
- "quality_check": "pass" or "fail"
- "quality_reason": string explaining why it passes or fails"""

        return self._call_claude(user_prompt, max_tokens=500)

    # ------------------------------------------------------------------
    # 5. generate_audience_profile
    # ------------------------------------------------------------------

    def generate_audience_profile(self, audience_description: str) -> dict[str, Any]:
        """Expand a short audience description into a full profile.

        Args:
            audience_description: Brief description of the target audience.

        Returns:
            Dict with demographics, psychographics, pain_points,
            motivations, media_habits, objections.
        """
        if self.demo_mode:
            return _demo_audience_profile()

        user_prompt = f"""Expand this audience description into a full marketing persona profile.

Audience: {audience_description}

Return a JSON object with these keys:
- "demographics": string (age range, gender split, location, income bracket, job roles)
- "psychographics": string (values, attitudes, lifestyle, technology adoption level)
- "pain_points": list of 4-5 specific pain points
- "motivations": list of 4-5 motivations/goals
- "media_habits": list of 5-6 media channels and platforms they use
- "objections": list of 3-4 likely objections to the product/campaign"""

        return self._call_claude(user_prompt, max_tokens=1500)

    # ------------------------------------------------------------------
    # 6. generate_channel_plan
    # ------------------------------------------------------------------

    def generate_channel_plan(
        self,
        brief_context: dict[str, Any],
        budget: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Generate a channel plan with tactics and budget allocation.

        Args:
            brief_context: Dict with campaign_name, objective,
                target_audience, key_messages.
            budget: Optional total budget in dollars.

        Returns:
            List of channel plan dicts with channel, tactic, rationale, budget_pct.
        """
        if self.demo_mode:
            return _demo_channel_plan()

        budget_note = f"Total budget: ${budget:,.0f}" if budget else "No specific budget — provide percentage-based allocation"

        user_prompt = f"""Create a channel plan for this campaign.

Context:
- Campaign: {brief_context.get('campaign_name', 'N/A')}
- Objective: {brief_context.get('objective', 'N/A')}
- Audience: {json.dumps(brief_context.get('target_audience', 'N/A'))}
- Key Messages: {json.dumps(brief_context.get('key_messages', []))}
- {budget_note}

Available channels: Email, In-App, Social Media, Blog, Video, Paid Search, PR, Events

Return a JSON object:
- "channel_plan": list of objects, each with:
  - "channel": string (from the list above)
  - "tactic": string (specific tactic for this channel)
  - "rationale": string (why this channel for this audience)
  - "budget_pct": number (percentage of total budget, all must sum to 100)

Include 5-8 channels. Allocate based on audience media habits and campaign objectives."""

        result = self._call_claude(user_prompt, max_tokens=2000)
        return result.get("channel_plan", _demo_channel_plan())

    # ------------------------------------------------------------------
    # 7. generate_raci_matrix
    # ------------------------------------------------------------------

    def generate_raci_matrix(
        self, campaign_type: str = "product_launch"
    ) -> list[dict[str, str]]:
        """Generate a RACI matrix for the campaign.

        Args:
            campaign_type: Type of campaign (product_launch, feature_update,
                competitive_response, brand_awareness, seasonal, re_engagement).

        Returns:
            List of dicts with keys: task, responsible, accountable, consulted, informed.
        """
        if self.demo_mode:
            return [
                {"task": "Campaign Strategy & Brief", "responsible": "PMM Lead", "accountable": "VP Marketing", "consulted": "Product, Data Science", "informed": "Executive Team"},
                {"task": "Creative Asset Development", "responsible": "Creative Team", "accountable": "PMM Lead", "consulted": "Brand Guidelines", "informed": "PMM"},
                {"task": "Email Campaign Execution", "responsible": "Email Marketing", "accountable": "PMM Lead", "consulted": "CRM Team", "informed": "Analytics"},
                {"task": "Social Media Campaign", "responsible": "Social Team", "accountable": "PMM Lead", "consulted": "Creative, Legal", "informed": "PR"},
                {"task": "Performance Reporting", "responsible": "Analytics Team", "accountable": "PMM Lead", "consulted": "Data Science", "informed": "Executive Team"},
            ]

        user_prompt = f"""Generate a RACI matrix for a {campaign_type} marketing campaign.

Create 5-7 key tasks for this campaign. For each task, assign roles:
- Responsible: Who does the work
- Accountable: Who owns the outcome
- Consulted: Who provides input
- Informed: Who is kept in the loop

Return JSON: {{"raci": [{{"task": str, "responsible": str, "accountable": str, "consulted": str, "informed": str}}, ...]}}"""

        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=user_prompt, max_tokens=2048,
            )
            result = _parse_json_response(raw_text)
            if result and isinstance(result, dict):
                return result.get("raci", [])
            if result and isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error("generate_raci_matrix error: %s", e)
            return []

    # ------------------------------------------------------------------
    # 8. render_brief_markdown
    # ------------------------------------------------------------------

    def render_brief_markdown(self, brief: dict[str, Any]) -> str:
        """Render a complete brief as a professional markdown document.

        Args:
            brief: A full brief dict as returned by generate_full_brief().

        Returns:
            Markdown-formatted string with all 14 sections.
        """
        lines: list[str] = []

        # --- Header ---
        lines.append(f"# Campaign Brief: {brief.get('campaign_name', 'Untitled')}")
        lines.append("")
        lines.append(f"**Launch Tier:** {brief.get('launch_tier', 'N/A')}  ")
        lines.append(f"**Generated:** {brief.get('generated_at', 'N/A')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # --- 1. Background/Context ---
        lines.append("## 1. Background & Context")
        lines.append(brief.get("background_context", "N/A"))
        lines.append("")

        # --- 2. Objective ---
        lines.append("## 2. Objective (SMART)")
        lines.append(brief.get("objective_smart", "N/A"))
        lines.append("")

        # --- 3. Target Audience ---
        lines.append("## 3. Target Audience")
        audience = brief.get("target_audience", {})
        if isinstance(audience, dict):
            lines.append(f"**Demographics:** {audience.get('demographics', 'N/A')}  ")
            lines.append(f"**Psychographics:** {audience.get('psychographics', 'N/A')}")
            lines.append("")
            if audience.get("pain_points"):
                lines.append("**Pain Points:**")
                for pt in audience["pain_points"]:
                    lines.append(f"- {pt}")
                lines.append("")
            if audience.get("motivations"):
                lines.append("**Motivations:**")
                for m in audience["motivations"]:
                    lines.append(f"- {m}")
                lines.append("")
            if audience.get("media_habits"):
                lines.append("**Media Habits:**")
                for h in audience["media_habits"]:
                    lines.append(f"- {h}")
                lines.append("")
            if audience.get("objections"):
                lines.append("**Likely Objections:**")
                for obj in audience["objections"]:
                    lines.append(f"- {obj}")
                lines.append("")
        else:
            lines.append(str(audience))
            lines.append("")

        # --- 4. Key Insight ---
        lines.append("## 4. Key Insight")
        lines.append(f"*{brief.get('key_insight', 'N/A')}*")
        lines.append("")

        # --- 5. Positioning ---
        lines.append("## 5. Positioning Statement")
        lines.append(f"**Short (25 words):** {brief.get('positioning_short', 'N/A')}")
        lines.append("")
        lines.append(f"**Detailed (100 words):** {brief.get('positioning_detailed', 'N/A')}")
        lines.append("")

        # --- 6. Key Messages ---
        lines.append("## 6. Key Messages")
        for i, msg in enumerate(brief.get("key_messages", []), 1):
            lines.append(f"{i}. {msg}")
        lines.append("")

        # --- 7. Single-Minded Proposition ---
        lines.append("## 7. Single-Minded Proposition (SMP)")
        smp_data = brief.get("single_minded_proposition", {})
        if isinstance(smp_data, dict):
            smp_text = smp_data.get("smp", "N/A")
            qc = smp_data.get("quality_check", "N/A")
            qr = smp_data.get("quality_reason", "")
            badge = "PASS" if qc == "pass" else "FAIL"
            lines.append(f"**\"{smp_text}\"**")
            lines.append("")
            lines.append(f"Quality Check: **{badge}** — {qr}")
        else:
            lines.append(str(smp_data))
        lines.append("")

        # --- 8. Channel Plan ---
        lines.append("## 8. Channel Plan")
        lines.append("")
        lines.append("| Channel | Tactic | Rationale | Budget % |")
        lines.append("|---------|--------|-----------|----------|")
        for ch in brief.get("channel_plan", []):
            lines.append(
                f"| {ch.get('channel', 'N/A')} "
                f"| {ch.get('tactic', 'N/A')} "
                f"| {ch.get('rationale', 'N/A')} "
                f"| {ch.get('budget_pct', 'N/A')}% |"
            )
        lines.append("")

        # --- 9. Content Deliverables ---
        lines.append("## 9. Content Deliverables")
        lines.append("")
        deliverables = brief.get("deliverables", brief.get("content_deliverables", []))
        if deliverables:
            lines.append("| Asset | Spec | Owner |")
            lines.append("|-------|------|-------|")
            for d in deliverables:
                if isinstance(d, dict):
                    lines.append(
                        f"| {d.get('asset', d.get('asset_type', 'N/A'))} "
                        f"| {d.get('spec', d.get('specs', 'N/A'))} "
                        f"| {d.get('owner', d.get('quantity', 'N/A'))} |"
                    )
                else:
                    lines.append(f"- {d}")
        else:
            lines.append("Not specified")
        lines.append("")

        # --- 10. Success Metrics ---
        lines.append("## 10. Success Metrics / KPIs")
        lines.append("")
        lines.append("| KPI | Target | Measurement |")
        lines.append("|-----|--------|-------------|")
        for m in brief.get("success_metrics", []):
            lines.append(
                f"| {m.get('metric', m.get('kpi', 'N/A'))} "
                f"| {m.get('target', 'N/A')} "
                f"| {m.get('measurement', m.get('measurement_method', 'N/A'))} |"
            )
        lines.append("")

        # --- 11. Timeline ---
        lines.append("## 11. Timeline")
        lines.append("")
        for phase in brief.get("timeline", []):
            phase_name = phase.get("phase", "N/A")
            dates = phase.get("dates", phase.get("duration", "N/A"))
            lines.append(f"### {phase_name} ({dates})")
            for action in phase.get("actions", phase.get("activities", [])):
                lines.append(f"- {action}")
            lines.append("")

        # --- 12. Budget Breakdown ---
        budget = brief.get("budget_breakdown")
        if budget:
            lines.append("## 12. Budget Breakdown")
            lines.append("")
            if isinstance(budget, dict):
                lines.append("| Channel | Amount |")
                lines.append("|---------|--------|")
                for channel, amount in budget.items():
                    if isinstance(amount, (int, float)):
                        lines.append(f"| {channel} | ${amount:,.0f} |")
                    else:
                        lines.append(f"| {channel} | {amount} |")
            elif isinstance(budget, list):
                lines.append("| Category | Amount | Notes |")
                lines.append("|----------|--------|-------|")
                for b in budget:
                    lines.append(
                        f"| {b.get('category', 'N/A')} "
                        f"| {b.get('amount_pct', b.get('amount', 'N/A'))} "
                        f"| {b.get('notes', '')} |"
                    )
            lines.append("")

        # --- 13. RACI Matrix ---
        lines.append("## 13. RACI Matrix")
        lines.append("")
        raci = brief.get("raci_matrix", {})
        if isinstance(raci, dict):
            lines.append("| Role | Responsibility |")
            lines.append("|------|---------------|")
            for role, resp in raci.items():
                lines.append(f"| {role} | {resp} |")
        lines.append("")

        # --- 14. Approvals ---
        lines.append("## 14. Approvals Needed")
        lines.append("")
        lines.append("| Stakeholder | Approves |")
        lines.append("|-------------|----------|")
        for a in brief.get("approvals_needed", []):
            lines.append(
                f"| {a.get('stakeholder', 'N/A')} "
                f"| {a.get('approves', a.get('what_they_approve', 'N/A'))} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("*Generated by Campaign Brief Generator AI*")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 9. classify_launch_tier
    # ------------------------------------------------------------------

    def classify_launch_tier(self, feature_description: str) -> dict[str, str]:
        """Auto-classify a feature into a launch tier (Tier 0-3).

        Args:
            feature_description: Description of the feature or product.

        Returns:
            Dict with "tier", "reasoning", and "brief_depth".
        """
        if self.demo_mode:
            return _demo_launch_tier()

        user_prompt = f"""Classify this feature into a launch tier based on the Product Marketing Alliance framework.

Feature: {feature_description}

Tier definitions:
- Tier 0: Company-defining — entirely new platform, new business model, rebrand. Requires full brief + war room + executive sponsorship.
- Tier 1: Major feature — significant new capability that changes user workflow. Requires full 14-section brief.
- Tier 2: Enhancement — improvement to existing feature, quality-of-life update. Requires light brief (5-7 key sections).
- Tier 3: Bug fix / minor — small fix, copy change, UI tweak. No brief needed.

Return a JSON object:
- "tier": string (one of "Tier 0", "Tier 1", "Tier 2", "Tier 3")
- "reasoning": string (2-3 sentences explaining the classification)
- "brief_depth": string (what kind of brief is recommended)"""

        return self._call_claude(user_prompt, max_tokens=500)


    # ------------------------------------------------------------------
    # Convenience wrappers for section-level generation
    # ------------------------------------------------------------------

    def extract_insight(self, background: str, audience: str) -> str:
        """Extract the key human insight from background and audience info."""
        if self.demo_mode:
            return ("Sellers don't just want faster listings — they want to feel confident "
                    "that their listings will actually sell. The fear of wasted effort is "
                    "the real barrier to listing more items.")
        prompt = (
            f"Background: {background}\nAudience: {audience}\n\n"
            "Extract the single most powerful human insight — the emotional truth "
            "that would make this audience care. Return ONLY the insight as a single "
            "paragraph (2-3 sentences). No JSON, no labels."
        )
        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=prompt, max_tokens=256,
            )
            return raw_text.strip()
        except Exception as e:
            logger.error("extract_insight error: %s", e)
            return "Unable to extract insight automatically."

    def generate_positioning(self, brief_context: dict) -> dict:
        """Generate short and detailed positioning statements."""
        if self.demo_mode:
            return {
                "positioning_short": "AI-powered listings that sell faster with zero effort.",
                "positioning_detailed": (
                    "For e-commerce sellers who struggle with creating compelling listings, "
                    "our AI Listing Generator transforms product photos into optimized, "
                    "high-converting listings in seconds — unlike manual listing tools that "
                    "require copywriting skills and hours of effort."
                ),
            }
        prompt = (
            f"Brief context: {json.dumps(brief_context, default=str)}\n\n"
            "Generate positioning statements. Return JSON with:\n"
            '"positioning_short": 25-word max positioning statement\n'
            '"positioning_detailed": 100-word detailed positioning statement'
        )
        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=prompt, max_tokens=2048,
            )
            return _parse_json_response(raw_text) or {
                "positioning_short": "", "positioning_detailed": ""
            }
        except Exception as e:
            logger.error("generate_positioning error: %s", e)
            return {"positioning_short": "", "positioning_detailed": ""}

    def generate_key_messages(self, brief_context: dict) -> list:
        """Generate 3-5 ranked key messages."""
        if self.demo_mode:
            return [
                "List in seconds, not hours — just snap a photo and AI does the rest.",
                "AI-optimized titles and descriptions that buyers actually search for.",
                "Join 10M+ sellers already using AI to list smarter and sell faster.",
                "Focus on sourcing great products — let AI handle the listing.",
                "From photo to published in under 60 seconds.",
            ]
        prompt = (
            f"Brief context: {json.dumps(brief_context, default=str)}\n\n"
            "Generate 3-5 key messages ranked by impact. "
            'Return JSON: {"messages": ["msg1", "msg2", ...]}'
        )
        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=prompt, max_tokens=2048,
            )
            result = _parse_json_response(raw_text)
            return result.get("messages", []) if result else []
        except Exception as e:
            logger.error("generate_key_messages error: %s", e)
            return []

    def generate_deliverables(self, brief_context: dict) -> list:
        """Generate list of content deliverables with specs."""
        if self.demo_mode:
            return [
                {"asset": "Launch Email", "spec": "HTML, 600px wide, 200 words max", "owner": "PMM"},
                {"asset": "In-App Banner", "spec": "1200x400px, 15 words max", "owner": "Design"},
                {"asset": "Blog Post", "spec": "800-1000 words, SEO-optimized", "owner": "Content"},
                {"asset": "Tutorial Video", "spec": "60-90 seconds, screen recording + voiceover", "owner": "Video"},
                {"asset": "Social Posts (x5)", "spec": "Platform-native formats, 280 chars max", "owner": "Social"},
                {"asset": "Help Center Article", "spec": "Step-by-step guide with screenshots", "owner": "Support"},
            ]
        prompt = (
            f"Brief context: {json.dumps(brief_context, default=str)}\n\n"
            "Generate a list of content deliverables needed for this campaign. "
            'Return JSON: {"deliverables": [{"asset": str, "spec": str, "owner": str}, ...]}'
        )
        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=prompt, max_tokens=2048,
            )
            result = _parse_json_response(raw_text)
            return result.get("deliverables", []) if result else []
        except Exception as e:
            logger.error("generate_deliverables error: %s", e)
            return []

    def generate_timeline(self, brief_context: dict) -> list:
        """Generate phased campaign timeline."""
        if self.demo_mode:
            return [
                {"phase": "Awareness", "duration": "Week 1-2", "actions": ["Teaser emails", "Social posts", "Internal briefing"]},
                {"phase": "Launch", "duration": "Week 3", "actions": ["Launch email", "In-app announcement", "Blog post", "PR outreach"]},
                {"phase": "Sustain", "duration": "Week 4-6", "actions": ["Tutorial content", "Success stories", "Retargeting ads"]},
                {"phase": "Optimize", "duration": "Week 7+", "actions": ["Analyze metrics", "A/B test refinements", "Scale winning channels"]},
            ]
        prompt = (
            f"Brief context: {json.dumps(brief_context, default=str)}\n\n"
            "Generate a phased campaign timeline with 4 phases: Awareness, Launch, Sustain, Optimize. "
            'Return JSON: {"timeline": [{"phase": str, "duration": str, "actions": [str]}, ...]}'
        )
        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=prompt, max_tokens=2048,
            )
            result = _parse_json_response(raw_text)
            return result.get("timeline", []) if result else []
        except Exception as e:
            logger.error("generate_timeline error: %s", e)
            return []

    def generate_kpis(self, brief_context: dict) -> list:
        """Generate success metrics and KPIs."""
        if self.demo_mode:
            return [
                {"metric": "Adoption Rate", "target": "50% of active sellers", "measurement": "Product analytics dashboard"},
                {"metric": "Listing Completion Rate", "target": ">90%", "measurement": "Funnel tracking"},
                {"metric": "Email Open Rate", "target": ">25%", "measurement": "Email platform"},
                {"metric": "Time to First AI Listing", "target": "<5 minutes", "measurement": "User session data"},
                {"metric": "Seller Satisfaction (CSAT)", "target": ">80%", "measurement": "Post-use survey"},
            ]
        prompt = (
            f"Brief context: {json.dumps(brief_context, default=str)}\n\n"
            "Generate 5-7 success metrics/KPIs for this campaign. "
            'Return JSON: {"kpis": [{"metric": str, "target": str, "measurement": str}, ...]}'
        )
        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=self.system_prompt, user_prompt=prompt, max_tokens=2048,
            )
            result = _parse_json_response(raw_text)
            return result.get("kpis", []) if result else []
        except Exception as e:
            logger.error("generate_kpis error: %s", e)
            return []

    # ------------------------------------------------------------------
    # 13. help_write_background
    # ------------------------------------------------------------------

    def help_write_background(self, campaign_name: str, context: str = "") -> str:
        """Generate a background/context paragraph from campaign name and optional context.

        Args:
            campaign_name: The campaign or product/feature name.
            context: Optional additional context (e.g., from uploaded documents).

        Returns:
            A background/context paragraph string.
        """
        if self.demo_mode:
            return (
                f"The market for {campaign_name or 'this product'} is rapidly evolving. "
                "Key competitors have recently launched similar capabilities, raising customer "
                "expectations and creating urgency. Our internal data shows a 40% increase in "
                "user requests for this functionality over the past quarter. With Q2 being peak "
                "acquisition season, the timing is critical to capture mindshare and establish "
                "category leadership before competitors consolidate their position."
            )

        extra = f"\n\nAdditional context from documents:\n{context[:2000]}" if context else ""
        user_prompt = f"""Write a compelling Background/Context paragraph for a campaign brief.

Campaign/Product: {campaign_name}
{extra}

The background should answer "Why now?" and include:
- Market conditions or competitive triggers
- Internal data or trends that support the campaign
- Urgency and timing rationale

Return a JSON object with one key:
- "background": string (2-4 sentences, professional tone)"""

        try:
            result = self._call_claude(user_prompt, max_tokens=500)
            return result.get("background", "")
        except Exception as e:
            logger.error("help_write_background error: %s", e)
            return f"Error generating background: {e}"

    # ------------------------------------------------------------------
    # 14. proofread_text
    # ------------------------------------------------------------------

    def proofread_text(self, text: str) -> str:
        """Proofread and refine text for grammar, clarity, and tone.

        Args:
            text: The text to proofread.

        Returns:
            The improved text string.
        """
        if self.demo_mode:
            return (
                text.rstrip(".") + ". "
                "[Proofread version] This text has been refined for clarity, grammar, "
                "and professional tone. Sentences have been tightened, passive voice "
                "has been converted to active voice, and marketing jargon has been "
                "replaced with clear, direct language."
            )

        user_prompt = f"""Proofread and refine the following text for a campaign brief.

Text to proofread:
{text}

Fix:
- Grammar and spelling errors
- Passive voice → active voice
- Vague language → specific, concrete language
- Overly long sentences → concise, clear statements
- Inconsistent tone → professional marketing tone

Return a JSON object with one key:
- "proofread": string (the improved text, same length or shorter)"""

        try:
            result = self._call_claude(user_prompt, max_tokens=800)
            return result.get("proofread", text)
        except Exception as e:
            logger.error("proofread_text error: %s", e)
            return f"Error proofreading: {e}"

    # ------------------------------------------------------------------
    # 15. summarize_text
    # ------------------------------------------------------------------

    def summarize_text(self, text: str) -> str:
        """Summarize text into 2-3 concise sentences.

        Args:
            text: The text to summarize.

        Returns:
            A 2-3 sentence summary string.
        """
        if self.demo_mode:
            # Return a shortened version
            sentences = text.split(".")
            if len(sentences) > 3:
                return ". ".join(s.strip() for s in sentences[:3] if s.strip()) + "."
            return text

        user_prompt = f"""Summarize the following text into 2-3 concise sentences.

Text:
{text}

Keep the most important points: the "why now", key trigger, and business impact.

Return a JSON object with one key:
- "summary": string (2-3 sentences max)"""

        try:
            result = self._call_claude(user_prompt, max_tokens=300)
            return result.get("summary", text)
        except Exception as e:
            logger.error("summarize_text error: %s", e)
            return f"Error summarizing: {e}"

    # ------------------------------------------------------------------
    # 16. generate_objective
    # ------------------------------------------------------------------

    def generate_objective(self, campaign_name: str, background: str) -> str:
        """Generate a complete SMART campaign objective from context.

        Args:
            campaign_name: The campaign name.
            background: The background/context paragraph.

        Returns:
            A SMART-formatted objective string.
        """
        if self.demo_mode:
            return (
                f"Increase {campaign_name or 'feature'} adoption by 40% among professional "
                "users (those with 50+ monthly transactions) within 90 days of campaign launch "
                "in Q2 2026, measured through product analytics dashboard with weekly progress "
                "tracking against the pre-campaign baseline."
            )

        user_prompt = f"""Generate a SMART campaign objective based on this context.

Campaign: {campaign_name}
Background: {background}

The objective must be:
- Specific: What exactly will be accomplished?
- Measurable: What's the metric and target number?
- Achievable: Realistic given typical marketing resources
- Relevant: Tied to a business outcome
- Time-bound: Has a clear deadline

Return a JSON object with one key:
- "objective": string (1-2 sentences, SMART-formatted)"""

        try:
            result = self._call_claude(user_prompt, max_tokens=500)
            return result.get("objective", "")
        except Exception as e:
            logger.error("generate_objective error: %s", e)
            return f"Error generating objective: {e}"

    # ------------------------------------------------------------------
    # 17. help_write_audience
    # ------------------------------------------------------------------

    def help_write_audience(self, campaign_name: str, background: str, objective: str) -> str:
        """Generate a target audience description from campaign context.

        Args:
            campaign_name: The campaign name.
            background: The background/context.
            objective: The campaign objective.

        Returns:
            A target audience description string.
        """
        if self.demo_mode:
            return (
                f"Primary audience for {campaign_name or 'this campaign'}: Professional users "
                "aged 25-55 who are active on the platform (50+ monthly transactions). They are "
                "efficiency-driven, tech-savvy early adopters who value tools that save time and "
                "scale their operations. Key pain points include manual workflows, inconsistent "
                "quality, and difficulty scaling beyond current volume. They consume content via "
                "YouTube tutorials, industry forums, email newsletters, and social media."
            )

        user_prompt = f"""Generate a target audience description for a campaign brief.

Campaign: {campaign_name}
Background: {background}
Objective: {objective}

Write a concise target audience description (3-5 sentences) that includes:
- Demographics (age, role, location)
- Key behaviors and platform usage
- Pain points relevant to the campaign
- Motivations and decision drivers

Return a JSON object with one key:
- "audience": string (3-5 sentences)"""

        try:
            result = self._call_claude(user_prompt, max_tokens=500)
            return result.get("audience", "")
        except Exception as e:
            logger.error("help_write_audience error: %s", e)
            return f"Error generating audience: {e}"


# ---------------------------------------------------------------------------
# BriefStore class
# ---------------------------------------------------------------------------


class BriefStore:
    """Persists campaign briefs to a local JSON file.

    Stores briefs in data/briefs.json with unique IDs for retrieval,
    search, and deletion.
    """

    def __init__(self, filepath: str = "data/briefs.json") -> None:
        """Initialize the store, creating the data directory and file if needed.

        Args:
            filepath: Path to the JSON storage file.
        """
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        if not self.filepath.exists():
            self.filepath.write_text("[]", encoding="utf-8")
        logger.info("BriefStore initialized at %s", self.filepath.resolve())

    def save(self, brief: dict[str, Any]) -> str:
        """Save a brief and return its unique ID.

        Args:
            brief: A campaign brief dict to persist.

        Returns:
            The generated brief_id string.
        """
        brief_id = brief.get("brief_id") or str(uuid.uuid4())[:8]
        brief["brief_id"] = brief_id
        brief.setdefault("saved_at", datetime.now(timezone.utc).isoformat())

        data = self._read()
        # Replace if same ID exists, otherwise append
        data = [b for b in data if b.get("brief_id") != brief_id]
        data.append(brief)
        self._write(data)

        logger.info("Saved brief '%s' (id=%s)", brief.get("campaign_name"), brief_id)
        return brief_id

    def load_all(self) -> list[dict[str, Any]]:
        """Load and return all stored briefs.

        Returns:
            List of all brief dicts, newest first.
        """
        data = self._read()
        data.sort(key=lambda b: b.get("saved_at", ""), reverse=True)
        return data

    def get_by_id(self, brief_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a specific brief by ID.

        Args:
            brief_id: The unique brief identifier.

        Returns:
            The brief dict if found, None otherwise.
        """
        for brief in self._read():
            if brief.get("brief_id") == brief_id:
                return brief
        logger.warning("Brief not found: %s", brief_id)
        return None

    def delete(self, brief_id: str) -> bool:
        """Delete a brief by ID.

        Args:
            brief_id: The unique brief identifier.

        Returns:
            True if the brief was found and deleted, False otherwise.
        """
        data = self._read()
        original_len = len(data)
        data = [b for b in data if b.get("brief_id") != brief_id]

        if len(data) < original_len:
            self._write(data)
            logger.info("Deleted brief: %s", brief_id)
            return True

        logger.warning("Brief not found for deletion: %s", brief_id)
        return False

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search briefs by keyword across campaign names and objectives.

        Args:
            query: Search query string (case-insensitive).

        Returns:
            List of matching brief dicts.
        """
        query_lower = query.lower()
        results = []

        for brief in self._read():
            searchable = " ".join([
                brief.get("campaign_name", ""),
                brief.get("objective_smart", ""),
                brief.get("background_context", ""),
                brief.get("key_insight", ""),
            ]).lower()

            if query_lower in searchable:
                results.append(brief)

        logger.info("Search '%s' returned %d results", query, len(results))
        return results

    # -- internal helpers --

    def _read(self) -> list[dict[str, Any]]:
        """Read the JSON file contents."""
        try:
            text = self.filepath.read_text(encoding="utf-8")
            return json.loads(text)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Could not read %s; returning empty list", self.filepath)
            return []

    def _write(self, data: list[dict[str, Any]]) -> None:
        """Write the full list back to JSON."""
        self.filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 60)
    print("Campaign Brief Generator — Module Test")
    print("=" * 60)

    generator = BriefGenerator()
    store = BriefStore()

    if generator.demo_mode:
        print("\n[DEMO MODE] No API key found — using sample data.\n")

    # --- Test 1: Generate full brief ---
    print("\n--- Test 1: Generate Full Brief ---\n")
    brief = generator.generate_full_brief(
        campaign_name="AI Listing Magic",
        background="Online sellers spend 15 min per listing. Competitors launching AI tools.",
        objective="Increase AI listing tool adoption by 30% in Q2 2026",
        target_audience="Professional sellers with 50+ monthly listings",
        feature_description="AI-Powered Listing Generator that creates complete product listings from a single photo",
        launch_tier="Tier 1",
        budget=75000,
    )
    print(f"  Campaign: {brief.get('campaign_name')}")
    print(f"  Tier: {brief.get('launch_tier')}")
    print(f"  Messages: {len(brief.get('key_messages', []))}")
    print(f"  Channels: {len(brief.get('channel_plan', []))}")

    # --- Test 2: SMART objective ---
    print("\n--- Test 2: Make Objective SMART ---\n")
    smart = generator.make_objective_smart("Get more sellers to use the AI listing tool")
    print(f"  SMART: {smart[:120]}...")

    # --- Test 3: Campaign names ---
    print("\n--- Test 3: Campaign Name Suggestions ---\n")
    names = generator.generate_campaign_names(
        feature_description="AI-powered listing generator",
        audience="Professional online sellers",
        count=5,
    )
    for name in names:
        print(f"  - {name}")

    # --- Test 4: SMP ---
    print("\n--- Test 4: Single-Minded Proposition ---\n")
    smp = generator.generate_smp({
        "campaign_name": "AI Listing Magic",
        "objective": "Increase adoption by 30%",
        "target_audience": "Professional sellers",
        "key_insight": "Sellers want to be business owners, not content creators",
        "feature_description": "AI listing generator",
    })
    print(f"  SMP: \"{smp.get('smp')}\"")
    print(f"  Quality: {smp.get('quality_check')} — {smp.get('quality_reason')}")

    # --- Test 5: Audience profile ---
    print("\n--- Test 5: Audience Profile ---\n")
    profile = generator.generate_audience_profile("Professional eBay sellers with 50+ listings per month")
    print(f"  Demographics: {profile.get('demographics', 'N/A')[:80]}...")
    print(f"  Pain Points: {len(profile.get('pain_points', []))}")
    print(f"  Motivations: {len(profile.get('motivations', []))}")

    # --- Test 6: Channel plan ---
    print("\n--- Test 6: Channel Plan ---\n")
    channels = generator.generate_channel_plan(
        brief_context={"campaign_name": "AI Listing Magic", "objective": "Increase adoption"},
        budget=75000,
    )
    for ch in channels:
        print(f"  {ch.get('channel')}: {ch.get('budget_pct')}% — {ch.get('tactic', '')[:50]}")

    # --- Test 7: RACI matrix ---
    print("\n--- Test 7: RACI Matrix ---\n")
    raci = generator.generate_raci_matrix("product_launch")
    for role, resp in raci.items():
        print(f"  {role}: {resp[:60]}...")

    # --- Test 8: Launch tier classification ---
    print("\n--- Test 8: Launch Tier Classification ---\n")
    tier = generator.classify_launch_tier(
        "AI-powered listing generator that creates complete product listings from a single photo"
    )
    print(f"  Tier: {tier.get('tier')}")
    print(f"  Reasoning: {tier.get('reasoning', '')[:100]}...")

    # --- Test 9: Render markdown ---
    print("\n--- Test 9: Render Brief as Markdown ---\n")
    md = generator.render_brief_markdown(brief)
    print(f"  Markdown length: {len(md)} characters")
    print(f"  Preview:\n{md[:500]}...")

    # --- Test 10: BriefStore ---
    print("\n--- Test 10: BriefStore CRUD ---\n")
    brief_id = store.save(brief)
    print(f"  Saved brief ID: {brief_id}")

    loaded = store.get_by_id(brief_id)
    print(f"  Loaded by ID: {loaded.get('campaign_name') if loaded else 'NOT FOUND'}")

    all_briefs = store.load_all()
    print(f"  Total briefs in store: {len(all_briefs)}")

    search_results = store.search("listing")
    print(f"  Search 'listing': {len(search_results)} results")

    deleted = store.delete(brief_id)
    print(f"  Deleted: {deleted}")
    print(f"  After delete: {len(store.load_all())} briefs")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
