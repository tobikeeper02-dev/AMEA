"""Streamlit front-end for the AMEA market analysis assistant."""
from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from typing import List

import sys

from sys_path_sanitizer import sanitize_numpy_source_paths

sanitize_numpy_source_paths()

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from amea.pipeline import ComparativeAnalysis, generate_market_analysis
from amea.report.exporters import export_to_docx
from amea.research.llm import (
    ChatGPTNotConfiguredError,
    is_chatgpt_configured,
    run_chatgpt_healthcheck,
)

st.set_page_config(page_title="AMEA - Market Entry Copilot", layout="wide")


def _render_header():
    st.title("AMEA – Automated Market Entry Analysis")
    st.markdown(
        """
        This workspace collects your engagement context and routes it directly through
        OpenAI's ChatGPT API (gpt-5-nano by default) to synthesize tailored PESTEL narratives,
        scores, and recommendations. No static indicator library is used—every run is freshly
        generated for the company, industry, and markets you specify.
        """
    )
    st.caption("All qualitative outputs come from live ChatGPT responses. Provide an API key to activate them.")


def _priority_selector() -> List[str]:
    options = [
        "Growth potential",
        "Cost efficiency",
        "Risk mitigation",
        "Sustainability",
        "Digital acceleration",
    ]
    return st.multiselect("Key strategic priorities", options, default=["Growth potential", "Risk mitigation"])


def _render_scorecard(analysis: ComparativeAnalysis):
    if not analysis.markets:
        st.info("Run an analysis to populate the scorecard.")
        return

    data = []
    for market in analysis.markets:
        row = {"Country": market.country, "Composite score": market.score.composite}
        for key, value in market.score.dimension_scores.items():
            row[key.replace("_", " ").title()] = value
        data.append(row)

    frame = pd.DataFrame(data)
    st.subheader("Comparative scorecard")
    st.dataframe(frame.set_index("Country"))

    radar_data = frame.drop(columns=["Composite score"], errors="ignore")
    if radar_data.shape[1] > 0:
        melted = radar_data.reset_index().melt(id_vars="Country", var_name="Dimension", value_name="Score")
        fig = px.line_polar(
            melted,
            r="Score",
            theta="Dimension",
            color="Country",
            line_close=True,
            range_r=[0, 100],
            title="Capability radar",
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_market_detail(analysis: ComparativeAnalysis):
    if not analysis.markets:
        return

    for market in analysis.markets:
        with st.expander(f"{market.country} deep-dive", expanded=market == analysis.best_market()):
            score_text = f"{market.score.composite}/100" if market.score.composite else "Not scored"
            st.markdown(f"**Opportunity score:** {score_text}")
            if market.entry_mode:
                st.markdown(f"**Recommended entry mode:** {market.entry_mode}")

            if market.news:
                st.markdown("### Recent signals")
                for headline in market.news:
                    st.write(f"• {headline}")

            st.markdown("### PESTEL summary")
            cols = st.columns(3)
            dimensions = list(market.pestel.items())
            for index, (dimension, bullets) in enumerate(dimensions):
                with cols[index % 3]:
                    st.markdown(f"**{dimension}**")
                    if bullets:
                        for bullet in bullets:
                            st.write(f"- {bullet}")
                    else:
                        st.caption("No insights returned.")

            if market.turnaround_actions:
                st.markdown("### Risk mitigations")
                for theme, action in market.turnaround_actions.items():
                    st.write(f"**{str(theme).title()}**: {action}")

            if market.sources:
                st.markdown("### Sources cited")
                for source in market.sources:
                    st.write(f"- {source}")


def _render_export_controls(analysis: ComparativeAnalysis):
    if not analysis.markets:
        return

    buffer = BytesIO()
    export_to_docx(analysis, Path("/tmp/amea_report.docx"))
    with open("/tmp/amea_report.docx", "rb") as doc_handle:
        buffer.write(doc_handle.read())
    st.download_button(
        label="Download DOCX report",
        data=buffer.getvalue(),
        file_name="amea_report.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def _render_company_context(analysis: ComparativeAnalysis):
    brief = analysis.company_brief or {}
    has_summary = bool(brief.get("profile_summary"))
    bullet_sections = [
        ("Strategic fit", brief.get("strategic_fit", [])),
        ("Demand drivers", brief.get("demand_drivers", [])),
        ("Technology enablers", brief.get("technology_enablers", [])),
        ("Regulatory watch", brief.get("regulatory_watch", [])),
        ("Sustainability factors", brief.get("sustainability_factors", [])),
        ("Risk watch", brief.get("risk_watch", [])),
    ]

    if not has_summary and not any(bullets for _, bullets in bullet_sections):
        return

    st.subheader("Company & industry intelligence")
    if has_summary:
        st.markdown(f"**Summary:** {brief['profile_summary']}")

    cols = st.columns(3)
    for index, (label, bullets) in enumerate(bullet_sections):
        cleaned = [bullet for bullet in bullets if bullet]
        if not cleaned:
            continue
        with cols[index % 3]:
            st.markdown(f"**{label}**")
            for bullet in cleaned:
                st.write(f"- {bullet}")


def _parse_market_list(raw: str) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    _render_header()

    with st.sidebar:
        st.header("Engagement setup")
        st.markdown("#### OpenAI configuration")

        api_key_default = st.session_state.get("amea_openai_api_key", "")
        api_key_input = st.text_input(
            "API key",
            value=api_key_default,
            type="password",
            help="Paste your OpenAI key or leave blank to rely on environment/secrets configuration.",
        )
        if api_key_input:
            st.session_state["amea_openai_api_key"] = api_key_input.strip()
        elif "amea_openai_api_key" in st.session_state:
            st.session_state.pop("amea_openai_api_key")

        base_url_default = st.session_state.get("amea_openai_base_url", "")
        base_url_input = st.text_input(
            "Base URL (optional)",
            value=base_url_default,
            placeholder="https://api.openai.com/v1",
            help="Override when routing through Azure OpenAI or a proxy.",
        )
        if base_url_input:
            st.session_state["amea_openai_base_url"] = base_url_input.strip()
        elif "amea_openai_base_url" in st.session_state:
            st.session_state.pop("amea_openai_base_url")

        model_default = st.session_state.get("amea_openai_model") or os.getenv("AMEA_OPENAI_MODEL", "gpt-5-nano")
        model_input = st.text_input(
            "Model name",
            value=model_default,
            help="Specify the ChatGPT model to use (defaults to gpt-5-nano).",
        )
        if model_input:
            st.session_state["amea_openai_model"] = model_input.strip()
        elif "amea_openai_model" in st.session_state:
            st.session_state.pop("amea_openai_model")

        temperature_state = st.session_state.get("amea_openai_temperature")
        if temperature_state is None:
            try:
                temperature_default = float(os.getenv("AMEA_OPENAI_TEMPERATURE", "0.2"))
            except ValueError:
                temperature_default = 0.2
        else:
            try:
                temperature_default = float(temperature_state)
            except (TypeError, ValueError):
                temperature_default = 0.2
        temperature_input = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(temperature_default),
            step=0.05,
            help="Lower values keep outputs deterministic; higher values encourage creative variety.",
        )
        st.session_state["amea_openai_temperature"] = temperature_input

        col_status, col_health = st.columns([2, 1])
        with col_status:
            if is_chatgpt_configured():
                st.success("ChatGPT integration active for all narratives and scores.")
            else:
                st.warning(
                    "ChatGPT integration inactive. Provide an API key above or set OPENAI_API_KEY to enable AI-generated insights."
                )
        with col_health:
            if st.button("Test API"):
                try:
                    result = run_chatgpt_healthcheck()
                    st.success(f"Status {result['status']} · {result['model']} · {result['latency_ms']} ms")
                except ChatGPTNotConfiguredError as exc:
                    st.error(str(exc))
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Health check failed: {exc}")

        st.divider()
        company = st.text_input("Company name", value="Instacart")
        industry = st.text_input("Industry", value="Online grocery delivery")
        use_case = st.selectbox(
            "Primary use case",
            options=["Market expansion", "Partnership scouting", "Investment diligence"],
            help="Tailor outputs to market entry, partner evaluation, or investment screening contexts.",
        )
        markets_raw = st.text_area(
            "Target markets (comma separated)",
            value="Germany, France",
            help="List the countries you want ChatGPT to analyse, separated by commas.",
        )
        markets = _parse_market_list(markets_raw)
        priorities = _priority_selector()
        st.file_uploader("Upload internal context (optional)")
        run = st.button("Run analysis", type="primary")

    if not run:
        st.info("Configure the engagement in the sidebar and run the analysis.")
        return

    if not company or not markets:
        st.warning("Please provide a company name and at least one market (comma separated).")
        return

    try:
        analysis = generate_market_analysis(company, industry, use_case, markets, priorities)
    except ChatGPTNotConfiguredError as exc:
        st.error(str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        st.error(f"ChatGPT call failed: {exc}")
        return

    if best := analysis.best_market():
        leading = (
            f"{best.country} leads with a composite score of {best.score.composite}/100." if best.score.composite else ""
        )
        suffix = f" Recommended entry mode: {best.entry_mode}." if best.entry_mode else ""
        st.success(f"{leading}{suffix}")

    st.caption(
        f"{analysis.company} · {analysis.industry or 'Industry not specified'} · Focus: {analysis.use_case}"
    )

    _render_company_context(analysis)
    _render_scorecard(analysis)
    _render_market_detail(analysis)
    _render_export_controls(analysis)


if __name__ == "__main__":
    main()
