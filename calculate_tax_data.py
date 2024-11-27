import pandas as pd


def apply_tax_to_bracket(lower_limit: int, upper_limit: int, rate: float):
    return (upper_limit - lower_limit) * rate


def add_row_to_data(data: pd.DataFrame, row: pd.DataFrame):
    data = pd.concat([data, row], ignore_index=True)
    return data


def calculate_tax_breakdown_data(income: int, brackets: dict):
    df_keys = ["bracket_low", "bracket_high", "bracket_rate", 
                "bracket_owed", "cum_owed_low", "cum_owed_high"]
    tax_breakdown_data = pd.DataFrame(columns=df_keys)
    # Starting range
    bracket_high_bound = list(brackets.keys())[0]
    bracket_low_bound = 0
    cumulative_owed_low = 0
    for bracket_high_bound in brackets.keys():
        bracket_rate = brackets[bracket_high_bound]
        bracket_high_value = min(income, bracket_high_bound)
        bracket_owed = apply_tax_to_bracket(bracket_low_bound, 
                                            bracket_high_value, 
                                            bracket_rate)
        cumulative_owed_high = cumulative_owed_low + bracket_owed
        if bracket_owed > 0:
            df_values = [bracket_low_bound, bracket_high_bound,
                            bracket_rate, bracket_owed,
                            cumulative_owed_low, cumulative_owed_high]
            data_row = pd.DataFrame(dict(zip(df_keys, df_values)), index=[0])
            tax_breakdown_data = add_row_to_data(tax_breakdown_data, data_row)
            # Update for next iteration
            bracket_low_bound = bracket_high_bound
            cumulative_owed_low = cumulative_owed_high
    return tax_breakdown_data