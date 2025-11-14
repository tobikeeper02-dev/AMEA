# AMEA

AMEA (Automated Market Entry Analysis) is an AI-first research assistant that builds market-entry briefings directly from OpenAI's
ChatGPT Responses API. The Streamlit dashboard collects your engagement inputs, calls ChatGPT for every insight, and assembles a
board-ready report without relying on any stored indicator library.

## Getting started

### Prerequisites

Create and activate a Python 3.10+ environment, then install the project dependencies:

```bash
pip install -r requirements.txt
```

### Run the Streamlit workspace

Launch the interactive dashboard locally:

```bash
streamlit run streamlit_app.py
```

### Enable ChatGPT-powered narratives

Every qualitative and scoring output now comes from ChatGPT. Provide credentials before launching the Streamlit app, or paste them
directly into the sidebar controls once the app is running.

**Environment setup (optional but recommended for local development):**

```bash
export OPENAI_API_KEY="your-openai-key"
# Optional overrides
export AMEA_OPENAI_MODEL="gpt-5-nano"        # default model
export AMEA_OPENAI_TEMPERATURE="0.2"        # keep outputs focused
```

**In-app configuration:** Use the **OpenAI configuration** section in the Streamlit sidebar to paste your API key, set a custom
base URL (for Azure/OpenAI proxies), adjust the model, and tweak temperature. The sidebar status indicator confirms when ChatGPT
is active, and the **Test API** button runs a quick health check so you can verify connectivity without leaving the app.

If the key is missing the app will halt—there is no longer a heuristic or cached fallback.

### What the workflow does

1. **Engagement capture** – you provide the company, industry, strategic priorities, use case, and comma-separated country list.
2. **Company brief generation** – ChatGPT produces a tailored summary of the client’s business model, differentiators, and
   watchpoints aligned to your priorities.
3. **Market-specific calls** – for each country, ChatGPT returns PESTEL bullets, quantitative-style scores, recent signals,
   entry guidance, mitigation ideas, and source citations. Every run is generated from scratch.
4. **Visualisation & export** – the Streamlit UI renders scorecards, radar charts, detailed PESTEL tables, and offers a
   DOCX download that mirrors the on-screen content.

Because everything is generated live, rerunning the same scenario can surface refreshed commentary as macro conditions evolve.

## Architecture overview

```
AMEA/
├── streamlit_app.py         # Streamlit front-end with ChatGPT status + health check
└── src/amea/
    ├── pipeline.py          # Orchestrates company brief + per-market ChatGPT calls
    ├── analysis/scoring.py  # Data structures for model-returned scores
    ├── research/llm.py      # OpenAI client helpers and prompt builders
    └── report/              # Export utilities (DOCX)
```

No offline datasets are bundled—the assistant depends entirely on the ChatGPT API responses you authorise.

## Roadmap

* Add optional retrieval plugins (news search, World Bank APIs) to feed verified facts into the prompts.
* Extend the export pipeline with PPTX and HTML dashboards.
* Introduce collaborative annotations so teams can capture client feedback directly in the workspace.
