"""
Quality Checker Module for the Campaign Brief Generator.

Scores campaign briefs against best practices and catches common mistakes.
Uses the Anthropic Claude API for intelligent analysis, with a demo mode
fallback when no API key is available.
"""

import json
import logging
import os
import re
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

import llm_provider

# The 14-section framework from CLAUDE.md
BRIEF_SECTIONS = [
    "Campaign Name",
    "Background/Context",
    "Objective",
    "Target Audience",
    "Key Insight",
    "Positioning Statement",
    "Key Messages",
    "Single-Minded Proposition (SMP)",
    "Channel Plan",
    "Content Deliverables",
    "Success Metrics/KPIs",
    "Timeline",
    "Budget",
    "Approvals/RACI",
]

# The 9 common mistakes
COMMON_MISTAKES = [
    "Too long (>2 pages / >1000 words)",
    "Multiple objectives",
    "Vague audience",
    "No insight",
    "And/also in SMP",
    "No success metrics",
    "No competitive context",
    "Missing why now / background",
    "No approvals / RACI defined",
]

QUALITY_CHECK_SYSTEM_PROMPT = """You are an expert campaign brief reviewer with deep knowledge of \
marketing best practices. You analyze campaign briefs against a 14-section framework and check \
for 9 common mistakes.

The 14 essential sections of a great campaign brief are:
1. Campaign Name
2. Background/Context (the "why now")
3. Objective (SMART format)
4. Target Audience (specific, with pain points)
5. Key Insight (human truth, not just data)
6. Positioning Statement (short + detailed)
7. Key Messages (3-5, ranked)
8. Single-Minded Proposition / SMP (ONE thing, no "and/also")
9. Channel Plan (channel + tactic + owner + due date)
10. Content Deliverables (assets with specs)
11. Success Metrics / KPIs (specific, measurable targets)
12. Timeline (phased)
13. Budget (allocation across channels)
14. Approvals / RACI (who decides what)

The 9 common mistakes to check for:
1. Too long (>2 pages / >1000 words)
2. Multiple objectives (should be ONE primary objective)
3. Vague audience ("everyone", "all users", "general public", etc.)
4. No insight (data without human truth)
5. "And/also" in SMP (not single-minded if it contains "and", "also", "plus", "as well as")
6. No success metrics
7. No competitive context
8. Missing "why now" / background
9. No approvals / RACI defined

Return your analysis as valid JSON only — no markdown fencing."""

SMP_CHECK_SYSTEM_PROMPT = """You are an expert at evaluating Single-Minded Propositions (SMPs) \
for campaign briefs. An SMP must be:
- Truly single-minded: ONE core idea, not multiple ideas joined by "and", "also", "plus", "as well as"
- Concise: ideally under 15 words
- Clear: anyone in the company should understand it immediately
- Compelling: it should make someone care

Return your analysis as valid JSON only — no markdown fencing."""

SMART_CHECK_SYSTEM_PROMPT = """You are an expert at evaluating marketing objectives using the \
SMART framework (Specific, Measurable, Achievable, Relevant, Time-bound). \
Analyze the given objective and provide detailed feedback on each SMART dimension.

Return your analysis as valid JSON only — no markdown fencing."""

COMPARE_SYSTEM_PROMPT = """You are an expert campaign brief reviewer. You will compare two \
campaign briefs (Brief A and Brief B) and determine which is stronger, providing detailed \
reasoning across multiple quality dimensions.

Return your analysis as valid JSON only — no markdown fencing."""


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract and parse JSON from a model response, with fallbacks."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    for fence in ("```json", "```"):
        if fence in text:
            start = text.index(fence) + len(fence)
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass

    # Try finding the first { ... } block
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse JSON from response: %s", text[:200])
    return None


def _score_to_grade(score: float) -> str:
    """Convert a numeric score (1-10) to a letter grade."""
    if score >= 9:
        return "A"
    elif score >= 7:
        return "B"
    elif score >= 5:
        return "C"
    elif score >= 3:
        return "D"
    else:
        return "F"


# ---------------------------------------------------------------------------
# Demo / sample data
# ---------------------------------------------------------------------------

def _demo_check_brief() -> dict:
    """Return a sample brief quality check result for demo mode."""
    return {
        "overall_score": 6,
        "grade": "C",
        "dimension_scores": {
            "clarity": 7,
            "specificity": 5,
            "actionability": 6,
            "audience_focus": 5,
            "measurability": 4,
        },
        "mistakes_found": [
            {
                "mistake": "Vague audience",
                "severity": "critical",
                "description": "The target audience is described as 'small business owners' "
                               "without specific demographics, pain points, or behavioral traits.",
                "fix": "Define the audience with specifics: 'Small business owners aged 30-50 "
                       "with fewer than 10 employees who currently manage inventory manually "
                       "and are frustrated by stockouts during peak seasons.'",
            },
            {
                "mistake": "No success metrics",
                "severity": "critical",
                "description": "The brief does not include any specific KPIs or success metrics. "
                               "There is no way to measure if the campaign succeeds.",
                "fix": "Add 3-5 specific, measurable KPIs such as: 'Increase trial sign-ups by "
                       "25% within 60 days', 'Achieve 15% email open rate', 'Drive 500 demo "
                       "requests in Q2'.",
            },
            {
                "mistake": "And/also in SMP",
                "severity": "warning",
                "description": "The SMP contains 'and also' which indicates it is trying to "
                               "communicate multiple ideas instead of one single-minded message.",
                "fix": "Choose the strongest single idea and remove the secondary message. "
                       "A great SMP is one sentence, one idea, no conjunctions.",
            },
            {
                "mistake": "Missing why now / background",
                "severity": "warning",
                "description": "The brief lacks context on why this campaign is happening now. "
                               "What market event, competitor move, or customer need triggered it?",
                "fix": "Add a Background section explaining the catalyst: e.g., 'Competitor X "
                       "launched a similar feature in Q1, and our churn data shows 12% of users "
                       "cited this as a switching reason.'",
            },
        ],
        "strengths": [
            "Clear campaign name that reflects the initiative",
            "Well-structured key messages with clear hierarchy",
            "Channel plan includes specific tactics for each platform",
            "Timeline is phased logically (Awareness -> Launch -> Sustain)",
        ],
        "improvement_suggestions": [
            "PRIORITY 1: Add specific, measurable KPIs with numeric targets and timeframes",
            "PRIORITY 2: Narrow the target audience with demographics, psychographics, and pain points",
            "PRIORITY 3: Rewrite the SMP to focus on ONE single idea — remove 'and also'",
            "PRIORITY 4: Add a Background/Context section with the 'why now' trigger",
            "PRIORITY 5: Include a RACI matrix for campaign approvals and sign-off",
        ],
        "missing_sections": [
            "Background/Context",
            "Key Insight",
            "Success Metrics/KPIs",
            "Budget",
            "Approvals/RACI",
        ],
        "smp_check": {
            "has_smp": True,
            "is_single_minded": False,
            "issue": "SMP contains 'and also', making it a dual proposition rather than single-minded.",
        },
    }


def _demo_check_smp() -> dict:
    """Return a sample SMP check result for demo mode."""
    return {
        "is_single_minded": False,
        "has_and_also": True,
        "word_count": 18,
        "clarity_score": 5,
        "suggestions": [
            "The simplest way to turn your photos into sales.",
            "Sell faster with one-tap AI listings.",
            "From photo to sold — effortlessly.",
        ],
    }


def _demo_check_smart() -> dict:
    """Return a sample SMART objective check for demo mode."""
    return {
        "is_smart": False,
        "specific": {
            "passes": True,
            "feedback": "The objective clearly states what will be achieved (increase trial sign-ups).",
        },
        "measurable": {
            "passes": False,
            "feedback": "No numeric target is specified. Add a percentage or absolute number.",
        },
        "achievable": {
            "passes": True,
            "feedback": "The goal appears realistic given typical campaign performance benchmarks.",
        },
        "relevant": {
            "passes": True,
            "feedback": "Trial sign-ups directly support the product growth strategy.",
        },
        "time_bound": {
            "passes": False,
            "feedback": "No deadline or timeframe is specified. Add 'by Q2 2026' or 'within 60 days'.",
        },
        "improved_version": "Increase trial sign-ups by 25% (from 2,000 to 2,500 per month) "
                            "within 60 days of campaign launch through targeted paid social "
                            "and email nurture sequences.",
    }


def _demo_compare_briefs() -> dict:
    """Return a sample brief comparison result for demo mode."""
    return {
        "winner": "Brief B",
        "score_a": 5,
        "score_b": 8,
        "summary": "Brief B is significantly stronger due to its specific audience definition, "
                   "measurable KPIs, and clear single-minded proposition. Brief A suffers from "
                   "vague targeting and lacks success metrics.",
        "dimension_comparison": {
            "clarity": {"brief_a": 6, "brief_b": 8, "advantage": "Brief B"},
            "specificity": {"brief_a": 4, "brief_b": 9, "advantage": "Brief B"},
            "actionability": {"brief_a": 5, "brief_b": 8, "advantage": "Brief B"},
            "audience_focus": {"brief_a": 3, "brief_b": 8, "advantage": "Brief B"},
            "measurability": {"brief_a": 4, "brief_b": 9, "advantage": "Brief B"},
        },
        "brief_a_strengths": [
            "Creative campaign name",
            "Good channel diversity",
        ],
        "brief_b_strengths": [
            "Precise target audience with behavioral insights",
            "SMART objectives with clear numeric targets",
            "Strong single-minded proposition",
            "Complete RACI matrix",
            "Budget allocation with ROI projections",
        ],
        "recommendations_for_a": [
            "Add specific audience demographics and pain points",
            "Include measurable KPIs with numeric targets",
            "Rewrite the SMP to be truly single-minded",
            "Add competitive context and the 'why now'",
        ],
    }


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class QualityChecker:
    """Scores campaign briefs against best practices and catches common mistakes.

    Uses the Anthropic Claude API for intelligent analysis. Falls back to
    demo mode with sample results when no API key is configured.
    """

    _MIN_CALL_INTERVAL: float = 0.5

    def __init__(self) -> None:
        """Initialize the LLM provider. Activates demo mode if not configured."""
        self._last_call_time: float = 0.0
        if llm_provider.is_configured():
            self.demo_mode = False
            logger.info("QualityChecker initialized with %s", llm_provider.provider_display_name())
        else:
            self.demo_mode = True
            logger.info("QualityChecker initialized in DEMO mode (LLM provider not configured)")

    def _rate_limit(self) -> None:
        """Enforce a minimum interval between API calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._MIN_CALL_INTERVAL:
            time.sleep(self._MIN_CALL_INTERVAL - elapsed)
        self._last_call_time = time.time()

    def _call_claude(self, system: str, user_prompt: str, max_tokens: int = 4096) -> Optional[dict]:
        """Send a prompt to the configured LLM and return the parsed JSON response."""
        if self.demo_mode:
            return None

        self._rate_limit()
        try:
            raw_text = llm_provider.generate(
                system=system,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
            )
            result = _parse_json_response(raw_text)
            if result is None:
                logger.error("Could not parse JSON from LLM response.")
            return result
        except Exception as exc:
            logger.error("LLM API error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # 1. check_brief — full brief quality analysis
    # ------------------------------------------------------------------

    def check_brief(self, brief_text: str) -> dict:
        """Analyze a campaign brief and return a comprehensive quality report.

        Args:
            brief_text: The campaign brief as markdown or plain text.

        Returns:
            A dict containing overall_score, grade, dimension_scores,
            mistakes_found, strengths, improvement_suggestions,
            missing_sections, and smp_check.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning sample brief check results.")
            return _demo_check_brief()

        word_count = len(brief_text.split())
        logger.info("Checking brief quality (%d words)...", word_count)

        user_prompt = f"""Analyze the following campaign brief and return a JSON object with exactly these fields:

1. "overall_score": integer 1-10 (10 = perfect brief)
2. "dimension_scores": object with these keys, each an integer 1-10:
   - "clarity": Is the brief clear and unambiguous?
   - "specificity": Are audience, metrics, and deliverables specific?
   - "actionability": Can someone execute from this brief alone?
   - "audience_focus": Is the target audience well-defined with insights?
   - "measurability": Are KPIs specific and measurable?
3. "mistakes_found": array of objects, each with:
   - "mistake": name of the mistake (from the 9 common mistakes list)
   - "severity": "critical" / "warning" / "suggestion"
   - "description": what's wrong
   - "fix": how to fix it
4. "strengths": array of strings — what the brief does well
5. "improvement_suggestions": array of prioritized suggestions (most important first)
6. "missing_sections": array of section names from the 14-section framework that are absent or severely lacking
7. "smp_check": object with:
   - "has_smp": boolean — does the brief contain a Single-Minded Proposition?
   - "is_single_minded": boolean — is it truly one idea?
   - "issue": string describing any problem (empty string if none)

Additional context: The brief has {word_count} words. If it exceeds 1000 words, flag "Too long" as a mistake.

Here is the brief to analyze:

---
{brief_text}
---"""

        result = self._call_claude(QUALITY_CHECK_SYSTEM_PROMPT, user_prompt)

        if result is None:
            logger.warning("Falling back to demo results due to API failure.")
            return _demo_check_brief()

        # Ensure grade is derived from overall_score
        score = result.get("overall_score", 5)
        result["grade"] = _score_to_grade(score)
        return result

    # ------------------------------------------------------------------
    # 2. check_smp — focused SMP analysis
    # ------------------------------------------------------------------

    def check_smp(self, smp_text: str) -> dict:
        """Perform a focused quality check on a Single-Minded Proposition.

        Args:
            smp_text: The SMP text to evaluate.

        Returns:
            A dict with is_single_minded, has_and_also, word_count,
            clarity_score, and suggestions.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning sample SMP check results.")
            return _demo_check_smp()

        logger.info("Checking SMP: '%s'", smp_text[:80])

        # Quick local checks
        smp_lower = smp_text.lower()
        conjunctions = ["and", "also", "plus", "as well as"]
        has_and_also = any(
            re.search(r"\b" + re.escape(conj) + r"\b", smp_lower) for conj in conjunctions
        )
        word_count = len(smp_text.split())

        user_prompt = f"""Evaluate this Single-Minded Proposition (SMP) for a campaign brief.

SMP: "{smp_text}"

Return a JSON object with exactly these fields:
- "is_single_minded": boolean — does it communicate exactly ONE idea?
- "has_and_also": boolean — does it contain "and", "also", "plus", or "as well as"?
- "word_count": integer
- "clarity_score": integer 1-10 (10 = crystal clear to anyone)
- "suggestions": array of 3 improved alternative versions that are more single-minded and concise"""

        result = self._call_claude(SMP_CHECK_SYSTEM_PROMPT, user_prompt, max_tokens=1024)

        if result is None:
            logger.warning("Falling back to demo SMP results due to API failure.")
            return _demo_check_smp()

        # Override with local checks for accuracy
        result["has_and_also"] = has_and_also
        result["word_count"] = word_count
        return result

    # ------------------------------------------------------------------
    # 3. check_smart_objective — SMART framework check
    # ------------------------------------------------------------------

    def check_smart_objective(self, objective: str) -> dict:
        """Check whether an objective meets the SMART framework.

        Args:
            objective: The objective text to evaluate.

        Returns:
            A dict with is_smart, specific, measurable, achievable,
            relevant, time_bound (each with passes + feedback), and
            improved_version.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning sample SMART check results.")
            return _demo_check_smart()

        logger.info("Checking SMART objective: '%s'", objective[:80])

        user_prompt = f"""Evaluate this campaign objective against the SMART framework.

Objective: "{objective}"

Return a JSON object with exactly these fields:
- "is_smart": boolean — does it pass ALL five SMART criteria?
- "specific": object with "passes" (boolean) and "feedback" (string)
- "measurable": object with "passes" (boolean) and "feedback" (string)
- "achievable": object with "passes" (boolean) and "feedback" (string)
- "relevant": object with "passes" (boolean) and "feedback" (string)
- "time_bound": object with "passes" (boolean) and "feedback" (string)
- "improved_version": string — a rewritten version that passes all SMART criteria"""

        result = self._call_claude(SMART_CHECK_SYSTEM_PROMPT, user_prompt, max_tokens=1024)

        if result is None:
            logger.warning("Falling back to demo SMART results due to API failure.")
            return _demo_check_smart()

        return result

    # ------------------------------------------------------------------
    # 4. compare_briefs — head-to-head comparison
    # ------------------------------------------------------------------

    def compare_briefs(self, brief_a: str, brief_b: str) -> dict:
        """Compare two campaign briefs and determine which is stronger.

        Args:
            brief_a: First brief (markdown or plain text).
            brief_b: Second brief (markdown or plain text).

        Returns:
            A dict with winner, scores, summary, dimension_comparison,
            strengths for each, and recommendations.
        """
        if self.demo_mode:
            logger.info("Demo mode: returning sample comparison results.")
            return _demo_compare_briefs()

        logger.info("Comparing two briefs (%d words vs %d words)...",
                     len(brief_a.split()), len(brief_b.split()))

        user_prompt = f"""Compare these two campaign briefs and determine which is stronger.

Score each on the 5 quality dimensions (clarity, specificity, actionability, audience_focus, measurability) on a 1-10 scale.

Return a JSON object with exactly these fields:
- "winner": "Brief A" or "Brief B"
- "score_a": integer 1-10 overall score for Brief A
- "score_b": integer 1-10 overall score for Brief B
- "summary": string — 2-3 sentence explanation of the comparison
- "dimension_comparison": object with keys for each dimension, each containing:
  - "brief_a": integer 1-10
  - "brief_b": integer 1-10
  - "advantage": "Brief A" or "Brief B" or "Tie"
- "brief_a_strengths": array of strings
- "brief_b_strengths": array of strings
- "recommendations_for_a": array of suggestions to improve Brief A
- "recommendations_for_b": array of suggestions to improve Brief B

=== BRIEF A ===
{brief_a}

=== BRIEF B ===
{brief_b}"""

        result = self._call_claude(COMPARE_SYSTEM_PROMPT, user_prompt)

        if result is None:
            logger.warning("Falling back to demo comparison results due to API failure.")
            return _demo_compare_briefs()

        return result


# ---------------------------------------------------------------------------
# CLI test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Campaign Brief Quality Checker — Test Run")
    print("=" * 60)

    checker = QualityChecker()

    if checker.demo_mode:
        print("\n[DEMO MODE] LLM provider not configured. Showing sample results.\n")
    else:
        print(f"\n[LIVE MODE] Using {llm_provider.provider_display_name()}.\n")

    # --- Test 1: Full brief check ---
    sample_brief = """# Spring Product Launch Campaign

## Objective
Increase sign-ups for our new inventory tool.

## Target Audience
Small business owners who need help managing inventory.

## Key Messages
1. Save time with automated inventory tracking
2. Never run out of stock again
3. Affordable pricing for small teams

## SMP
Our tool saves you time and also reduces costs across your entire business.

## Channel Plan
- Email marketing to existing users
- Social media ads on Facebook and Instagram
- Blog post on company website
- Partner webinar series

## Timeline
- Week 1-2: Awareness phase
- Week 3-4: Launch and activation
- Week 5-8: Sustain and optimize

## Content Deliverables
- 3 email templates
- 5 social media creatives
- 1 landing page
- 1 blog post
- Webinar slide deck
"""

    print("-" * 60)
    print("TEST 1: Full Brief Quality Check")
    print("-" * 60)
    result = checker.check_brief(sample_brief)
    print(f"  Overall Score: {result['overall_score']}/10 (Grade: {result['grade']})")
    print(f"  Dimension Scores:")
    for dim, score in result["dimension_scores"].items():
        print(f"    {dim}: {score}/10")
    print(f"  Mistakes Found: {len(result['mistakes_found'])}")
    for m in result["mistakes_found"]:
        print(f"    [{m['severity'].upper()}] {m['mistake']}: {m['description'][:80]}...")
    print(f"  Strengths: {len(result['strengths'])}")
    for s in result["strengths"]:
        print(f"    + {s}")
    print(f"  Missing Sections: {result['missing_sections']}")
    print(f"  SMP Check: single-minded={result['smp_check']['is_single_minded']}")

    # --- Test 2: SMP check ---
    print("\n" + "-" * 60)
    print("TEST 2: SMP Quality Check")
    print("-" * 60)
    smp = "Our tool saves you time and also reduces costs across your entire business."
    smp_result = checker.check_smp(smp)
    print(f"  SMP: \"{smp}\"")
    print(f"  Single-minded: {smp_result['is_single_minded']}")
    print(f"  Has and/also: {smp_result['has_and_also']}")
    print(f"  Word count: {smp_result['word_count']}")
    print(f"  Clarity score: {smp_result['clarity_score']}/10")
    print(f"  Suggestions:")
    for s in smp_result["suggestions"]:
        print(f"    -> {s}")

    # --- Test 3: SMART objective check ---
    print("\n" + "-" * 60)
    print("TEST 3: SMART Objective Check")
    print("-" * 60)
    objective = "Increase sign-ups for our new inventory tool."
    smart_result = checker.check_smart_objective(objective)
    print(f"  Objective: \"{objective}\"")
    print(f"  Is SMART: {smart_result['is_smart']}")
    for dim_name in ("specific", "measurable", "achievable", "relevant", "time_bound"):
        dim = smart_result[dim_name]
        status = "PASS" if dim["passes"] else "FAIL"
        print(f"    [{status}] {dim_name}: {dim['feedback']}")
    print(f"  Improved: {smart_result['improved_version']}")

    # --- Test 4: Brief comparison ---
    print("\n" + "-" * 60)
    print("TEST 4: Brief Comparison")
    print("-" * 60)
    brief_b = """# AI Listing Enhancement Campaign

## Background
Competitor X launched AI-powered listings in Q1 2026, gaining 8% market share
among power sellers. Our seller NPS dropped 12 points. We must respond now.

## Objective
Increase AI Listing adoption among top-tier sellers by 30% (from 15% to 19.5%)
within 90 days of campaign launch.

## Target Audience
Professional e-commerce sellers aged 28-45 who list 50+ items/month,
currently using manual listing workflows, frustrated by time spent on
product photography and description writing.

## Key Insight
Power sellers don't want another tool — they want their weekends back.

## SMP
List in seconds, not hours.

## Success Metrics
- Primary: 30% increase in AI Listing feature adoption (15% -> 19.5%)
- Secondary: 20% reduction in avg. listing creation time
- Tertiary: Seller NPS improvement of +5 points within 90 days

## Approvals
| Role | Person | Responsibility |
|------|--------|---------------|
| PMM Lead | Sarah | Accountable |
| Product Manager | Mike | Consulted |
| Design Lead | Priya | Responsible |
| VP Marketing | James | Informed |
"""
    compare_result = checker.compare_briefs(sample_brief, brief_b)
    print(f"  Winner: {compare_result['winner']}")
    print(f"  Brief A score: {compare_result['score_a']}/10")
    print(f"  Brief B score: {compare_result['score_b']}/10")
    print(f"  Summary: {compare_result['summary']}")

    print("\n" + "=" * 60)
    print("All tests completed.")
    print("=" * 60)
