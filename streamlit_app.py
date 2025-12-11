"""Streamlit UI for the ChatGPT-driven AMEA analysis pipeline."""

from typing import List
import sys
from pathlib import Path


def _insert_repo_paths() -> None:
    """Ensure the in-repo package is importable even when not installed."""
    current = Path(__file__).resolve().parent
    candidates = [current, current / "src", current.parent / "src"]
    for path in candidates:
        if path.exists():
            as_str = str(path)
            if as_str not in sys.path:
                sys.path.insert(0, as_str)


_insert_repo_paths()

import streamlit as st

from amea.pipeline import AnalysisResult, generate_analysis
from amea.research.llm import (
    ChatGPTConfig,
    ChatGPTNotConfiguredError,
    is_chatgpt_configured,
    run_healthcheck,
)


st.set_page_config(page_title="AMEA – ChatGPT Market Analysis", layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_markets(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _render_status(config: ChatGPTConfig) -> None:
    if is_chatgpt_configured(config):
        st.success("ChatGPT is configured and will be used for this session.")
    else:
        st.warning("No OpenAI API key detected. Add one below to run live analyses.")

    if st.button("Run API health check"):
        st.info(run_healthcheck(config))


def _render_market_cards(result: AnalysisResult) -> None:
    for market in result.markets:
        with st.expander(market.country):
            st.markdown(f"**Summary:** {market.summary or 'No summary returned.'}")
            if market.recommendations:
                st.markdown("**Recommendations:**")
                for rec in market.recommendations:
                    st.write(f"- {rec}")
            if market.pestel:
                st.markdown("**PESTEL**")
                cols = st.columns(3)
                for idx, (dimension, bullets) in enumerate(market.pestel.items()):
                    with cols[idx % 3]:
                        st.markdown(f"**{dimension}**")
                        for bullet in bullets or []:
                            st.write(f"- {bullet}")
            if market.sources:
                st.markdown("**Sources:**")
                for source in market.sources:
                    st.write(f"- {source}")
            if market.raw_response:
                st.caption("Raw ChatGPT output")
                st.code(market.raw_response, language="json")


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("AMEA – Automated Market Entry (ChatGPT-powered)")
    st.write(
        "Every run calls ChatGPT directly to generate company briefs and market-specific "
        "PESTEL analysis. No cached datasets or preset answers are used."
    )

    with st.sidebar:
        st.header("ChatGPT configuration")
        api_key = st.text_input("OpenAI API key", type="password")
        base_url = st.text_input("OpenAI base URL", help="Optional; defaults to api.openai.com")
        model = st.text_input("Model", value="gpt-5-nano")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
        config = ChatGPTConfig.from_inputs(api_key, base_url, model, temperature)
        _render_status(config)

    st.header("Engagement details")
    company = st.text_input("Company", value="SampleCo")
    industry = st.text_input("Industry", value="Retail")
    markets_raw = st.text_input("Target markets (comma-separated)", value="Germany, France")
    priorities = st.multiselect(
        "Top priorities",
        options=["Growth", "Cost efficiency", "Risk mitigation", "Sustainability", "Digital"],
        default=["Growth", "Risk mitigation"],
    )

    if st.button("Run analysis"):
        markets = _parse_markets(markets_raw)
        if not markets:
            st.error("Please enter at least one market (comma-separated).")
            return

        try:
            result = generate_analysis(
                config,
                company=company or "Unknown company",
                industry=industry or "General",
                markets=markets,
                priorities=priorities,
            )
        except ChatGPTNotConfiguredError as exc:
            st.error(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            st.error(f"Analysis failed: {exc}")
            return

        st.subheader("Company brief")
        st.write(result.company_brief or "No brief returned.")

        st.subheader("Market insights")
        if not result.markets:
            st.info("Add at least one market to generate insights.")
        else:
            _render_market_cards(result)


if __name__ == "__main__":
    main()
