import numpy as np
import streamlit as st

import create_bracket_graph

import requests
import pprint as pp
from collections import defaultdict

INCOME = 400000
BRACKETS_SINGLE_FILER = {
    11925: 0.1,
    48475: 0.12,
    103350: 0.22,
    197300: 0.24,
    250525: 0.32,
    626350: 0.35,
    np.inf: 0.37
}
owner = st.secrets.database.db_username
repo = "understanding-progressive-taxation"
path = "bracket-data-store"

# Request contents of the repo
response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/contents',
                        auth=(owner, f'{st.secrets.database.db_api_key}'))
response = response.json()

# Find the SHA for the database tree
for node in response:
    if node['name'] == path:
        data_tree_SHA = node['sha']

# Request the tree structure, recursively
response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/git/trees/{data_tree_SHA}?recursive=1',
                        auth=(owner, f'{st.secrets.database.db_api_key}'))
response = response.json()

# Recreate the directory structure
file_tree = {}
for node in response['tree']:
    node_path = node['path'].split('/')
    cwd = file_tree
    # Drill down the tree, stopping before the last file in the path
    for dir in node_path[:-1]:
        cwd = cwd.setdefault(dir, {})
    # If the last file is a tree, create the next level of nesting
    if node["type"] == "tree":
        cwd[node_path[-1]] = {}
    # otherwise, this is the end of the branch on the tree—save its url
    else:
        cwd[node_path[-1]] = node["url"]

countries = []
for country in file_tree.keys():
    countries.append(country)
country = st.selectbox("Select your country:", countries)
file_tree = file_tree[country] # go down one level


fiscal_years = []
for fiscal_year in file_tree.keys():
    fiscal_years.append(fiscal_year)
fiscal_year = st.selectbox("Select the fiscal year:", fiscal_years, help="""Each year has different
                            tax brackets.""")
file_tree = file_tree[fiscal_year] # go down one level

filer_types = []
for filer_type in file_tree.keys():
    # The filer type is part of the file name, remove the extension
    filer_type = filer_type.removesuffix(".json")
    filer_types.append(filer_type)
filer_type = st.selectbox("Choose your filing status:", filer_types, 
                          help="""Generally tax brackets favor those with dependents.""")

# Use the input to load the brackets data
user_bracket_path = f"bracket-data-store/{country}/{fiscal_year}/{filer_type}.json"
print(f'https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/{user_bracket_path}')
response = requests.get(f'https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/{user_bracket_path}',
                        auth=(owner, f'{st.secrets.database.db_api_key}'))
brackets = response.json() #dict, but all k-v are str
brackets = {int(k) if k.isdigit() else np.inf:float(v) for k,v in brackets.items()}


user_income = st.number_input(label="Input your taxable income (in your country's currency):",
                format="%.2f", step=1000.00, min_value=0.00, value=65000.00)

# brackets = BRACKETS_SINGLE_FILER
chart = create_bracket_graph.TaxBracketBreakdownGraph(user_income, brackets)
st.altair_chart(chart.get_full_combochart(), theme=None, use_container_width=True)