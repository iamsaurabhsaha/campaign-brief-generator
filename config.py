"""
Configuration constants for the Campaign Brief Generator.
"""

# ── App Metadata ─────────────────────────────────────────────────────────────
APP_NAME = "Campaign Brief Generator"
VERSION = "1.0.0"

# ── Color Constants ──────────────────────────────────────────────────────────
PRIMARY_BLUE = "#1E3A5F"
ACCENT_RED = "#E74C3C"
ACCENT_YELLOW = "#F39C12"
ACCENT_GREEN = "#27AE60"

# ── API Configuration ────────────────────────────────────────────────────────
# LLM provider and model are now configured via environment variables.
# See .env.example for all supported providers (Anthropic, OpenAI, Azure,
# Google Gemini, AWS Bedrock, Ollama).
# Legacy constant kept for backward compatibility with any external references.
MAX_TOKENS = 4096

# ── Brief Sections ───────────────────────────────────────────────────────────
BRIEF_SECTIONS = [
    {
        "name": "Campaign Name",
        "description": "Clear, descriptive name that conveys the campaign's purpose at a glance.",
    },
    {
        "name": "Background & Context",
        "description": "Market situation, competitive landscape, and the 'why now' for this campaign.",
    },
    {
        "name": "Objective",
        "description": "Specific, measurable goal the campaign aims to achieve.",
    },
    {
        "name": "Target Audience",
        "description": "Primary and secondary audience segments with behavioral and demographic details.",
    },
    {
        "name": "Key Messages",
        "description": "Core value propositions and supporting proof points for the campaign.",
    },
    {
        "name": "Channel Strategy",
        "description": "Channel mix with allocation percentages and rationale for each channel.",
    },
    {
        "name": "Launch Tier",
        "description": "Campaign tier (0-3) determining scope, resources, and cross-functional involvement.",
    },
    {
        "name": "Timeline & Milestones",
        "description": "Key dates, phases, and deliverable deadlines from kickoff to post-launch.",
    },
    {
        "name": "KPIs & Success Metrics",
        "description": "Quantitative and qualitative metrics to measure campaign effectiveness.",
    },
    {
        "name": "Budget & Resources",
        "description": "Budget allocation across channels, creative production, and tooling.",
    },
    {
        "name": "RACI Matrix",
        "description": "Responsible, Accountable, Consulted, Informed assignments for each workstream.",
    },
    {
        "name": "Risks & Mitigations",
        "description": "Potential risks to campaign success and planned mitigation strategies.",
    },
    {
        "name": "Creative Requirements",
        "description": "Asset specifications, brand guidelines, and creative deliverables needed.",
    },
    {
        "name": "Approval & Sign-off",
        "description": "Stakeholders required to approve the brief before execution begins.",
    },
]

# ── Launch Tiers ─────────────────────────────────────────────────────────────
LAUNCH_TIERS = {
    0: {
        "name": "Tier 0 — Company-Wide Event",
        "description": "Major strategic initiative requiring full company alignment. CEO-level visibility, all-hands involvement, and sustained multi-month execution.",
        "examples": "Annual flagship event, major rebrand, platform migration",
    },
    1: {
        "name": "Tier 1 — Major Launch",
        "description": "High-impact launch with broad channel activation, PR, and cross-functional coordination. Significant budget and executive sponsorship.",
        "examples": "New product line, major feature launch, competitive response",
    },
    2: {
        "name": "Tier 2 — Standard Launch",
        "description": "Moderate-scope campaign targeting existing users or specific segments. Standard channel mix with PMM-led execution.",
        "examples": "Feature update, seasonal campaign, re-engagement",
    },
    3: {
        "name": "Tier 3 — Lightweight Update",
        "description": "Minimal campaign for minor updates. Limited channels, primarily in-app and email. PMM can execute independently.",
        "examples": "Bug fix announcement, minor UI change, policy update",
    },
}

# ── Marketing Channels ───────────────────────────────────────────────────────
CHANNELS = [
    {"name": "Email", "description": "Targeted email campaigns to segmented user lists."},
    {"name": "In-App", "description": "In-product messaging, banners, tooltips, and modals."},
    {"name": "Social Media", "description": "Organic and paid posts across social platforms."},
    {"name": "Blog", "description": "Long-form content on the company blog or publication."},
    {"name": "PR", "description": "Press releases, media outreach, and analyst briefings."},
    {"name": "Paid Search", "description": "Search engine marketing and keyword-targeted ads."},
    {"name": "Paid Retargeting", "description": "Display and social retargeting of known audiences."},
    {"name": "Video", "description": "Video content for social, YouTube, and on-site embedding."},
    {"name": "Events", "description": "Webinars, conferences, and community events."},
    {"name": "Paid Display", "description": "Banner and programmatic display advertising."},
]

# ── Quality Dimensions ───────────────────────────────────────────────────────
QUALITY_DIMENSIONS = [
    {
        "name": "Clarity",
        "description": "Is the brief easy to understand? Are objectives and audience clearly defined with no ambiguity?",
    },
    {
        "name": "Completeness",
        "description": "Are all essential sections filled in with sufficient detail? Are there gaps that would block execution?",
    },
    {
        "name": "Measurability",
        "description": "Are KPIs specific and quantifiable? Can success be objectively determined at campaign end?",
    },
    {
        "name": "Feasibility",
        "description": "Is the timeline realistic? Are resource requirements achievable given constraints?",
    },
    {
        "name": "Strategic Alignment",
        "description": "Does the campaign align with broader business goals, brand positioning, and current priorities?",
    },
]

# ── Common Mistakes ──────────────────────────────────────────────────────────
COMMON_MISTAKES = [
    {
        "name": "Vague Objectives",
        "description": "Objectives lack specificity — missing numeric targets, timeframes, or clear success criteria.",
    },
    {
        "name": "Undefined Audience",
        "description": "Target audience described too broadly or without behavioral/demographic segmentation.",
    },
    {
        "name": "Missing KPIs",
        "description": "No measurable success metrics defined, making it impossible to evaluate campaign effectiveness.",
    },
    {
        "name": "Unrealistic Timeline",
        "description": "Timeline doesn't account for creative production, approvals, or cross-functional dependencies.",
    },
    {
        "name": "Channel Mismatch",
        "description": "Selected channels don't align with where the target audience actually engages.",
    },
    {
        "name": "No Competitive Context",
        "description": "Background section ignores competitive landscape and fails to establish differentiation.",
    },
    {
        "name": "Scope Creep",
        "description": "Brief tries to accomplish too many objectives or address too many audiences simultaneously.",
    },
    {
        "name": "Missing RACI",
        "description": "No clear ownership or accountability assignments, leading to execution confusion.",
    },
    {
        "name": "Budget Gaps",
        "description": "Budget not specified or not broken down by channel, leaving teams without spending guidance.",
    },
]

# ── RACI Roles ───────────────────────────────────────────────────────────────
RACI_ROLES = [
    "PMM",
    "Product",
    "Engineering",
    "Design",
    "Sales",
    "Support",
    "Legal",
    "Exec",
]

# ── Campaign Types ───────────────────────────────────────────────────────────
CAMPAIGN_TYPES = [
    "Product Launch",
    "Feature Update",
    "Competitive Response",
    "Seasonal Campaign",
    "Re-engagement Campaign",
    "Brand Awareness",
    "Partnership Announcement",
    "Policy / Compliance Update",
    "Customer Education",
    "Expansion / New Market",
]
