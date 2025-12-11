# AMEA Next

A fresh implementation of the AMEA market analysis app that relies entirely on live ChatGPT output. It collects engagement inputs, queries the OpenAI API for company briefs and per-market PESTEL insights, and renders the results in Streamlit.

## Quick start
1. Install dependencies:
   ```bash
   pip install -r new_app/requirements.txt
   ```
2. Provide your OpenAI credentials (gpt-5-nano by default):
   ```bash
   export OPENAI_API_KEY="your-key"
   export AMEA_OPENAI_MODEL="gpt-5-nano"
   export AMEA_OPENAI_TEMPERATURE="0.2"  # optional
   export AMEA_OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
   ```
3. Run the Streamlit app from the repo root:
   ```bash
   streamlit run new_app/streamlit_app.py
   ```

Use the sidebar to adjust credentials, run a quick health check, and generate company-aware market analyses. The app never reads bundled indicator data—everything comes from the ChatGPT API.
