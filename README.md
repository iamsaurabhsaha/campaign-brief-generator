# AI Campaign Brief Generator

**Live App:** [campaign-brief-generator.streamlit.app](https://campaign-brief-generator.streamlit.app)

An AI-powered tool that helps Product Marketing Managers create comprehensive, high-quality campaign briefs in minutes. Built with Streamlit and powered by Claude API.

## What It Does

A 6-step guided wizard that walks you through creating a complete campaign brief with AI assistance at every stage — from strategy to export.

| Step | What You Do |
|------|-------------|
| **Setup** | Name your campaign, select launch tier (Full Brief or Light Brief) |
| **Strategy** | Define background/context, upload supporting documents, set objective (with SMART formatting), define target audience |
| **Messaging** | Key insight, positioning statements, key messages, single-minded proposition (SMP) |
| **Execution** | Channel plan, content deliverables, campaign timeline, budget allocation |
| **Governance** | KPIs/success metrics, RACI matrix |
| **Review & Export** | Preview full brief, download as Word (.docx) |

### AI-Powered Buttons

Every section has AI assistance:

| Button | What It Does |
|--------|-------------|
| **Help Me Write** | Expands your notes into full paragraphs using campaign context |
| **Proofread** | Refines grammar, clarity, and tone — shows "Looks good" if no changes needed |
| **Generate** | Creates content from scratch based on all previously filled sections |
| **Make it SMART** | Reformats objectives into Specific, Measurable, Achievable, Relevant, Time-bound goals |
| **Extract Insight** | Pulls the key human insight from your background and audience |
| **Insert** | Accept AI suggestions into your brief |

### Smart Features

- **Context chaining** — each generation step uses all previously filled sections as context
- **Coherence check** — warns if your campaign name doesn't match the background/uploaded documents
- **Proofread approval** — when text is already well-written, shows "Looks good" instead of returning near-identical text
- **Validation** — requires context before generating (e.g., background must be filled before generating objectives)
- **No specific dates** — objectives and timelines use relative timeframes ("within 90 days of launch"), never calendar dates
- **Green checkmarks** — field labels show ✓ when filled so you can track progress at a glance
- **Bookmarkable URLs** — each step has its own URL (`?step=strategy`, `?step=messaging`, etc.)

### Word Document Export

The exported .docx includes:
- Professional formatting (Calibri 11pt, 1.15 line spacing, narrow margins)
- Page border
- Numbered tables with centered headers for Channel Plan, Timeline, KPIs, RACI
- Clean markdown-to-Word conversion (bold text, no markdown artifacts)
- Formatted budget with $ sign and commas

## Demo Mode

The app works **without an API key** using sample data. Every feature is functional in demo mode so you can explore the full workflow.

## Getting Started

### Prerequisites

- Python 3.9+
- An API key from a supported LLM provider (optional — app works in demo mode)

### Installation

```bash
git clone https://github.com/iamsaurabhsaha/campaign-brief-generator.git
cd campaign-brief-generator
pip install -r requirements.txt
```

### Add your API key (optional)

```bash
cp .env.example .env
# Edit .env and set your preferred LLM provider + API key
```

Supported providers: Anthropic, OpenAI, Google Gemini, AWS Bedrock, Azure OpenAI, Ollama

### Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

### Deploy to Streamlit Cloud

1. Push to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Add your API key in Settings > Secrets
5. Deploy

## Project Structure

```
campaign-brief-generator/
├── app.py                 # Streamlit app (6-step wizard, custom CSS)
├── brief_generator.py     # LLM API — generates all brief sections
├── llm_provider.py        # Multi-provider LLM abstraction layer
├── quality_checker.py     # Brief quality analysis
├── creative_engine.py     # Creative concepts generation
├── templates.py           # Pre-built campaign templates
├── config.py              # Constants and configuration
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
└── README.md
```

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/) with custom CSS
- **AI:** [Anthropic Claude API](https://www.anthropic.com/) (claude-sonnet-4-6) — also supports OpenAI, Google Gemini, AWS Bedrock, Azure OpenAI, and Ollama
- **Export:** python-docx (Word documents)
- **Charts:** Plotly (budget allocation pie chart)

## Brief Framework

Follows the industry-standard **14-section campaign brief framework**:

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
14. RACI Matrix

### Launch Tiers

| Tier | Scale | Brief Depth |
|------|-------|-------------|
| **Full Brief** | Major launch or new feature | All 14 sections required |
| **Light Brief** | Enhancement or update | Key sections only (Background, Objective, Key Messages, Deliverables) |

## Built By

**Saurabh Saha** — [GitHub](https://github.com/iamsaurabhsaha) · [LinkedIn](https://www.linkedin.com/in/iamsaurabhsaha/) · [saurabhsaha700@gmail.com](mailto:saurabhsaha700@gmail.com)

## License

MIT License
