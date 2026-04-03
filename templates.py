"""
Pre-built brief templates for common campaign types.
Each template pre-fills the Brief Builder with relevant defaults.
"""


class TemplateManager:
    """Manages campaign brief templates."""

    TEMPLATES = [
        {
            "template_id": "product_launch",
            "name": "Product Launch (Tier 1)",
            "description": "Full-scale launch campaign for a new product or major feature. Includes broad channel mix and high-visibility tactics.",
            "tier": 1,
            "icon": "🚀",
            "defaults": {
                "campaign_name": "[Feature Name] Launch Campaign",
                "background": (
                    "We're launching [feature] to address [market need]. "
                    "Competitors [X] and [Y] have similar offerings, but our approach "
                    "differentiates through [key differentiator]. Market research indicates "
                    "[data point] demand among our target segment."
                ),
                "objective": "Achieve [X]% adoption among [segment] within [timeframe]",
                "target_audience": (
                    "Current sellers who [behavior], new sellers looking for [need], "
                    "and adjacent segments exploring [category]"
                ),
                "channels": {
                    "email": 30,
                    "in_app": 25,
                    "social": 20,
                    "blog": 15,
                    "pr": 10,
                },
                "tier": 1,
                "kpis": [
                    "Adoption rate within target segment",
                    "Activation rate (first meaningful use)",
                    "Channel-specific conversion rates",
                    "Awareness lift (pre/post survey)",
                ],
                "timeline": "8-12 weeks",
            },
        },
        {
            "template_id": "feature_update",
            "name": "Feature Update (Tier 2)",
            "description": "Lighter brief for incremental feature updates targeting the existing user base. Fewer channels, focused messaging.",
            "tier": 2,
            "icon": "🔧",
            "defaults": {
                "campaign_name": "[Feature Name] Update Announcement",
                "background": (
                    "We're releasing an update to [existing feature] based on user feedback. "
                    "Key improvements include [improvement 1] and [improvement 2]. "
                    "This addresses [X]% of support tickets related to [pain point]."
                ),
                "objective": "Drive awareness and adoption of the updated feature among existing users within [timeframe]",
                "target_audience": (
                    "Existing users currently using [feature], "
                    "particularly those who have submitted feedback or support requests"
                ),
                "channels": {
                    "in_app": 40,
                    "email": 35,
                    "blog": 25,
                },
                "tier": 2,
                "kpis": [
                    "Feature adoption rate among existing users",
                    "Reduction in related support tickets",
                    "User satisfaction score (post-update)",
                ],
                "timeline": "4-6 weeks",
            },
        },
        {
            "template_id": "competitive_response",
            "name": "Competitive Response",
            "description": "Rapid-response campaign to counter a competitor move. Emphasizes differentiation and market-share defense.",
            "tier": 1,
            "icon": "⚔️",
            "defaults": {
                "campaign_name": "Competitive Response: [Competitor Move]",
                "background": (
                    "[Competitor] has announced [competitive move], which directly impacts "
                    "our positioning in [market segment]. Their approach [strengths/weaknesses]. "
                    "Our differentiation lies in [key advantages]. Customer sentiment data "
                    "shows [relevant insight]."
                ),
                "objective": "Defend market share and reinforce differentiation among [segment] by clearly communicating our unique value",
                "target_audience": (
                    "Current customers at risk of switching, prospects evaluating alternatives, "
                    "and industry analysts covering the space"
                ),
                "channels": {
                    "email": 25,
                    "social": 25,
                    "pr": 20,
                    "blog": 15,
                    "paid_search": 15,
                },
                "tier": 1,
                "kpis": [
                    "Customer retention rate in affected segment",
                    "Share of voice vs. competitor",
                    "Win/loss ratio changes",
                    "Analyst sentiment shift",
                ],
                "timeline": "2-4 weeks (accelerated)",
            },
        },
        {
            "template_id": "seasonal_campaign",
            "name": "Seasonal Campaign",
            "description": "Time-bound campaign aligned with seasonal buying patterns to maximize GMV during peak periods.",
            "tier": 1,
            "icon": "📅",
            "defaults": {
                "campaign_name": "[Season/Event] Campaign [Year]",
                "background": (
                    "Historical data shows [X]% increase in buying activity during [season/event]. "
                    "Last year's campaign drove [results]. Key categories include [category 1] "
                    "and [category 2]. Buyer behavior shifts toward [pattern] during this period."
                ),
                "objective": "Increase GMV by [X]% during [peak period] compared to [baseline period]",
                "target_audience": (
                    "Active buyers with purchase history in seasonal categories, "
                    "lapsed buyers from previous seasonal campaigns, "
                    "and new prospects searching for [seasonal terms]"
                ),
                "channels": {
                    "email": 30,
                    "social": 25,
                    "paid_search": 25,
                    "in_app": 20,
                },
                "tier": 1,
                "kpis": [
                    "GMV during campaign period vs. baseline",
                    "Conversion rate by channel",
                    "Average order value",
                    "New buyer acquisition during period",
                ],
                "timeline": "6-8 weeks (including pre-campaign teasers)",
            },
        },
        {
            "template_id": "re_engagement",
            "name": "Re-engagement Campaign",
            "description": "Win-back campaign targeting dormant users with personalized incentives and messaging to drive reactivation.",
            "tier": 2,
            "icon": "🔄",
            "defaults": {
                "campaign_name": "[Segment] Re-engagement Campaign",
                "background": (
                    "Analysis shows [X]% of users who were active [timeframe] ago have become dormant. "
                    "Common drop-off reasons include [reason 1], [reason 2], and [reason 3]. "
                    "Previous re-engagement efforts achieved [Y]% reactivation rate."
                ),
                "objective": "Reactivate [X]% of inactive users (defined as no activity in [timeframe]) within [campaign duration]",
                "target_audience": (
                    "Dormant users who were previously active but have not engaged in [timeframe], "
                    "segmented by last activity type and lifetime value"
                ),
                "channels": {
                    "email": 40,
                    "in_app": 30,
                    "paid_retargeting": 30,
                },
                "tier": 2,
                "kpis": [
                    "Reactivation rate (dormant to active)",
                    "Time to first action after re-engagement",
                    "Retained reactivation at 30/60/90 days",
                    "Cost per reactivation by channel",
                ],
                "timeline": "4-6 weeks",
            },
        },
        {
            "template_id": "brand_awareness",
            "name": "Brand Awareness",
            "description": "Top-of-funnel campaign to increase brand recall and consideration among a broader audience.",
            "tier": 1,
            "icon": "📣",
            "defaults": {
                "campaign_name": "[Brand/Initiative] Awareness Campaign",
                "background": (
                    "Current brand awareness in [target market] sits at [X]% (aided recall). "
                    "Key perception gaps include [gap 1] and [gap 2]. "
                    "Competitors [A] and [B] hold [Y]% and [Z]% awareness respectively. "
                    "Research indicates opportunity to position around [theme]."
                ),
                "objective": "Increase brand recall by [X]% and consideration by [Y]% among [target audience] within [timeframe]",
                "target_audience": (
                    "Broader market audience including potential buyers unfamiliar with the brand, "
                    "industry professionals, and decision-makers in [target verticals]"
                ),
                "channels": {
                    "social": 30,
                    "video": 25,
                    "pr": 20,
                    "events": 15,
                    "paid": 10,
                },
                "tier": 1,
                "kpis": [
                    "Aided and unaided brand recall (survey)",
                    "Brand consideration score",
                    "Share of voice in target channels",
                    "Content engagement rate",
                    "Earned media impressions",
                ],
                "timeline": "10-16 weeks",
            },
        },
    ]

    @classmethod
    def get_all_templates(cls) -> list:
        """Returns list of all available template dicts."""
        return cls.TEMPLATES

    @classmethod
    def get_template(cls, template_id: str) -> dict:
        """Returns a single template by its template_id.

        Args:
            template_id: The unique identifier for the template.

        Returns:
            The matching template dict.

        Raises:
            ValueError: If no template matches the given ID.
        """
        for template in cls.TEMPLATES:
            if template["template_id"] == template_id:
                return template
        raise ValueError(
            f"Template '{template_id}' not found. "
            f"Available templates: {[t['template_id'] for t in cls.TEMPLATES]}"
        )
