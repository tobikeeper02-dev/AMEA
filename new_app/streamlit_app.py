"""Fresh Streamlit interface for AMEA Next."""
from pathlib import Path
import sys
from typing import List

import streamlit as st

# Ensure local package importability without altering existing files
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from amea_new import AnalysisResult, OpenAIConfig, analyze_request, health_check  # noqa: E402


def _collect_markets(raw: str) -> List[str]:
    return [m.strip() for m in raw.split(",") if m.strip()]


def sidebar_inputs() -> OpenAIConfig:
    st.sidebar.header("OpenAI settings")
    api_key = st.sidebar.text_input("API key", type="password")
    base_url = st.sidebar.text_input("Base URL (optional)") or None
    model = st.sidebar.text_input("Model", value="gpt-5-nano")
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2)
    st.sidebar.caption("gpt-5-nano ignores temperature but other models may use it.")
    return OpenAIConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
    )


def render_health(cfg: OpenAIConfig) -> None:
    st.subheader("Health check")
    if st.button("Run connectivity test"):
        try:
            status = health_check(cfg)
            st.success(f"ChatGPT responded: {status}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Health check failed: {exc}")


def render_results(results: List[AnalysisResult]) -> None:
    for result in results:
        with st.expander(f"{result.country} PESTEL"):
            for key in ["Political", "Economic", "Social", "Technological", "Environmental", "Legal"]:
                value = result.pestel.get(key, "Not returned")
                st.markdown(f"**{key}:** {value}")
            st.markdown("**Raw ChatGPT output**")
            st.code(result.raw_text)


def main() -> None:
    st.title("AMEA Next")
    st.markdown("Generate PESTEL insights with live ChatGPT responses.")

    cfg = sidebar_inputs()
    render_health(cfg)

    st.subheader("Engagement inputs")
    company = st.text_input("Company", value="Acme Corp")
    industry = st.text_input("Industry", value="E-commerce")
    markets_raw = st.text_input("Target markets (comma separated)", value="Germany, France")
    priorities_raw = st.text_area("Priorities (one per line)", value="Growth\nRegulation readiness")

    if st.button("Run analysis"):
        markets = _collect_markets(markets_raw)
        priorities = [p.strip() for p in priorities_raw.splitlines() if p.strip()]
        try:
            results = analyze_request(
                company=company,
                industry=industry,
                markets=markets,
                priorities=priorities,
                config=cfg,
            )
            render_results(results)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Analysis failed: {exc}")


if __name__ == "__main__":
    main()
