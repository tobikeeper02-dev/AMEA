# AMEA

AMEA (Automated Market Entry Analysis) is an AI-augmented research assistant that helps consultants and students evaluate international expansion opportunities. The current prototype ships with a Streamlit dashboard, heuristic analysis engine, and report export workflow so you can compare markets in minutes.

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

The assistant can call OpenAI's ChatGPT to synthesize PESTEL narratives and rewrite recent news highlights. Provide credentials before launching the Streamlit app, or paste them directly into the sidebar controls once the app is running.

**Environment setup (optional but recommended for local development):**

```bash
export OPENAI_API_KEY="your-openai-key"
# Optional overrides
export AMEA_OPENAI_MODEL="gpt-4o-mini"        # or another Responses API model
export AMEA_OPENAI_TEMPERATURE="0.2"          # keep outputs focused
```

**In-app configuration:** Use the **OpenAI configuration** section in the Streamlit sidebar to paste your API key, set a custom base URL (for Azure/OpenAI proxies), adjust the model, and tweak temperature. The sidebar status indicator will confirm when ChatGPT is active.

The integration automatically falls back to the packaged heuristic content if the credentials are missing or an API error occurs.

The app lets you configure the engagement (company, industry, target markets, strategic priorities, and desired use case), executes an automated research synthesis, and renders comparative analytics (PESTEL narratives, scoring radar, and recommended entry mode). Each market includes citation-style source lists so you can trace the input data. You can also download an auto-generated Word document summarizing the findings.

### Company- and industry-aware insights

When ChatGPT is enabled, AMEA first asks the model to craft a company and industry brief that captures business-model nuances, regulatory watchpoints, and strategic levers tied to your stated priorities. That context is injected into each country’s PESTEL request so the resulting commentary addresses the specific organisation and sector rather than repeating generic guidance. The Streamlit dashboard surfaces this brief in a dedicated “Company & industry intelligence” card, and the DOCX export mirrors the same content at the top of the report.

If ChatGPT is unavailable, AMEA still generates a deterministic company brief based on the provided inputs so the rest of the pipeline has a clear strategic frame of reference.

## Architecture overview

```
AMEA/
├── streamlit_app.py         # Streamlit front-end
├── data/
│   └── country_indicators.json  # Curated macro indicators and narratives
└── src/amea/
    ├── pipeline.py              # Orchestrates research → analysis → export
    ├── research/                # Data access layer (API stubs, loaders)
    ├── analysis/                # Scoring, PESTEL heuristics, recommendations
    └── report/                  # Export utilities (DOCX, future formats)
```

The current version uses packaged indicator data to simulate automated research. These modules are structured so they can be swapped with live API integrations (World Bank, IMF, etc.) and generative AI calls in future iterations.

## Roadmap

* Integrate real-time data sources and LLM-generated context.
* Expand framework coverage (Porter’s Five Forces, VRIO) and factor weighting.
* Add FastAPI backend for programmatic access and authentication.
* Support additional export formats (PDF, PPTX) and richer visualizations.
