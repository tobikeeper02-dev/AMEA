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

The assistant can call OpenAI's ChatGPT to synthesize PESTEL narratives and rewrite recent news highlights. Provide credentials before launching the Streamlit app:

```bash
export OPENAI_API_KEY="your-openai-key"
# Optional overrides
export AMEA_OPENAI_MODEL="gpt-4o-mini"        # or another Responses API model
export AMEA_OPENAI_TEMPERATURE="0.2"          # keep outputs focused
```

The integration automatically falls back to the packaged heuristic content if the credentials are missing or an API error occurs.

The app lets you configure the engagement (company, industry, target markets, strategic priorities, and desired use case), executes an automated research synthesis, and renders comparative analytics (PESTEL narratives, scoring radar, and recommended entry mode). Each market includes citation-style source lists so you can trace the input data. You can also download an auto-generated Word document summarizing the findings.

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
