import pandas as pd
import altair as alt

class TaxBracketBreakdownGraph:
    def __init__(self, user_income: int, tax_bracket_data: dict) -> None:
        self.calculate_tax_breakdown_data(user_income, tax_bracket_data)
        self.colorize_data()
        self.set_axis_styles(user_income, tax_bracket_data)
        income_chart = self.draw_income_graph(user_income)
        bracket_chart = self.draw_bracket_graph(self.tax_breakdown_data)
        total_owed_chart = self.draw_cumulative_obligation_graph(user_income, self.tax_breakdown_data)
        gridline_layer = self.draw_gridlines(self.tax_breakdown_data)

        # Order matters
        self.chart_assembly = [income_chart, gridline_layer, bracket_chart,
                               total_owed_chart]


    def calculate_tax_breakdown_data(self, income: int, brackets: dict):
        df_keys = ["bracket_low", "bracket_high", "bracket_rate", 
                   "bracket_owed", "cum_owed_low", "cum_owed_high"]
        self.tax_breakdown_data = pd.DataFrame(columns=df_keys)
        # Starting range
        bracket_high_bound = list(brackets.keys())[0]
        bracket_low_bound = 0
        cumulative_owed_low = 0
        for bracket_high_bound in brackets.keys():
            bracket_rate = brackets[bracket_high_bound]
            bracket_high_value = min(income, bracket_high_bound)
            bracket_owed = self.apply_tax_to_bracket(bracket_low_bound, 
                                                     bracket_high_value, 
                                                     bracket_rate)
            cumulative_owed_high = cumulative_owed_low + bracket_owed
            if bracket_owed > 0:
                df_values = [bracket_low_bound, bracket_high_bound,
                             bracket_rate, bracket_owed,
                             cumulative_owed_low, cumulative_owed_high]
                data_row = pd.DataFrame(dict(zip(df_keys, df_values)), index=[0])
                self.add_row_to_data(data_row)
                # Update for next iteration
                bracket_low_bound = bracket_high_bound
                cumulative_owed_low = cumulative_owed_high


    def apply_tax_to_bracket(self, lower_limit: int, upper_limit: int, rate: float):
        return (upper_limit - lower_limit) * rate
    

    def add_row_to_data(self, row: pd.DataFrame):
        self.tax_breakdown_data = pd.concat([self.tax_breakdown_data, row],
                                            ignore_index=True)


    def colorize_data(self):
        # Colors from Sasha Trubetskoy
        colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', 
                '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', 
                '#9a6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', 
                '#000075', '#808080', '#ffffff', '#000000']
        self.tax_breakdown_data['color'] = colors[0:len(self.tax_breakdown_data)]


    def set_axis_styles(self, income: int, bracket_data: dict):
        self.x_axis_def = alt.Axis(labelFontSize=14, labelAngle=0)
        self.y_axis_def = alt.Axis(values=list(bracket_data.keys())[:-1]+[income],
                                   format='$,.2f', labelOverlap="greedy",
                                   labelFontSize=14)
    

    def draw_income_graph(self, income: int):
        # The only data needed is the income data point
        income_data = pd.DataFrame({
            "Income": [income],
            "Name": "Income",
        })
        # Create the chart
        income_chart = alt.Chart(income_data).transform_calculate(
            display_text='toString(format(datum.Income, "$,.2f"))'
        ).mark_bar(color='yellowgreen').encode(
            x=alt.X("Name:N", axis=self.x_axis_def, title=""),
            y=alt.Y("Income:Q", axis=self.y_axis_def, title=""),
            tooltip=[alt.Tooltip('display_text:N', title="Income")]
        )
        # Add descriptive text
        income_text = income_chart.mark_text(
            align='center', baseline='bottom', color='black', fontSize=14, dy=-2
        ).encode(
            y=alt.Y('Income:Q', axis=self.y_axis_def), 
            text=alt.Text('Income:Q', format='$,.2f')
        )
        income_chart_full = income_chart + income_text
        
        return income_chart_full


    def draw_bracket_graph(self, tax_data):
        # Create the chart with each bracket bar
        liability_chart = alt.Chart(tax_data).transform_calculate(
            label='"Owed Per Bracket"',
            bracket_top_end_owed='datum.bracket_owed + datum.bracket_low'
        ).mark_bar().encode(
            x=alt.X('label:N', axis=self.x_axis_def),
            y=alt.Y('bracket_low:Q', axis=self.y_axis_def, title=""),
            y2=alt.Y2("bracket_top_end_owed:Q"),
            color=alt.Color('color', legend=None),
            tooltip=[alt.Tooltip('bracket_owed:Q', format='$,.2f', title="Owed")]
        )
        # Label each bracket bar
        text_equation = 'format(datum.bracket_rate, ".0%") + " (" + format(datum.bracket_owed, "$,.2f") + ")"'
        liability_text = liability_chart.transform_calculate(
            text = text_equation
        ).mark_text(
            align='center', baseline='bottom', fontSize=14, dy=-2
        ).encode(
            y=alt.Y('bracket_top_end_owed:Q', axis=self.y_axis_def, title=""),
            color=alt.value('black'),
            text=alt.Text("text:N"),
            tooltip=[alt.Tooltip('bracket_rate:Q', format='.0%', title="Bracket Tax Rate")]
        )
        # Create underlay for the descriptive text for visual clarity
        liability_text_underlay = liability_text.mark_text(
            align='center', baseline='bottom', fontSize=14,
            stroke='white', strokeWidth=5, strokeJoin='round', dy=-2
        )
        return  liability_text_underlay + liability_chart + liability_text
    

    def draw_cumulative_obligation_graph(self, income, tax_data):
        # Create the chart with each bracket bar
        cumulative_liability_chart = alt.Chart(tax_data).transform_calculate(
            label='"Total Owed"'
        ).mark_bar().encode(
            x=alt.X("label:N", axis=self.x_axis_def, title=""),
            y=alt.Y("cum_owed_low:Q", axis=self.y_axis_def, title=""),
            y2=alt.Y2("cum_owed_high:Q"),
            color=alt.Color('color', legend=None),
            tooltip=[alt.Tooltip('max(cum_owed_high):Q', format='$,.2f', title="Total Owed")]
        )
        # Label the total obligation
        text_equation = 'format(datum.cum_owed_high, "$,.2f") + " (" + format(datum.effective_rate, ".1%") + ")"'
        cumulative_liability_text = alt.Chart(tax_data).transform_window(
            sort=[alt.SortField("cum_owed_high", order="descending")],
            rank="rank(cum_owed_high)"
        ).transform_filter(
            alt.datum.rank == 1 # Only mark on the maximum value
        ).transform_calculate(
            label='"Total Owed"',
            income=alt.expr.toString(income),
            effective_rate=f'datum.cum_owed_high / datum.income',
            text = text_equation
        ).mark_text(
            align='center', baseline='bottom', fontSize=14, dy=-2
        ).encode(
            x=alt.X('label:N', axis=self.x_axis_def, title=""),
            y=alt.Y('cum_owed_high:Q', axis=self.y_axis_def, title=""),
            text=alt.Text('text:N'),
            tooltip=[alt.Tooltip('max(cum_owed_high):Q', format='$,.2f', title="Total Owed"),
                     alt.Tooltip('max(effective_rate):Q', format='.1%', title="Effective Tax Rate")]
        )

        # Create underlay for the descriptive text for visual clarity
        cumulative_liability_underlay = cumulative_liability_text.mark_text(
            align='center', baseline='bottom', fontSize=14,
            stroke='white', strokeWidth=5, strokeJoin='round', dy=-2
        )

        return cumulative_liability_underlay + cumulative_liability_chart + cumulative_liability_text
    

    def draw_gridlines(self, tax_data):
        gridlines = alt.Chart(tax_data).mark_rule(
            color='darkslategray', strokeDash=[2,2]
        ).encode(
            y=alt.Y('bracket_low:Q')
        )
        return gridlines
    

    def get_full_combochart(self):
        return alt.layer(*self.chart_assembly)