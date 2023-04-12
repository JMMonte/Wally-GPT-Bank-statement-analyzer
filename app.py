import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
import math
import re
import chardet
import openai

st.set_page_config(page_title="GPT Bank statement analyzer", page_icon="🐈", layout="wide")

st.session_state = None

class FinancialApp:

    def __init__(self):
        self.data = None
        self.delimiter = ';'
        self.currency = '€'
        self.date_column = None
        self.debit_column = None
        self.credit_column = None
        self.balance_column = None
        self.category_column = None
        self.date_format = '%d-%b-%Y'
        self.file = None
        self.cat = None

    def get_encoding(self, file):
        """Detect the encoding of a file."""
        result = chardet.detect(file.read())
        return result['encoding']

    def read_csv(self, file, delimiter, encoding):
        """Read a CSV file with the specified delimiter and encoding."""
        file.seek(0)
        return pd.read_csv(file, delimiter=delimiter, encoding=encoding)

    def detect_headers(self):
        """Detect the headers of the CSV file."""
        return list(self.data.columns)
    
    def process_data(self):
        """Process the data in the CSV file."""
        self.data[self.date_column] = pd.to_datetime(self.data[self.date_column], format=self.date_format)
        self.data[self.debit_column] = self.data[self.debit_column].apply(self.clean_number)
        self.data[self.credit_column] = self.data[self.credit_column].apply(self.clean_number)
        self.data[self.balance_column] = self.data[self.balance_column].apply(self.clean_number)
        self.show_summary()

    def clean_number(self, num):
        """Clean a number string by removing non-numeric characters and converting it to a float."""
        try:
            num = re.sub(r'[^\d\.,]', '', str(num))
            return float(num.replace('.', '').replace(',', '.'))
        except ValueError:
            return np.nan
        
    def ask_gpt(self, api_key, prompt, data):
        """Send a query to the GPT API and return the response."""
        openai.api_key = api_key
        model_engine = "gpt-3.5-turbo"
        max_tokens = 4096 - 1689  # Maximum tokens allowed minus 1 for the API

        # Convert bank statement data to a readable string
        statement_str = data.to_string(index=False)

        # Calculate the number of tokens in the prompt
        prompt_tokens = math.ceil(len(prompt) / 4)

        # Calculate the remaining tokens available for statement_str
        available_tokens = max_tokens - prompt_tokens

        # Truncate statement_str to fit within the available tokens
        truncated_statement_str = statement_str[:available_tokens * 4]
        print(f"Truncated statement_str to {len(truncated_statement_str)} characters")

        # Create the GPT prompt
        full_prompt = f"{prompt}\n{truncated_statement_str}\n"
        print(f"Full prompt length: {len(full_prompt)} characters")
        print(f"Full prompt tokens: {math.ceil(len(full_prompt) / 4)}")

        # Call the GPT API
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=540,
            temperature=0.9
        )

        # Return the response
        output_text = response['choices'][0]['message']['content']
        return output_text

    def run(self):
        
        """Run the financial analysis app."""
        with st.sidebar:
            st.image("assets/wally_logo.png", use_column_width=True)
            st.title("Financial Analysis App")
            st.info("This app is for demonstration purposes only. It is not intended for production use. Please do not enter any sensitive data in your csv.")
            self.delimiter = st.text_input("Delimiter (default ';')", value=";")
            self.currency = st.text_input("Currency (default '€')", value="€")
            self.file = st.file_uploader("Upload your CSV file", type=['csv'])

        if self.file is not None:
            
            try:
                encoding = self.get_encoding(self.file)
                self.data = self.read_csv(self.file, self.delimiter, encoding)

                
                headers = self.detect_headers()
                with st.sidebar:
                    st.subheader("Match columns")
                    self.date_column = st.selectbox("Select date column", headers)
                    self.debit_column = st.selectbox("Select debit (expenses) column", headers)
                    self.credit_column = st.selectbox("Select credit (earnings) column", headers)
                    self.balance_column = st.selectbox("Select balance column", headers)
                    self.category_column = st.selectbox("Select category column", headers)
                    self.savings = st.number_input("Savings per month", value=1000, step=1000)

                    self.date_format = st.text_input("Date format (default '%d-%m-%Y')", value='%d-%m-%Y')
                    # Ask for OpenAI GPT API key
                    gpt_api_key = st.text_input("Enter your OpenAI GPT API key", type="password")
                    process = st.button("Process")

                if process:
                    st.session_state = True
                    if gpt_api_key:
                        # Call GPT API
                        response = self.ask_gpt(gpt_api_key, f"You are a bank statement analist. What can you tell me about my bank statement below? are there any transactions that stand out and I should pay attention to? write a list of recomendations based of the data. the currency is: {self.currency}", self.data)
                        st.header("CatGPT Response")
                        st.write(response)
                    self.process_data()

            except Exception as e:
                with st.sidebar:
                    st.write("Error: ", e)
        if st.session_state is None:
            self.cat = st.image("https://cataas.com/cat/gif", use_column_width=True)
        elif st.session_state:
            self.cat = st.empty()
                
    def show_summary(self):
        """Show a summary of the financial data."""
        st.header("Summary")

        current_month = datetime.now().strftime("%Y-%m")
        current_month_data = self.data[self.data[self.date_column].dt.to_period('M') == current_month]
        earnings = current_month_data[self.credit_column].sum()
        expenses = current_month_data[self.debit_column].sum()
        balance = earnings - expenses

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(value=f"{current_month}", label="Current Month")
        with col2:
            st.metric(value=f"{self.currency}{earnings:,.2f}", label="Earnings")
        with col3:
            st.metric(value=f"{self.currency}{expenses:,.2f}", label="Expenses")
        with col4:
            st.metric(value=f"{self.currency}{balance:,.2f}", label="Balance")
        
        # Recommended salary calculator
        avg_expenses = self.data[self.debit_column].mean() * 30  # Assuming 30 days per month
        st.subheader("Recommended Salary Calculator")
        st.write(f'''
                    How much would you like to save each month? This is taking into account a value of {self.currency}{self.savings} over your average monthly expenses.
                    ''')
        coli1, coli2 = st.columns(2)
        with coli1:
            st.metric(value=f"{self.currency}{avg_expenses:,.2f}", label="Average Monthly Expenses")
        with coli2:
            
            recommended_salary = avg_expenses + self.savings  # Assuming a 25% buffer
            st.metric(value=f"{self.currency}{recommended_salary:,.2f}", delta=f"{self.savings / avg_expenses * 100:,.2f}%" , label="Recommended Salary")

        self.show_charts()

    def group_by_time(self, time):
        """Group the data by the specified time period."""
        return self.data.groupby(pd.Grouper(key=self.date_column, freq=time)).sum()
    
    def group_by_category(self):
        """Group the data by category."""
        return self.data.groupby(self.category_column).sum()

    def show_charts(self):
        """Show charts of the financial data."""
        st.header("Charts")
        # Line chart of cumulative earnings and spending
        st.subheader("Cumulative Earnings and Spending")
        fig1 = go.Figure()

        # add a trace for earnings
        fig1.add_trace(go.Bar(x=self.data[self.date_column], y=self.data[self.credit_column], name='Earnings', marker=dict(color='green')))
        # add a trace for expenses
        fig1.add_trace(go.Bar(x=self.data[self.date_column], y=self.data[self.debit_column], name='Expenses', marker=dict(color='red')))
        # add a trace for the balance
        fig1.add_trace(go.Line(x=self.data[self.date_column], y=self.data[self.balance_column], name='Balance', marker=dict(color='blue')))

        # set the layout for the legend
        fig1.update_layout(showlegend=True, legend=dict(title=dict(text='Legend'), orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
        
        st.plotly_chart(fig1, use_container_width=True)

        # Pie chart of expenses per category
        # Assuming a "Category" column exists in the dataset
        st.subheader("Expenses per Category")
        expenses_by_category = self.data.groupby(self.category_column)[self.debit_column].sum().reset_index()
        fig2 = px.pie(expenses_by_category, values=self.debit_column, names=self.category_column)
        st.plotly_chart(fig2, use_container_width=True)

        # Line chart with expenses per category per month
        st.subheader("Expenses per Category per Month")
        expenses_by_category_month = self.data.groupby([self.data[self.date_column].dt.to_period('M'), self.category_column])[self.debit_column].sum().reset_index()
        expenses_by_category_month[self.date_column] = expenses_by_category_month[self.date_column].astype(str)
        fig3 = px.bar(expenses_by_category_month, x=self.date_column, y=self.debit_column, color=self.category_column)
        st.plotly_chart(fig3, use_container_width=True)

        # cumulative daily expenses
        st.subheader("Cumulative Daily Expenses")
        # get the unique months from the data
        months = self.data[self.date_column].dt.month_name().unique()
        # create an empty figure
        fig4 = go.Figure()
        # loop through each month and add a line to the figure
        for month in months:
            # filter the data by the month
            expenses_by_month = self.data[self.data[self.date_column].dt.month_name() == month]
            expenses_by_day = expenses_by_month.groupby(expenses_by_month[self.date_column].dt.to_period('D'))[self.debit_column].sum().reset_index()
            expenses_by_day[self.date_column] = expenses_by_day[self.date_column].astype(str)
            # use cumsum() to get the cumulative sum of the debit column
            expenses_by_day[self.debit_column] = expenses_by_day[self.debit_column].cumsum()
            # add a line to the figure with the month name as the legend
            fig4.add_trace(go.Scatter(x=expenses_by_day[self.date_column], y=expenses_by_day[self.debit_column], name=month))
        # add a title to the plot
        fig4.update_layout(title="Cumulative Daily Expenses by Month")
        st.plotly_chart(fig4, use_container_width=True)
        

if __name__ == "__main__":
    app = FinancialApp()
    app.run()