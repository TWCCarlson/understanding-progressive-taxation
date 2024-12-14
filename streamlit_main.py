import numpy as np
import streamlit as st
import requests
import glob
import json
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
from datetime import datetime

import create_graph
import calculate_tax_data


LOCAL_DEVELOPMENT = False
owner = st.secrets.database.db_username
db_key = st.secrets.database.db_api_key
repo = "understanding-progressive-taxation"
path = "bracket-data-store"


@st.cache_data
def get_tax_database_remote(owner, repo, path, db_key):
    # Request contents of the repo
    response = requests.get(f'https://api.github.com/repos/' + 
                            f'{owner}/{repo}/contents',
                            auth=(owner, f'{db_key}'))
    response = response.json()

    # Find the SHA for the database tree
    for node in response:
        if node['name'] == path:
            data_tree_SHA = node['sha']

    # Request the tree structure, recursively
    response = requests.get(f'https://api.github.com/repos/' + 
                            f'{owner}/{repo}/git/trees/' + 
                            f'{data_tree_SHA}?recursive=1',
                            auth=(owner, f'{db_key}'))
    response = response.json()
    return response


def get_tax_database_local(path):
    # Use local files
    tree = glob.glob("**", root_dir=path, recursive=True)
    file_tree = {}
    for node in tree:
        node_path = node.split('\\')
        cwd = file_tree
        # Drill down the tree, stopping before the last file in the path
        for dir in node_path[:-1]:
            cwd = cwd.setdefault(dir, {})
        if ".json" in node_path[-1]:
            cwd[node_path[-1].removesuffix(".json")] = node
        else:
            cwd[node_path[-1]] = {}
    return file_tree


def parse_db_structure(db):
    # Recreate the directory structure
    file_tree = {}
    for node in db['tree']:
        node_path = node['path'].split('/')
        cwd = file_tree
        # Drill down the tree, stopping before the last file in the path
        for dir in node_path[:-1]:
            cwd = cwd.setdefault(dir, {})
        # If the last file is a tree, create the next level
        if node["type"] == "tree":
            cwd[node_path[-1]] = {}
        # otherwise, this is the end of the branch on the tree, save url as val
        else:
            cwd[node_path[-1]] = node["url"]
    return file_tree


def get_country_options(file_tree):
    countries = []
    for country in file_tree.keys():
        countries.append(country)
    return countries


def get_year_options(file_tree):
    fiscal_years = []
    for fiscal_year in file_tree.keys():
        fiscal_years.append(fiscal_year)
    return fiscal_years


def get_filer_options(file_tree):
    filer_types = []
    for filer_type in file_tree.keys():
        # The filer type is part of the file name, remove the extension
        filer_type = filer_type.removesuffix(".json")
        filer_types.append(filer_type)
    return filer_types


@st.cache_data
def get_bracket_data_remote(owner, repo, db_key, country, fiscal_year, filer_type):
    user_bracket_path = f"bracket-data-store/{country}/{fiscal_year}/{filer_type}.json"
    # Use the input to load the brackets data
    response = requests.get(f'https://raw.githubusercontent.com/' + 
                            f'{owner}/{repo}/refs/heads/main/{user_bracket_path}',
                            auth=(owner, f'{db_key}'))
    print(response.status_code)
    if response.status_code != 404:
        brackets = response.json() #dict, but all k-v are str
        return brackets
    else:
        raise ValueError("Specified Data Does Not Exist")

def get_bracket_data_local(country, fiscal_year, filer_type):
    user_bracket_path = f"bracket-data-store/{country}/{fiscal_year}/{filer_type}.json"
    with open(user_bracket_path) as file:
            brackets = json.load(file)
            return brackets

def coerce_bracket_data_types(brackets):
    brackets = {int(k) if k.isdigit() else np.inf:float(v) for k,v in brackets.items()}
    return brackets


def convert_to_currency(value):
    return locale.currency(value, grouping=True)


def convert_to_percent(value, decimal_digits=2):
    return '{:.{dd}%}'.format(value, dd=decimal_digits)


if LOCAL_DEVELOPMENT:
    tree = get_tax_database_local(path)
else:
    db = get_tax_database_remote(owner, repo, path, db_key)
    tree = parse_db_structure(db)


st.markdown("# What are Progressive Tax Brackets?")
st.markdown("""The United States uses a progressive tax system. That means that 
            the amount you pay is broken out into several tax brackets. In
            each bracket you pay a certain rate on the income falling in that 
            bracket. The tax rate in each bracket increases as income levels do.""")
st.markdown("""This makes it harder to estimate what you owe in your head, but 
            it also means that if you make less you keep a bigger percent of 
            what you earn. Earning more also doesn't retroactively punish you 
            because the parts of your income that fall into lower brackets are 
            still taxed at a lower rate.""")
st.markdown("""Here's an example:""")

example_income = 65000
example_country = "United States"
# example_year = str(datetime.now().year)
example_year = "2025"
example_status = "Single Filer"
if LOCAL_DEVELOPMENT:
    brackets = get_bracket_data_local(example_country, example_year, example_status)
else:
    brackets = get_bracket_data_remote(owner, repo, db_key, example_country, 
                                       example_year, example_status)
brackets = coerce_bracket_data_types(brackets)
example_data = calculate_tax_data.calculate_tax_breakdown_data(example_income, brackets)
example_chart = create_graph.TaxBracketBreakdownGraph(example_data, example_income, brackets)
st.altair_chart(example_chart.get_full_combochart(), theme=None, use_container_width=True)
example_tax_paid = example_data['cum_owed_high'].max()
example_eff_rate_fmt = convert_to_percent(example_tax_paid/example_income, 2)
example_income_fmt = convert_to_currency(example_income)
example_tax_paid_fmt = convert_to_currency(example_tax_paid)

st.markdown("""Here's another way to think about it. Whenever your income is
            high enough to enter a new bracket your *marginal tax rate* increases.
            The marginal tax rate is the amount of tax you pay on the next dollar
            earned.""")

bracket_step_chart = create_graph.TaxBracketStepGraph(brackets)
st.altair_chart(bracket_step_chart.get_chart(), theme=None, use_container_width=True)


st.markdown(f"""Another measure is the *effective tax rate*. That's the calculated 
            percent of your income that you owe as tax. For the above example, 
            paying **\{example_tax_paid_fmt}** in tax on **\{example_income_fmt}** 
            of income is an effective tax rate of **{example_eff_rate_fmt}**.""")
st.markdown(f"""In the graph below you can see that after a certain amount of income
            the proportion of your income you pay in taxes becomes a straight line.
            This is because at the top end there aren't as many brackets, so
            most of the income gets taxed at the higher rates. However, those early
            brackets still tax you at a lower rate.""")
tax_owed_graph = create_graph.TaxOwedGraph(brackets)
st.altair_chart(tax_owed_graph.get_chart(), theme=None, use_container_width=True)



st.markdown("You can use this calculator to try it out for yourself:")
countries = get_country_options(tree)
country = st.selectbox("Select your country:", countries)
fiscal_years = get_year_options(tree[country])
fiscal_year = st.selectbox("Select the fiscal year:", fiscal_years)
filer_types = get_filer_options(tree[country][fiscal_year])
filer_type = st.selectbox("Choose your filing status:", filer_types, 
                          help="Generally tax brackets favor those with dependents.")

user_income = st.number_input(label="Input your taxable income (in your country's currency):",
                                key="income_input", value=65000)

if LOCAL_DEVELOPMENT:
    brackets = get_bracket_data_local(country, fiscal_year, filer_type)
else:
    brackets = get_bracket_data_remote(owner, repo, db_key, country, 
                                       fiscal_year, filer_type)
brackets = coerce_bracket_data_types(brackets)

tax_breakdown_data = calculate_tax_data.calculate_tax_breakdown_data(user_income, brackets)
chart = create_graph.TaxBracketBreakdownGraph(tax_breakdown_data, user_income, brackets)
st.altair_chart(chart.get_full_combochart(), theme=None, use_container_width=True)

st.write(f"Here's a tabular breakdown.")
st.markdown(f"If you earn **{locale.currency(user_income, grouping=True)}** in **{fiscal_year}** as a **{filer_type}** while living in **{country}**...")
tax_breakdown_data_display = tax_breakdown_data
total_owed = locale.currency(tax_breakdown_data['bracket_owed'].sum(), grouping=True)

tax_breakdown_data_display['bracket_low'] = tax_breakdown_data_display['bracket_low'].apply(convert_to_currency)
tax_breakdown_data_display['bracket_high'] = tax_breakdown_data_display['bracket_high'].apply(convert_to_currency)
tax_breakdown_data_display['bracket_rate'] = tax_breakdown_data_display['bracket_rate'].apply(convert_to_percent)
tax_breakdown_data_display['bracket_owed'] = tax_breakdown_data_display['bracket_owed'].apply(convert_to_currency)
mapper = {
    "bracket_low": "From...",
    "bracket_high": "... to",
    "bracket_rate": "You pay...",
    "bracket_owed": "...which is"
}
tax_breakdown_data_display = tax_breakdown_data_display.rename(mapper, axis='columns')
tax_breakdown_data_display = tax_breakdown_data_display.drop(["cum_owed_low", "cum_owed_high", "color"], axis='columns')
st.dataframe(tax_breakdown_data_display, hide_index=True, use_container_width=True)
st.markdown(f"Which amounts to a total tax obligation of **{total_owed}**.")
st.markdown(f"However, this is only one part of the tax calculation. There may be additional taxes to pay.")
st.markdown(f"""You may also be eligible for deductions. A typical deduction will reduce the taxable income you have. 
            In a progressive tax bracket this means you pay less in the highest-taxed brackets.""")