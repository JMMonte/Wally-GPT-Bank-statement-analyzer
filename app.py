import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
import re
import chardet

class FinancialApp:

    def __init__(self):
        self.data = None
        self.delimiter = ';'
        self.date_column = None
        self.debit_column = None
        self.credit_column = None
        self.balance_column = None
        self.category_column = None
        self.date_format = '%d-%b-%Y'
        self.file = None

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

    def run(self):
        """Run the financial analysis app."""
        with st.sidebar:
            st.title("Financial Analysis App")
            self.delimiter = st.text_input("Delimiter (default ';')", value=";")
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
                    process = st.button("Process")

                if process:
                    self.process_data()

            except Exception as e:
                with st.sidebar:
                    st.write("Error: ", e)
                
    def show_summary(self):
        """Show a summary of the financial data."""
        st.subheader("Summary")

        current_month = datetime.now().strftime("%Y-%m")
        current_month_data = self.data[self.data[self.date_column].dt.to_period('M') == current_month]
        earnings = current_month_data[self.credit_column].sum()
        expenses = current_month_data[self.debit_column].sum()
        balance = earnings - expenses

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(value=f"{current_month}", label="Current Month")
        with col2:
            st.metric(value=f"${earnings:,.2f}", label="Earnings")
        with col3:
            st.metric(value=f"${expenses:,.2f}", label="Expenses")
        with col4:
            st.metric(value=f"${balance:,.2f}", label="Balance")
        
        # Recommended salary calculator
        avg_expenses = self.data[self.debit_column].mean() * 30  # Assuming 30 days per month
        
        st.write("How much would you like to save each month?")
        coli1, coli2 = st.columns(2)
        with coli1:
            st.metric(value=f"${avg_expenses:,.2f}", label="Average daily Expenses")
        with coli2:
            
            recommended_salary = avg_expenses + self.savings  # Assuming a 25% buffer
            st.metric(value=f"${recommended_salary:,.2f}", delta=f"{self.savings / avg_expenses * 100:,.2f}%" , label="Recommended Salary")

        self.show_charts()

    def show_charts(self):
        """Show charts of the financial data."""
        st.subheader("Charts")
        # Line chart of cumulative earnings and spending
        fig1 = go.Figure()

        # add a trace for earnings
        fig1.add_trace(go.Bar(x=self.data[self.date_column], y=self.data[self.credit_column], name='Earnings', marker=dict(color='green')))
        # add a trace for expenses
        fig1.add_trace(go.Bar(x=self.data[self.date_column], y=self.data[self.debit_column], name='Expenses', marker=dict(color='red')))
        # add a trace for the balance
        fig1.add_trace(go.Line(x=self.data[self.date_column], y=self.data[self.balance_column], name='Balance', marker=dict(color='blue')))

        # set the layout for the legend
        fig1.update_layout(showlegend=True, legend=dict(title=dict(text='Legend'), orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

        st.plotly_chart(fig1)

        # Pie chart of expenses per category
        # Assuming a "Category" column exists in the dataset
        expenses_by_category = self.data.groupby(self.category_column)[self.debit_column].sum().reset_index()
        fig2 = px.pie(expenses_by_category, values=self.debit_column, names=self.category_column)
        st.plotly_chart(fig2)

        # Line chart with expenses per category per month
        expenses_by_category_month = self.data.groupby([self.data[self.date_column].dt.to_period('M'), self.category_column])[self.debit_column].sum().reset_index()
        expenses_by_category_month[self.date_column] = expenses_by_category_month[self.date_column].astype(str)
        fig3 = px.line(expenses_by_category_month, x=self.date_column, y=self.debit_column, color=self.category_column)
        st.plotly_chart(fig3)

if __name__ == "__main__":
    app = FinancialApp()
    app.run()