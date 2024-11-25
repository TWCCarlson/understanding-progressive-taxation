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

st.selectbox("Select your country:", ["United States"])
st.selectbox("Select the fiscal year:", [2025], help="""Each year has different
             tax brackets.""")
st.selectbox("Choose your filing status:",
             ["Single Filer", "Head of Household", "Married Filing Separately",
              "Married Filing Jointly"], help="""Generally, tax brackets 
              favor those with dependents.""")
st.number_input(label="Input your taxable income (in your country's currency):",
                format="%.2f", step=1000.00, min_value=0.00, value=65000.00)


chart = create_bracket_graph.TaxBracketBreakdownGraph(INCOME, BRACKETS_SINGLE_FILER)
st.altair_chart(chart.get_full_combochart(), theme=None, use_container_width=True)