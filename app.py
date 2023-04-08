import pandas as pd
import streamlit as st
import plotly.express as px
import datetime as dt
import plotly.graph_objects as go
import plotly.express as px
import chardet
import re
import io

def calculate_monthly_budget(df, selected_columns):
    now = dt.datetime.now()
    start_of_month = dt.datetime(now.year, now.month, 1)

    df = df[df[selected_columns["date"]] >= start_of_month]

    income = df[df[selected_columns["credit"]].notna()][selected_columns["credit"]].sum()
    expenses = df[df[selected_columns["debit"]].notna()][selected_columns["debit"]].sum()
    monthly_budget = income - expenses
    return monthly_budget

def plot_cumulative_totals_by_category(df, selected_columns):
    df = df.set_index(selected_columns["date"])
    df.sort_index(inplace=True)

    categories = df[selected_columns["category"]].unique()

    cat_dfs = []
    for category in categories:
        cat_df = df[df[selected_columns["category"]] == category]
        cum_debits = cat_df[selected_columns["debit"]].cumsum()
        cum_credits = cat_df[selected_columns["credit"]].cumsum()
        cat_cumulative_totals = pd.concat([cum_debits, cum_credits], axis=1)
        cat_cumulative_totals.columns = ["Cumulative Debits", "Cumulative Credits"]
        cat_cumulative_totals["Category"] = category
        cat_dfs.append(cat_cumulative_totals)

    cumulative_totals = pd.concat(cat_dfs, axis=0)
    cumulative_totals.reset_index(inplace=True)

    fig = px.line(cumulative_totals, x=selected_columns["date"], y=["Cumulative Debits", "Cumulative Credits"], color="Category", title="Cumulative Totals by Category")
    st.plotly_chart(fig)


def plot_cumulative_totals(df, selected_columns):
    df = df.set_index(selected_columns["date"]).fillna(0)
    df.sort_index(inplace=True)

    df[selected_columns["debit"]] = pd.to_numeric(df[selected_columns["debit"]], errors='coerce')
    df[selected_columns["credit"]] = pd.to_numeric(df[selected_columns["credit"]], errors='coerce')

    df["Cumulative Debits"] = df[selected_columns["debit"]].cumsum()
    df["Cumulative Credits"] = df[selected_columns["credit"]].cumsum()

    fig = px.line(df[["Cumulative Debits","Cumulative Credits"]], title="Cumulative Totals")
    # fig.add_scatter(x=df.index, y=cum_debits, mode="lines", name="Cumulative Debits")
    # fig.add_scatter(x=df.index, y=cum_credits, mode="lines", name="Cumulative Credits")
    st.plotly_chart(fig)


def read_bank_statement(file, selected_columns, encoding):
    try:
        df = pd.read_csv(file, sep=";", skiprows=5, encoding=encoding, header=0)
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return None
    
    st.write(df.head())
    df.dropna(how='all', inplace=True)
    
    if selected_columns["date"] not in df.columns or selected_columns["debit"] not in df.columns or selected_columns["credit"] not in df.columns or selected_columns["category"] not in df.columns:
        st.error("One or more selected columns do not exist in the CSV file.")
        return None

    df[selected_columns["date"]] = pd.to_datetime(df[selected_columns["date"]], format=selected_columns["date_format"], errors='coerce')
    df.dropna(subset=[selected_columns["date"]], inplace=True)
    
    try:
        df[selected_columns["debit"]] = pd.to_numeric(df[selected_columns["debit"]].str.replace(re.escape(selected_columns["thousands_separator"]), '').str.replace(re.escape(selected_columns["decimal_separator"]), '.'))
        df[selected_columns["credit"]] = pd.to_numeric(df[selected_columns["credit"]].str.replace(re.escape(selected_columns["thousands_separator"]), '').str.replace(re.escape(selected_columns["decimal_separator"]), '.'))
    except Exception as e:
        st.error(f"Error converting debit or credit columns to numeric: {e}")
        return None

    return df


def categorize_expenses(df, selected_columns):
    expenses_by_category = df.groupby(selected_columns["category"])[selected_columns["debit"]].sum().reset_index()
    expenses_by_category.columns = ["Category", "Total Expenses"]
    expenses_by_category["Total Expenses"] = expenses_by_category["Total Expenses"].astype(str)
    return expenses_by_category


def calculate_monthly_budget(df, selected_columns):
    try:
        income = df[df[selected_columns["credit"]].notna()][selected_columns["credit"]].sum()
        expenses = df[df[selected_columns["debit"]].notna()][selected_columns["debit"]].sum()
        monthly_budget = income - expenses
    except Exception as e:
        st.error(f"Error calculating monthly budget: {e}")
        return None

    return monthly_budget

def recommend_salary_range(monthly_budget):
    min_salary = monthly_budget * 12 * 1.2
    max_salary = monthly_budget * 12 * 1.5
    return min_salary, max_salary

def process_input_text(text, selected_columns):
    try:
        df = pd.read_csv(io.StringIO(text), sep=";", skiprows=4, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"Error processing input text: {e}")
        return None
    
    df.dropna(how='all', inplace=True)
    
    if selected_columns["date"] not in df.columns or selected_columns["debit"] not in df.columns or selected_columns["credit"] not in df.columns or selected_columns["category"] not in df.columns:
        st.error("One or more selected columns do not exist in the input text.")
        return None
    
    try:
        df[selected_columns["date"]] = pd.to_datetime(df[selected_columns["date"]], format=selected_columns["date_format"])
        df[selected_columns["debit"]] = pd.to_numeric(df[selected_columns["debit"]].str.replace(selected_columns["thousands_separator"], '').str.replace(selected_columns["decimal_separator"], '.'))
        df[selected_columns["credit"]] = pd.to_numeric(df[selected_columns["credit"]].str.replace(selected_columns["thousands_separator"], '').str.replace(selected_columns["decimal_separator"], '.'))
    except Exception as e:
        st.error(f"Error converting columns to appropriate data types: {e}")
        return None

    return df

def select_columns(df):
    if 'selected_columns' not in st.session_state:
        st.session_state.selected_columns = {}

    st.subheader("Sample Bank Statement")
    st.write("Here's a sample of your bank statement to help you select the correct columns. Choose below the columns that correspond to the date, debit, credit, and category of each transaction.")

    columns = list(df.columns)

    selected_cols = {}
    date_column = st.selectbox("Select the date column:", options=columns)
    debit_column = st.selectbox("Select the debit column:", options=columns)
    credit_column = st.selectbox("Select the credit column:", options=columns)
    category_column = st.selectbox("Select the category column:", options=columns)
    date_format = st.text_input("Date format (e.g., '%d-%m-%Y')", "%d-%m-%Y")
    decimal_separator = st.text_input("Decimal separator (e.g., ',')", ",")
    thousands_separator = st.text_input("Thousands separator (e.g., '.')", ".")

    if date_column == debit_column or date_column == credit_column or date_column == category_column or debit_column == credit_column or debit_column == category_column or credit_column == category_column:
        st.error("Selected columns must be unique.")
        return
    
    st.session_state.selected_columns["date"] = date_column
    st.session_state.selected_columns["debit"] = debit_column
    st.session_state.selected_columns["credit"] = credit_column
    st.session_state.selected_columns["category"] = category_column
    st.session_state.selected_columns["date_format"] = date_format
    st.session_state.selected_columns["decimal_separator"] = decimal_separator
    st.session_state.selected_columns["thousands_separator"] = thousands_separator

    st.write(f"Selected columns: {st.session_state.selected_columns}")

st.title("Bank Statement Analyzer")

input_method = st.radio("Choose an input method:", ("Upload CSV File", "Paste CSV Content"))

if input_method == "Upload CSV File":
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file:
        file_bytes = uploaded_file.read()
        encoding = chardet.detect(file_bytes)['encoding']
        uploaded_file.seek(0)

        sample_df = pd.read_csv(uploaded_file, sep=";", skiprows=5, encoding=encoding)
        sample_df.dropna(how='all', inplace=True)

        select_columns(sample_df)

        if st.button("Process"):
            if all(val is not None for val in st.session_state.selected_columns.values()):
                uploaded_file.seek(0)
                df = read_bank_statement(uploaded_file, st.session_state.selected_columns, encoding)
                if df is not None:
                    expenses_by_category = categorize_expenses(df, st.session_state.selected_columns)
                    monthly_budget = calculate_monthly_budget(df, st.session_state.selected_columns)  # Pass selected_columns as an argument
                    if monthly_budget is not None:
                        income = df[df[st.session_state.selected_columns["credit"]].notna()][st.session_state.selected_columns["credit"]].sum()
                        expenses = df[df[st.session_state.selected_columns["debit"]].notna()][st.session_state.selected_columns["debit"]].sum()
                        min_salary, max_salary = recommend_salary_range(monthly_budget)
                        st.header("Expenses by Category")
                        st.write(expenses_by_category)
                        st.header("Monthly Budget")
                        st.write(f"Income: €{income:.2f}")
                        st.write(f"Expenses: €{expenses:.2f}")
                        st.write(f"Monthly Budget: €{monthly_budget:.2f}")
                        st.header("Recommended Salary Range")
                        st.write(f"€{min_salary:.2f} - €{max_salary:.2f}")
                        fig1 = px.pie(expenses_by_category, values="Total Expenses", names="Category", title="Expenses by Category")
                        st.plotly_chart(fig1)
                        plot_cumulative_totals(df, st.session_state.selected_columns)
                        plot_cumulative_totals_by_category(df, st.session_state.selected_columns)
            else:
                st.error("Please make sure all columns are selected before processing.")

elif input_method == "Paste CSV Content":
    input_text = st.text_area("Paste your bank statement CSV content here")

    if input_text:
        df = process_input_text(input_text, st.session_state.selected_columns)
        if df is not None:
            expenses_by_category = categorize_expenses(df, st.session_state.selected_columns)
            monthly_budget = calculate_monthly_budget(df, st.session_state.selected_columns)  # Pass selected_columns as an argument
            if monthly_budget is not None:
                income = df[df[st.session_state.selected_columns["credit"]].notna()][st.session_state.selected_columns["credit"]].sum()
                expenses = df[df[st.session_state.selected_columns["debit"]].notna()][st.session_state.selected_columns["debit"]].sum()
                min_salary, max_salary = recommend_salary_range(monthly_budget)
                st.header("Expenses by Category")
                st.write(expenses_by_category)
                st.header("Monthly Budget")
                st.write(f"Income: €{income:.2f}")
                st.write(f"Expenses: €{expenses:.2f}")
                st.write(f"Monthly Budget: €{monthly_budget:.2f}")
                st.header("Recommended Salary Range")
                st.write(f"€{min_salary:.2f} - €{max_salary:.2f}")
                fig1 = px.pie(expenses_by_category, values="Total Expenses", names="Category", title="Expenses by Category")
                st.plotly_chart(fig1)
                plot_cumulative_totals(df, st.session_state.selected_columns)
                plot_cumulative_totals_by_category(df, st.session_state.selected_columns)

