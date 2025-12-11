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
