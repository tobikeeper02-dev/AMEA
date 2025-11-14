"""Streamlit front-end for the AMEA market analysis assistant."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List

import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from amea.pipeline import ComparativeAnalysis, generate_market_analysis
from amea.report.exporters import export_to_docx
from amea.research.data_loader import load_country_indicators
from amea.research.llm import is_chatgpt_configured

st.set_page_config(page_title="AMEA - Market Entry Copilot", layout="wide")


def _render_header():
    st.title("AMEA – Automated Market Entry Analysis")
    st.markdown(
        """
        Combine curated macro indicators and AI reasoning to compare markets, synthesize insights,
        and export a board-ready report in minutes.
        """
    )
    st.caption("PESTEL narratives and news highlights leverage OpenAI ChatGPT when credentials are configured.")


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
    data = []
    for market in analysis.markets:
        row = {"Country": market.country, "Composite score": market.score.composite}
        row.update({key.title(): value for key, value in market.score.dimension_scores.items()})
        data.append(row)

    frame = pd.DataFrame(data)
    st.subheader("Comparative scorecard")
    st.dataframe(frame.set_index("Country"))

    if len(analysis.markets) > 0:
        fig = px.line_polar(
            frame.melt(id_vars=["Country", "Composite score"], var_name="Dimension", value_name="Score"),
            r="Score",
            theta="Dimension",
            color="Country",
            line_close=True,
            range_r=[0, 100],
            title="Capability radar",
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_market_detail(analysis: ComparativeAnalysis):
    for market in analysis.markets:
        with st.expander(f"{market.country} deep-dive", expanded=market == analysis.best_market()):
            st.markdown(f"**Opportunity score:** {market.score.composite}/100")
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
                    for bullet in bullets:
                        st.write(f"- {bullet}")

            if market.turnaround_actions:
                st.markdown("### Risk mitigations")
                for theme, action in market.turnaround_actions.items():
                    st.write(f"**{theme.title()}**: {action}")

            if market.sources:
                st.markdown("### Sources consulted")
                for source in market.sources:
                    st.write(f"- {source}")


def _render_export_controls(analysis: ComparativeAnalysis):
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


def main():
    _render_header()

    with st.sidebar:
        st.header("Engagement setup")
        if is_chatgpt_configured():
            st.success("ChatGPT integration active for narratives and news highlights.")
        else:
            st.warning(
                "ChatGPT integration inactive. Set OPENAI_API_KEY before running the analysis to enable AI-generated insights."
            )
        company = st.text_input("Company name", value="Instacart")
        industry = st.text_input("Industry", value="Online grocery delivery")
        use_case = st.selectbox(
            "Primary use case",
            options=["Market expansion", "Partnership scouting", "Investment diligence"],
            help="Tailor outputs to market entry, partner evaluation, or investment screening contexts.",
        )
        markets = st.multiselect(
            "Target markets",
            options=list(load_country_indicators().keys()),
            default=["Germany", "France"],
        )
        priorities = _priority_selector()
        st.file_uploader("Upload internal context (optional)")
        run = st.button("Run analysis", type="primary")

    if not run:
        st.info("Configure the engagement in the sidebar and run the analysis.")
        return

    if not company or not markets:
        st.warning("Please provide a company name and select at least one market.")
        return

    analysis = generate_market_analysis(company, industry, use_case, markets, priorities)

    if best := analysis.best_market():
        st.success(
            f"{best.country} leads with a composite score of {best.score.composite}/100. Recommended entry mode: {best.entry_mode}."
        )

    st.caption(
        f"{analysis.company} · {analysis.industry} · Focus: {analysis.use_case}"
    )

    _render_scorecard(analysis)
    _render_market_detail(analysis)
    _render_export_controls(analysis)


if __name__ == "__main__":
    main()
