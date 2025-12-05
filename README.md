# AMEA (Rebuilt)

This version focuses on reliability and simplicity: every analysis runs directly through the OpenAI ChatGPT API. Nothing is prewritten or cached. Provide your API key and the app returns engagement-specific briefs and PESTEL-style snapshots.

## Quickstart
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```
3. In the sidebar, paste your OpenAI API key (and optional base URL/model). Choose a company, industry, target markets, and priorities, then click **Run analysis**.

## OpenAI settings
- **API key**: required. Set `OPENAI_API_KEY` in your environment or paste it into the sidebar.
- **Model**: defaults to `gpt-5-nano`. Override with `AMEA_OPENAI_MODEL` or the sidebar field.
- **Base URL**: leave blank for api.openai.com; set `OPENAI_BASE_URL` to route through a proxy.
- **Temperature**: defaults to `0.2`; ignored by some smaller models.

Use the **Run API health check** button to confirm connectivity before generating analyses.

## What gets generated
- Company brief: 3-sentence overview tuned to your company and industry.
- Market insights for each country you list: JSON-driven PESTEL bullets, recommendations, and cited sources when the model provides them.

## Troubleshooting
- If you see configuration errors, ensure the API key is set and that your model choice exists in your OpenAI account.
- If ChatGPT returns invalid JSON, the app will still show whatever text the model produced so you can retry.
- The app avoids heavy dependencies to prevent import issues; if you prefer additional libraries, add them to `requirements.txt` and reinstall.
