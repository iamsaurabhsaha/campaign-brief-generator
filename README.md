# Campaign Brief Generator

**Live App:** [campaign-brief-generator.streamlit.app](https://campaign-brief-generator.streamlit.app)

An AI-powered tool that helps Product Marketing Managers create comprehensive, high-quality campaign briefs in minutes instead of hours. Built with Streamlit and the Anthropic Claude API.

## What It Does

This tool guides you through creating a complete campaign brief using a 6-step wizard with AI assistance at every stage. It can also check the quality of existing briefs and generate creative concepts.

### 3 Core Features

**1. AI Brief Builder** - A 6-step guided wizard that walks you through creating a complete campaign brief:

| Step | What You Do |
|------|-------------|
| **Setup** | Name your campaign, select launch tier (Tier 0-3), choose brief type |
| **Strategy** | Define background/context, objective (with SMART formatting), target audience |
| **Messaging** | Key insight, positioning statements, key messages, single-minded proposition |
| **Execution** | Channel plan, content deliverables, timeline, budget allocation |
| **Governance** | KPIs/success metrics, RACI matrix, approvals checklist |
| **Review & Export** | Preview full brief, download as Word (.docx) or Markdown, generate creative brief |

Every field has AI-powered buttons:
- **"Help Me Write"** - Expands your notes into full paragraphs
- **"Proofread"** - Refines grammar, clarity, and tone
- **"Generate"** - Creates content from scratch based on your context
- **"Make it SMART"** - Reformats objectives into Specific, Measurable, Achievable, Relevant, Time-bound goals
- **"Use This"** - Accept AI suggestions into your brief

**2. Brief Quality Checker** - Paste an existing brief or upload a document (PDF, Word, TXT) and get:
- Overall quality score (1-10) with letter grade
- Radar chart of 5 dimensions (Clarity, Specificity, Actionability, Audience Focus, Measurability)
- Issues found with severity levels (Critical, Warning, Suggestion)
- Strengths identified
- Prioritized improvement recommendations

**3. Creative Concepts Generator** - Paste or upload a completed brief, then:
- Generate 1-5 creative concept directions (theme, headline, tagline, tone, sample copy, appeal score)
- Generate a 5-email drip campaign sequence
- Download concepts and email sequences as Word documents

## Demo Mode

The app works **without an API key** using sample data. Every feature is functional in demo mode so you can explore the full workflow before adding your API key.

## Getting Started

### Prerequisites

- Python 3.9+
- An Anthropic API key (optional - app works in demo mode without one)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/iamsaurabhsaha/campaign-brief-generator.git
   cd campaign-brief-generator
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API key (optional):**

   ```bash
   cp .env.example .env
   # Edit .env and set your preferred LLM provider + API key
   # Supports: Anthropic, OpenAI, Google Gemini, AWS Bedrock, Azure OpenAI, Ollama
   ```

4. **Run the app:**

   ```bash
   streamlit run app.py
   ```

   The app opens at `http://localhost:8501`

### Deploy to Streamlit Cloud (Get a shareable link)

1. Push this repo to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add your `ANTHROPIC_API_KEY` in Settings > Secrets
5. Deploy - you'll get a public URL to share

## How to Use

### Creating Your First Brief

1. Open the app and click the **"AI Brief Builder"** tab
2. **Step 1 (Setup):** Enter a campaign name like "AI Magic Listing Launch", select Tier 1, choose Campaign Brief
3. **Step 2 (Strategy):** Describe the background, or click "Help Me Write" to get AI assistance. Upload supporting docs if you have them. Click "Make it SMART" to refine your objective.
4. **Step 3 (Messaging):** Click "Extract Insight" to generate your key insight, then "Generate Positioning", "Generate Key Messages", and "Generate SMP"
5. **Step 4 (Execution):** Click "Generate Channel Plan", "Generate Deliverables", and "Generate Timeline" to create your execution plan
6. **Step 5 (Governance):** Click "Generate KPIs" and "Generate RACI" for success metrics and responsibility matrix
7. **Step 6 (Review):** Preview your complete brief, download as Word document, or generate a Creative Brief

### Checking an Existing Brief

1. Click the **"Brief Quality Checker"** tab
2. Paste your brief text or upload a document
3. Select the brief type and launch tier
4. Click "Check Quality" for AI-powered analysis

### Generating Creative Concepts

1. Click the **"Creative Concepts"** tab
2. Paste your brief text or upload a document
3. Choose how many concepts (1-5)
4. Click "Generate Concepts" to see creative directions
5. Click "Generate Email Sequence" for a 5-email drip campaign
6. Download as Word documents

## Project Structure

```
campaign-brief-generator/
├── app.py                 # Streamlit dashboard (3 tabs, 6-step wizard)
├── brief_generator.py     # Claude API - generates all 14 brief sections
├── quality_checker.py     # AI-powered brief quality analysis
├── creative_engine.py     # Creative concepts + email sequence generation
├── templates.py           # Pre-built campaign templates
├── config.py              # Settings, constants, color scheme
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
└── README.md
```

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/) with custom CSS (Inter font, light theme)
- **AI:** [Anthropic Claude API](https://www.anthropic.com/) (claude-sonnet-4-20250514) — also supports OpenAI, Google Gemini, AWS Bedrock, Azure OpenAI, and Ollama via `.env` config
- **Charts:** Plotly
- **Export:** python-docx (Word documents)
- **Design:** E-commerce-inspired color scheme (Blue #0064D2, Red #E53238, Yellow #F5AF02, Green #86B817)

## Brief Framework

The tool follows the industry-standard **14-section campaign brief framework** used by leading PMM teams:

1. Campaign Name
2. Background/Context
3. Objective (SMART)
4. Target Audience
5. Key Insight
6. Positioning Statement (Short + Detailed)
7. Key Messages
8. Single-Minded Proposition (SMP)
9. Channel Plan
10. Content Deliverables
11. Timeline
12. Budget
13. Success Metrics/KPIs
14. RACI Matrix + Approvals

### Launch Tier System

| Tier | Scale | Brief Depth |
|------|-------|-------------|
| Tier 0 | Company-defining (new platform) | Full brief + war room |
| Tier 1 | Major feature launch | Full brief |
| Tier 2 | Enhancement or update | Light brief |
| Tier 3 | Bug fix / minor | No brief needed |

## License

MIT License - feel free to use and modify.
