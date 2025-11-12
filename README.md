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

The app lets you configure the engagement (company, industry, target markets, and strategic priorities), executes an automated research synthesis, and renders comparative analytics (PESTEL narratives, scoring radar, and recommended entry mode). You can also download an auto-generated Word document summarizing the findings.

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
