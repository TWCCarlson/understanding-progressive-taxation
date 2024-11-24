import numpy as np
import streamlit as st

import create_bracket_graph

INCOME = 75000
BRACKETS_SINGLE_FILER = {
    11925: 0.1,
    48475: 0.12,
    103350: 0.22,
    197300: 0.24,
    250525: 0.32,
    626350: 0.35,
    np.inf: 0.37
}

chart = create_bracket_graph.TaxBracketBreakdownGraph(INCOME, BRACKETS_SINGLE_FILER)
st.altair_chart(chart.get_full_combochart(), theme=None, use_container_width=True)