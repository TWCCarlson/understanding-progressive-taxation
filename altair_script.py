
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from streamlit_dimensions import st_dimensions

font_size = 14
axis_fontSize = 14
# st.set_page_config(layout="wide")


INCOME = 750000
BRACKETS_SINGLE_FILER = {
    11925: 0.1,
    48475: 0.12,
    103350: 0.22,
    197300: 0.24,
    250525: 0.32,
    626350: 0.35,
    np.inf: 0.37
}


tax_data = pd.DataFrame(columns=[
    "bracket_low", 
    "bracket_high", 
    "bracket_rate", 
    "bracket_paid"
])


def apply_tax(lower_limit, upper_limit, rate):
    return (upper_limit - lower_limit) * rate


bracket_high_bound = list(BRACKETS_SINGLE_FILER.keys())[0]
bracket_low_bound = 0
cum_paid_low = 0
for bracket_high_bound in BRACKETS_SINGLE_FILER.keys():
    bracket_rate = BRACKETS_SINGLE_FILER[bracket_high_bound]
    bracket_high_val = min(INCOME, bracket_high_bound)
    bracket_paid = apply_tax(bracket_low_bound, bracket_high_val, bracket_rate)
    cum_paid_high = cum_paid_low + bracket_paid
    if bracket_paid > 0:
        # Add to dataset
        data_row = pd.DataFrame({
            "bracket_low": bracket_low_bound,
            "bracket_high": bracket_high_bound,
            "bracket_rate": bracket_rate,
            "bracket_paid": bracket_paid,
            "cum_paid_low": cum_paid_low,
            "cum_paid_high": cum_paid_high
        }, index=[0])
        tax_data = pd.concat([tax_data, data_row], ignore_index=True)
        # Update for next iteration
        bracket_low_bound = bracket_high_bound
        cum_paid_low = cum_paid_high
print(tax_data)


# Colors from Sasha Trubetskoy
colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', 
          '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', 
          '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', 
          '#000075', '#808080', '#ffffff', '#000000']
tax_data['color'] = colors[0:len(tax_data)]


# Income is a single bar
income_data = pd.DataFrame({"Income": [INCOME], "Name": "Income", "color": "green"})

x_axis_def = alt.Axis(labelFontSize=axis_fontSize, labelAngle=0)
y_axis_def = alt.Axis(values=list(BRACKETS_SINGLE_FILER.keys())[:-1]+[INCOME], 
                    format='$,.2f', labelOverlap="greedy", labelAngle=0,
                    labelFontSize=axis_fontSize)


# Create the income chart
income_chart = alt.Chart(income_data).transform_calculate(
    label='"Income"',
    display_text='toString(format(datum.Income, "$,.2f"))'
).mark_bar(color='red').encode(
    x=alt.X("label:N", axis=x_axis_def, title=""),
    y=alt.Y("Income:Q", axis=y_axis_def, title=""),
    tooltip=[alt.Tooltip('display_text:N', title="Income")]
)
income_bar = income_chart.mark_bar(color='yellowgreen').encode()
income_text = income_chart.transform_calculate(
    position='datum.Income / 2'
).mark_text(
    align='center', baseline='bottom', color='black', fontSize=font_size, dy=-3
).encode(y='Income:Q', text=alt.Text("Income:Q", format='$,.2f'))
# income_chart + income_text


graph_container = st.container()
with graph_container:
    chart_width = st_dimensions()['width']

liability_chart = alt.Chart(tax_data).transform_calculate(
    label='"Owed Per Bracket"',
    bracket_top_end_paid='datum.bracket_paid + datum.bracket_low'
).encode(
    x=alt.X('label:N', sort=None),
    y=alt.Y("bracket_low:Q", title=""),
    y2=alt.Y2("bracket_top_end_paid:Q")
).properties(
    height=600
)
liability_bar = liability_chart.mark_bar().encode(
    color=alt.Color('color', legend=None),
    tooltip=[alt.Tooltip('bracket_paid:Q', format='$,.2f', title="Owed")]
)
liability_text = liability_chart.transform_calculate(
    # position=f'(datum.bracket_low + datum.bracket_top_end_paid) / 2',
    # position=f'(datum.bracket_top_end_paid-datum.bracket_low) > {text_width} ? (datum.bracket_low + datum.bracket_top_end_paid) / 2 : datum.bracket_top_end_paid'
    position='datum.bracket_top_end_paid'
).mark_text(
    # align=alt.condition(f'(datum.bracket_top_end_paid-datum.bracket_low) > {text_width}', alt.value('center'), alt.value('left')),
    # align=alt.expr(alt.expr.if_(alt.datum.bracket_top_end_paid-alt.datum.bracket_low > text_width, 'center', 'left')),
    align='center',
    baseline='bottom', color='black', fontSize=font_size
).encode(
    y='position:Q', text=alt.Text("bracket_rate:Q", format='.0%'),
    tooltip=[alt.Tooltip('bracket_rate:Q', format='.0%', title="Bracket Tax Rate")]
)

liability_text_underlay = alt.Chart(tax_data).transform_calculate(
    label='"Owed Per Bracket"',
    bracket_top_end_paid='datum.bracket_paid + datum.bracket_low',
    width='length(toString(format(datum.bracket_rate, ".0%")))'
).mark_rect(
    color='white', baseline='bottom', opacity=1,
    height=16,
    width=alt.expr('30 + 5 * datum.width'),
).encode(
    x='label:N',
    y='bracket_top_end_paid:Q',
    tooltip=alt.value(None)
)
# liability_bar + liability_text

total_liability_chart = alt.Chart(tax_data).transform_calculate(
    label='"Total Owed"',
).encode(
    y=alt.Y("cum_paid_low:Q"),
    y2=alt.Y2("cum_paid_high:Q"),
    x=alt.X('label:N', sort=['Income','Owed Per Bracket','Total Owed']),
)
total_liability_bar = total_liability_chart.mark_bar().encode(
    color=alt.Color('color', legend=None),
    tooltip=[alt.Tooltip('max(cum_paid_high):Q', format='$,.2f', title="Total Owed")]
)
total_liability_text = total_liability_chart.mark_text(
    align='center', baseline='bottom', color='black', dy=-2, fontSize=font_size, 
).encode(
    y='max(cum_paid_high):Q', x=alt.datum("Total Owed"), 
    text=alt.Text('max(cum_paid_high):Q', format="$,.2f"),
)
total_liability_text_underlay = alt.Chart(tax_data).transform_calculate(
    label='"Total Owed"',
    total_paid = 'max(datum.cum_paid_high)',
    width='toString(format(datum.cum_paid_high, "$,.2f"))'
).mark_rect(
    color='white', baseline='bottom', opacity=1,
    height=18, width=alt.expr('30 + 5 * length(datum.width)')
).encode(
    x=alt.datum("Total Owed"),
    y='total_paid:Q',
    tooltip='width:N'
)
# total_liability_bar + total_liability_text

gridlines = alt.Chart(tax_data).mark_rule(
    color='darkslategray', strokeDash=[2,2]
).encode(
    y=alt.Y('bracket_low:Q')
)

graph_container.altair_chart(income_bar + income_text + liability_text_underlay +
                             liability_bar + liability_text +
                             gridlines + total_liability_text_underlay + 
                             total_liability_bar + total_liability_text,
                            theme=None, use_container_width=True, key="tax_graph")
