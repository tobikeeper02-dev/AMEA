# AMEA

A lean Streamlit front end that sends every market-entry question straight to ChatGPT. Nothing is cached or prewritten—the UI collects your OpenAI credentials plus engagement inputs and then renders the model’s replies.

## Quickstart
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the app:
   ```bash
   streamlit run streamlit_app.py
   ```
3. Paste your OpenAI API key in the sidebar (or set `OPENAI_API_KEY` beforehand), pick a company, industry, and comma-separated markets, then click **Run analysis**.

## ChatGPT configuration
- **API key**: required. Provide via sidebar or `OPENAI_API_KEY`.
- **Base URL**: optional proxy override via sidebar or `OPENAI_BASE_URL`.
- **Model**: defaults to `gpt-5-nano`; override with `AMEA_OPENAI_MODEL` or the sidebar field.
- **Temperature**: defaults to `0.2` but is ignored automatically for models that do not support it.

Use the **Run API health check** button in the sidebar to verify connectivity. A short confirmation sentence from ChatGPT proves that requests are succeeding.

## What the app generates
- **Company brief**: concise overview of the company and industry positioning.
- **Market snapshots**: per-country JSON turned into PESTEL bullets, recommendations, and cited sources when the model supplies them.

If ChatGPT returns malformed JSON, the raw response is still displayed so you can retry with clearer prompts. There are no bundled datasets—every result comes from the model at request time.
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
export AMEA_OPENAI_TEMPERATURE="0.2"        # ignored by gpt-5-nano
```

**In-app configuration:** Use the **OpenAI configuration** section in the Streamlit sidebar to paste your API key, set a custom
base URL (for Azure/OpenAI proxies), adjust the model, and tweak temperature for models that expose that control (gpt-5-nano
always runs at its default setting). The sidebar status indicator confirms when ChatGPT is active, and the **Test API** button
runs a quick health check so you can verify connectivity without leaving the app.

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
