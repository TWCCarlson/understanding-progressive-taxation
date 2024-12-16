import pandas as pd
import json
import pathlib
# This is tailored to the Tax Foundation's Historical Income Tax Rates csv
# As such will not work on any other files or if they change the format of the file
# A copy of the file used it maintained in this repo
filer_types = ["Single Filer", "Married Filing Jointly", 
               "Married Filing Separately", "Head of Household"]


def identify_filer_type(string):
    for filer_type in filer_types:
        if filer_type in string:
            return filer_type
    raise ValueError(f"""String was not a valid filer type. Valid types are:
                     \n\t{filer_types}""")


def format_currency(data):
    data = data.replace("$", "")
    data = data.replace(",", "")
    return data


def format_percent(data):
    data = data.replace("%", "")
    data = float(data) / 100.00
    return data


def write_data_to_json(country: str, year: str, filer_type: str, 
                       bracket_dict: dict):
    directory_path = f"./bracket-data-store/{country}/{year}/"
    file_name = f"{filer_type}.json"
    pathlib.Path(directory_path).mkdir(parents=True, exist_ok=True)
    filepath = directory_path + file_name
    with open(filepath,'w') as outfile:
        json.dump(bracket_dict, outfile)


def parse_bracket(bracket: pd.DataFrame):
    # Drop ">" column
    bracket = bracket.drop(bracket.columns[-2], axis="columns")
    # Replace % with float
    bracket.iloc[:,1] = bracket.iloc[:,1].map(format_percent)
    # Strip "$" and ","
    bracket.iloc[:,-1] = bracket.iloc[:,-1].map(format_currency)
    # Shift income column up
    bracket.iloc[:,-1] = bracket.iloc[:,-1].shift(-1)
    # Replace NaN with "inf"
    bracket = bracket.infer_objects(copy=False).fillna("inf")
    # Writeout
    year = bracket.iloc[0,0]
    filer_type = bracket.columns[1]
    country = "United States"
    # Create dict from data
    key = bracket.columns[-1]
    value = bracket.columns[1]
    bracket_data = bracket[[key, value]].set_index(key).to_dict()[value]
    # Write the file out
    write_data_to_json(country, year, filer_type, bracket_data)


def rename_column(target, new_name):
    df.rename(columns={target:new_name}, inplace=True)


# Read all csv data and drop the notes column as well as any empty rows
df = pd.read_csv("./bracket-data-sources/Historical Income Tax Rates and Brackets, 1862-2021.csv")
df = df.drop(["Notes:"], axis="columns")
df = df.dropna(axis="index", how="any")
years_u = df['Year'].unique() # Find all unique years


# Rename columns to match my db names
for col in df.columns.tolist():
    # Try to rename filer type columns
    try:
        filer_type = identify_filer_type(col)
        rename_column(col, filer_type)
    except ValueError:
        pass

# For each year, extract the tax brackets
for year in years_u:
    year_brackets = df.loc[df["Year"] == year] # Boolean masks when "Year"==year
    for i in range(1, year_brackets.shape[1], 3):
        # Get indices for each set of 3 columns of interest
        cols=["Year"]
        for j in range(i,i+3):
            cols.append(year_brackets.iloc[:,j].name)
        tax_bracket = year_brackets[cols]
        parse_bracket(tax_bracket)

    