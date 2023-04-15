import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
import datetime as dt
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
        self.savings = None
        self.today = pd.Timestamp("today").normalize()

    def get_encoding(self, file): #Model
        """Detect the encoding of a file."""
        result = chardet.detect(file.read())
        return result['encoding']

    def read_csv(self, file, delimiter, encoding): #Model
        """Read a CSV file with the specified delimiter and encoding."""
        file.seek(0)
        return pd.read_csv(file, delimiter=delimiter, encoding=encoding)

    def detect_headers(self): #Model
        """Detect the headers of the CSV file."""
        return list(self.data.columns)
    
    def process_dates(self, start_date, end_date): #Model
        """Process the dates and return filtered data to display comparative graphs."""
        self.data[self.date_column] = pd.to_datetime(self.data[self.date_column], format="%Y-%m-%d")
        # Filter the data to the specified date range
        filtered_data = self.data[(self.data[self.date_column] >= start_date) & (self.data[self.date_column] <= end_date)]
        # Create a date range
        date_range = pd.date_range(start_date, end_date)
        # Merge the data with the date range to fill in missing dates
        filtered_data = filtered_data.merge(pd.DataFrame({self.date_column: date_range}), how="right", on=self.date_column).fillna({self.debit_column: 0})
        filtered_data = filtered_data.merge(pd.DataFrame({self.date_column: date_range}), how="right", on=self.date_column).fillna({self.credit_column: 0})
        # Convert the debit and credit columns to integers
        filtered_data[self.debit_column] = filtered_data[self.debit_column].astype(int)
        filtered_data[self.credit_column] = filtered_data[self.credit_column].astype(int)
        # Add a column for the day
        filtered_data["day"] = (filtered_data[self.date_column] - start_date).dt.days + 1
        # Calculate the cumulative sum
        filtered_data[self.debit_column] = filtered_data[self.debit_column].cumsum()  # Calculate the cumulative sum
        filtered_data[self.credit_column] = filtered_data[self.credit_column].cumsum()  # Calculate the cumulative sum
        return filtered_data

    def process_data(self): #Model
        """Process the data in the CSV file."""
        self.data[self.date_column] = pd.to_datetime(self.data[self.date_column], format=self.date_format)
        self.data[self.debit_column] = self.data[self.debit_column].apply(self.clean_number)
        self.data[self.credit_column] = self.data[self.credit_column].apply(self.clean_number)
        self.data[self.balance_column] = self.data[self.balance_column].apply(self.clean_number)
        self.show_summary()

    def clean_number(self, num): #Model
        """Clean a number string by removing non-numeric characters and converting it to a float."""
        try:
            num = re.sub(r'[^\d\.,]', '', str(num))
            return float(num.replace('.', '').replace(',', '.'))
        except ValueError:
            return np.nan
        
    def ask_gpt(self, api_key, prompt, data): #Model
        """Send a query to the GPT API and return the response."""
        openai.api_key = api_key
        model_engine = "gpt-3.5-turbo"
        max_tokens = 4096 - 1689  # Maximum tokens allowed minus 1 for the API

        # Convert bank statement data to a readable string
        if data is None:
            statement_str = ""
        else:
            statement_str = data.to_string(index=False)

        # Calculate the number of tokens in the prompt
        prompt_tokens = math.ceil(len(prompt) / 4)

        # Calculate the remaining tokens available for statement_str
        available_tokens = max_tokens - prompt_tokens

        # Truncate statement_str to fit within the available tokens
        truncated_statement_str = statement_str[:available_tokens * 4]

        # Create the GPT prompt
        full_prompt = f"{prompt}\n{truncated_statement_str}\n"

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

    def group_by_time(self, time): #Model
        """Group the data by the specified time period."""
        return self.data.groupby(pd.Grouper(key=self.date_column, freq=time)).sum()
    
    def group_by_category(self): #Model
        """Group the data by category."""
        return self.data.groupby(self.category_column).sum()
    
    def match_columns(self, headers): #Controller
        """Match the columns in the CSV file to the required columns."""
        # define the columns from header list
        self.date_column = st.selectbox("Select the date column", headers)
        self.debit_column = st.selectbox("Select the debit column", headers)
        self.credit_column = st.selectbox("Select the credit column", headers)
        self.balance_column = st.selectbox("Select the balance column", headers)
        self.category_column = st.selectbox("Select the category column", headers)
        self.description_column = st.selectbox("Select the description column", headers)
        return self.date_column, self.debit_column, self.credit_column, self.balance_column, self.category_column, self.description_column
    
    def run(self): #Controller
        """Run the financial analysis app."""
        with st.sidebar:
            st.image("assets/wally_logo.png", use_column_width=True)
            st.title("Financial Analysis App")
            with st.expander("About"):
                st.markdown("This app uses machine learning to analyze your bank statement data and generate a financial report.")
                st.markdown("The app uses the [OpenAI GPT-3 API](https://openai.com/blog/openai-api/) to generate the report.")
                st.info("This app is for demonstration purposes only. It is not intended for production use. Please do not enter any sensitive data in your csv.")
            with st.expander("Settings", expanded=True):
                self.delimiter = st.text_input("Delimiter (default ';')", value=";")
                self.currency = st.text_input("Currency (default '€')", value="€")
                self.savings = st.number_input(f"How much money do you want to save every month? (default {self.currency}1000)", value=1000)
                self.date_format = st.text_input("Date format (default '%d-%m-%Y')", value="%d-%m-%Y")
                self.gpt_api_key = st.text_input("Optional: Enter your OpenAI GPT API key", type="password")
            self.file = st.file_uploader("Upload your CSV file", type=['csv'])

        if self.file is not None:
            try:
                encoding = self.get_encoding(self.file)
                self.data = self.read_csv(self.file, self.delimiter, encoding)                
                headers = self.detect_headers()
                with st.sidebar:
                    with st.expander("Match columns", expanded=True):
                        self.match_columns(headers)

                    # Ask for OpenAI GPT API key
                    process = st.button("Process")

                if process:
                    st.session_state = True
                    with st.spinner("Processing data..."):
                        self.process_data()

            except Exception as e:
                with st.sidebar:
                    st.write("Error: ", e)
        if st.session_state is None:
            self.cat = st.image("https://cataas.com/cat/gif", use_column_width=True)
        elif st.session_state:
            self.cat = st.empty()

    def show_summary(self): #View
        """Show a summary of the financial data."""
        st.header("Summary")

        current_month = datetime.now().strftime("%Y-%m")
        current_month_data = self.data[self.data[self.date_column].dt.to_period('M') == current_month]
        earnings = current_month_data[self.credit_column].sum()
        expenses = current_month_data[self.debit_column].sum()
        balance = earnings - expenses
        self.avg_expenses = self.data[self.debit_column].mean() * 30.437  # Assuming 30.437 days average per month
        self.recommended_salary = self.avg_expenses + self.savings  # Assuming a 25% buffer

        # Calculate time deltas
        self.last_7_days = self.today - pd.Timedelta(days=7)
        self.previous_7_days = self.last_7_days - pd.Timedelta(days=7)
        self.last_15_days = self.today - pd.Timedelta(days=15)
        self.previous_15_days = self.last_15_days - pd.Timedelta(days=15)
        self.last_30_days = self.today - pd.Timedelta(days=30)
        self.previous_30_days = self.last_30_days - pd.Timedelta(days=30)
        self.last_180_days = self.today - pd.Timedelta(days=180)
        self.previous_180_days = self.last_180_days - pd.Timedelta(days=180)
        
        # Calculate value deltas
        self.delta_expenses_7 = 1/(self.data[(self.data[self.date_column] >= self.previous_7_days) & (self.data[self.date_column] < self.last_7_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_7_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum())-1
        self.delta_earnings_7 = 1/(self.data[(self.data[self.date_column] >= self.previous_7_days) & (self.data[self.date_column] < self.last_7_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_7_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum())-1
        self.delta_expenses_15 = 1/(self.data[(self.data[self.date_column] >= self.previous_15_days) & (self.data[self.date_column] < self.last_15_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_15_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum())-1
        self.delta_earnings_15 = 1/(self.data[(self.data[self.date_column] >= self.previous_15_days) & (self.data[self.date_column] < self.last_15_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_15_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum())-1
        self.delta_expenses_30 = 1/(self.data[(self.data[self.date_column] >= self.previous_30_days) & (self.data[self.date_column] < self.last_30_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_30_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum())-1
        self.delta_earnings_30 = 1/(self.data[(self.data[self.date_column] >= self.previous_30_days) & (self.data[self.date_column] < self.last_30_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_30_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum())-1
        self.delta_expenses_180 = 1/(self.data[(self.data[self.date_column] >= self.previous_180_days) & (self.data[self.date_column] < self.last_180_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_180_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum())-1
        self.delta_earnings_180 = 1/(self.data[(self.data[self.date_column] >= self.previous_180_days) & (self.data[self.date_column] < self.last_180_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= self.last_180_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum())-1
        
        # Filtered data
        self.data_last_7_days = self.process_dates(self.last_7_days, self.today)
        self.data_previous_7_days = self.process_dates(self.previous_7_days, self.last_7_days)
        self.data_last_15_days = self.process_dates(self.last_15_days, self.today)
        self.data_previous_15_days = self.process_dates(self.previous_15_days, self.last_15_days)
        self.data_last_30_days = self.process_dates(self.last_30_days, self.today)
        self.data_previous_30_days = self.process_dates(self.previous_30_days, self.last_30_days)
        self.data_last_180_days = self.process_dates(self.last_180_days, self.today)
        self.data_previous_180_days = self.process_dates(self.previous_180_days, self.last_180_days)

        # Calculat sum of earnings and expenses
        self.earnings_last_7_days = self.data[(self.data[self.date_column] >= self.last_7_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()
        self.expenses_last_7_days = self.data[(self.data[self.date_column] >= self.last_7_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()
        self.earnings_previous_7_days = self.data[(self.data[self.date_column] >= self.previous_7_days) & (self.data[self.date_column] < self.last_7_days)][self.credit_column].sum()
        self.expenses_previous_7_days = self.data[(self.data[self.date_column] >= self.previous_7_days) & (self.data[self.date_column] < self.last_7_days)][self.debit_column].sum()
        self.earnings_last_15_days = self.data[(self.data[self.date_column] >= self.last_15_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()
        self.expenses_last_15_days = self.data[(self.data[self.date_column] >= self.last_15_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()
        self.earnings_previous_15_days = self.data[(self.data[self.date_column] >= self.previous_15_days) & (self.data[self.date_column] < self.last_15_days)][self.credit_column].sum()
        self.expenses_previous_15_days = self.data[(self.data[self.date_column] >= self.previous_15_days) & (self.data[self.date_column] < self.last_15_days)][self.debit_column].sum()
        self.earnings_last_30_days = self.data[(self.data[self.date_column] >= self.last_30_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()
        self.expenses_last_30_days = self.data[(self.data[self.date_column] >= self.last_30_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()
        self.earnings_previous_30_days = self.data[(self.data[self.date_column] >= self.previous_30_days) & (self.data[self.date_column] < self.last_30_days)][self.debit_column].sum()
        self.expenses_previous_30_days = self.data[(self.data[self.date_column] >= self.previous_30_days) & (self.data[self.date_column] < self.last_30_days)][self.credit_column].sum()
        self.earnings_last_180_days = self.data[(self.data[self.date_column] >= self.last_180_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()
        self.expenses_last_180_days = self.data[(self.data[self.date_column] >= self.last_180_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()
        self.earnings_previous_180_days = self.data[(self.data[self.date_column] >= self.previous_180_days) & (self.data[self.date_column] < self.last_180_days)][self.debit_column].sum()
        self.expenses_previous_180_days = self.data[(self.data[self.date_column] >= self.previous_180_days) & (self.data[self.date_column] < self.last_180_days)][self.credit_column].sum()

        col1, col2 = st.columns(2)
    
        if self.gpt_api_key:
            # Call GPT API
            with st.spinner("Calling OpeanAI's GPT API..."):
                response = self.ask_gpt(self.gpt_api_key, f'''
                You are a bank statement financial analist. What can you tell me about my bank statement below? Also, consider the following:
                1. The currency is {self.currency}
                2. The current month is {current_month}
                3. The earnings for the current month are {self.currency}{earnings:,.2f}
                4. The expenses for the current month are {self.currency}{expenses:,.2f}
                5. The balance for the current month is {self.currency}{balance:,.2f}
                6. The earnings for the last 7 days are {self.currency}{self.earnings_last_7_days:,.2f}
                7. The expenses for the last 7 days are {self.currency}{self.expenses_last_7_days:,.2f}
                8. The earnings for the previous 7 days are {self.currency}{self.earnings_previous_7_days:,.2f}
                9. The expenses for the previous 7 days are {self.currency}{self.expenses_previous_7_days:,.2f}
                10. The earning growth for the last 7 days is {self.delta_earnings_7:,.2%}
                11. The expense growth for the last 7 days is {self.delta_expenses_7:,.2%}
                12. The earnings for the last 30 days are {self.currency}{self.earnings_last_30_days:,.2f}
                13. The expenses for the last 30 days are {self.currency}{self.expenses_last_30_days:,.2f}
                14. The recommended salary for the current month is {self.currency}{self.recommended_salary:,.2f}
                Write a list of 5 recomendations based of the data, be specific, and include the numbers from the list above.
                Write 2 forecasest based on these numbers, be specific, and include the numbers from the list above.
                In your response introduce theories, concepts, and explain your reasoning.
                ''', self.data)
                st.info("🐱💬 Wally's overview")
                st.info(response)
        else:
            st.warning("You need to set your GPT API key in the config file to use this feature.")
        with col1:
            col3, col4 = st.columns(2)
            with col3:
                st.metric(value=f"{current_month}", label="Current Month")
            with col4:
                st.metric(value=f"{self.currency}{earnings:,.2f}", label="Earnings")
        with col2:
            col5, col6 = st.columns(2)
            with col5:
                st.metric(value=f"{self.currency}{expenses:,.2f}", label="Expenses")
            with col6:
                st.metric(value=f"{self.currency}{balance:,.2f}", label="Balance")  
            col7, col8 = st.columns(2)
                
            with col7:
                st.metric(value=f"{self.currency}{self.avg_expenses:,.2f}", label="Average Monthly Expenses")
            with col8:
                st.metric(value=f"{self.currency}{self.recommended_salary:,.2f}", delta=f"{self.savings / self.avg_expenses * 100:,.2f}%" , label="Recommended Salary")
        
        # Calculate expenses larger than average
        # filter the data to get the expenses larger than the average
        expenses_larger_than_average = self.data[self.data[self.debit_column] > self.avg_expenses]
        # sort the data by the debit column
        expenses_larger_than_average = expenses_larger_than_average.sort_values(self.debit_column, ascending=False)


        st.subheader("Expenses Larger than Average")
        col,col0 = st.columns(2)
        with col:
            # create an experimental interactive panda table with the data
            st.dataframe(expenses_larger_than_average.style.highlight_max(axis=0),use_container_width=True)
        with col0:
            if self.gpt_api_key:
                # Call OpenAI API
                with st.spinner("Calling OpenAI's API..."):
                    response = self.ask_gpt(self.gpt_api_key, f'''
                    You are a bank statement financial analist.
                    What can you tell me about this list of expenses larger than my average monthly spending?
                    write a list of 5 recomendations based of the data.
                    the currency is: {self.currency}
                    the current month is: {current_month}
                    Be specific, and include the numbers from the data.
                    Data:
                    ''', expenses_larger_than_average)
                    st.info("🐱💬 Wally's ideas on expenses larger than average")
                    st.info(response)
            else:
                st.warning("You need to set your GPT API key in the config file to use this feature.")
        self.show_charts()

    def show_charts(self): #View
        """Show charts of the financial data."""
        st.subheader("Cumulative variation of earnings and expenses")
        tab1, tab2,tab3, tab4 = st.tabs(["7 days","15 days", "30 days", "180 days"])

        with tab1:
            col9, col10 = st.columns(2)
            with col9:
                # show metric of the total expenses for the last 7 days with delta in relation to the previous 7 days
                st.metric(label="Total Expenses Last 7 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_7_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()}", delta=f"{self.delta_expenses_7*100}%", delta_color="inverse")
            with col10:
                # show metric of the total earnings for the last 7 days with delta in relation to the previous 7 days
                st.metric(label="Total Earnings Last 7 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_7_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()}", delta=f"{self.delta_earnings_7*100}%")

            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=self.data_last_7_days["day"], y=self.data_last_7_days[self.debit_column], name="Last 7 days", mode='lines+markers'))
            fig5.add_trace(go.Scatter(x=self.data_previous_7_days["day"], y=self.data_previous_7_days[self.debit_column], name="Previous 7 days", mode='lines+markers'))
            fig5.add_trace(go.Scatter(x=self.data_last_7_days["day"], y=self.data_last_7_days[self.credit_column], name="Earnigns Last 7 days", mode='lines+markers'))
            # add a line with the expenses for the previous 7 days
            fig5.add_trace(go.Scatter(x=self.data_previous_7_days["day"], y=self.data_previous_7_days[self.credit_column], name="Earnings Previous 7 days", mode='lines+markers'))
            fig5.update_layout(title="Total Expenses for the Last 7 days")
            st.plotly_chart(fig5, use_container_width=True)
        
        with tab2:
            col11, col12 = st.columns(2)
            with col11:
                # show metric of the total expenses for the last 15 days with delta in relation to the previous 15 days
                st.metric(label="Total Expenses Last 15 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_15_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()}", delta=f"{self.delta_expenses_15*100}%", delta_color="inverse")
            with col12:
                # show metric of the total earnings for the last 15 days with delta in relation to the previous 15 days
                st.metric(label="Total Earnings Last 15 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_15_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()}", delta=f"{self.delta_earnings_15*100}%")

            fig6 = go.Figure()
            fig6.add_trace(go.Scatter(x=self.data_last_15_days["day"], y=self.data_last_15_days[self.debit_column], name="Last 15 days", mode='lines+markers'))
            fig6.add_trace(go.Scatter(x=self.data_previous_15_days["day"], y=self.data_previous_15_days[self.debit_column], name="Previous 15 days", mode='lines+markers'))
            fig6.add_trace(go.Scatter(x=self.data_last_15_days["day"], y=self.data_last_15_days[self.credit_column], name="Earnigns Last 15 days", mode='lines+markers'))
            # add a line with the expenses for the previous 15 days
            fig6.add_trace(go.Scatter(x=self.data_previous_15_days["day"], y=self.data_previous_15_days[self.credit_column], name="Earnings Previous 15 days", mode='lines+markers'))
            fig6.update_layout(title="Total Expenses for the Last 15 days")
            st.plotly_chart(fig6, use_container_width=True)

        with tab3:
            col13, col14 = st.columns(2)

            with col13:
                # show metric of the total expenses for the last 30 days with delta in relation to the previous 30 days
                st.metric(label="Total Expenses Last 30 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_30_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()}", delta=f"{self.delta_expenses_30*100}%", delta_color="inverse")
            with col14:
                # show metric of the total earnings for the last 30 days with delta in relation to the previous 30 days
                st.metric(label="Total Earnings Last 30 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_30_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()}", delta=f"{self.delta_earnings_30*100}%")

            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=self.data_last_30_days["day"], y=self.data_last_30_days[self.debit_column], name="Expenses Last 30 days", mode='lines+markers'))
            fig8.add_trace(go.Scatter(x=self.data_previous_30_days["day"], y=self.data_previous_30_days[self.debit_column], name="Expenses Previous 30 days", mode='lines+markers'))
            # add a line with the earnings for the last 30 days
            fig8.add_trace(go.Scatter(x=self.data_last_30_days["day"], y=self.data_last_30_days[self.credit_column], name="Earnigns Last 30 days", mode='lines+markers'))
            # add a line with the expenses for the previous 30 days
            fig8.add_trace(go.Scatter(x=self.data_previous_30_days["day"], y=self.data_previous_30_days[self.credit_column], name="Earnings Previous 30 days", mode='lines+markers'))
            fig8.update_layout(title="Expenses by day in the last 30 days")
            st.plotly_chart(fig8, use_container_width=True)
        
        with tab4:
            col15, col16 = st.columns(2)
            with col15:
                # show metric of the total expenses for the last 180 days with delta in relation to the previous 180 days
                st.metric(label="Total Expenses Last 180 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_180_days) & (self.data[self.date_column] < self.today)][self.debit_column].sum()}", delta=f"{self.delta_expenses_180*100}%", delta_color="inverse")
            with col16:
                # show metric of the total earnings for the last 180 days with delta in relation to the previous 180 days
                st.metric(label="Total Earnings Last 180 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= self.last_180_days) & (self.data[self.date_column] < self.today)][self.credit_column].sum()}", delta=f"{self.delta_earnings_180*100}%")

            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=self.data_last_180_days["day"], y=self.data_last_180_days[self.debit_column], name="Last 180 days", mode='lines+markers'))
            fig9.add_trace(go.Scatter(x=self.data_previous_180_days["day"], y=self.data_previous_180_days[self.debit_column], name="Previous 180 days", mode='lines+markers'))
            # add a line with the earnings for the last 180 days
            fig9.add_trace(go.Scatter(x=self.data_last_180_days["day"], y=self.data_last_180_days[self.credit_column], name="Earnigns Last 180 days", mode='lines+markers'))
            # add a line with the expenses for the previous 180 days
            fig9.add_trace(go.Scatter(x=self.data_previous_180_days["day"], y=self.data_previous_180_days[self.credit_column], name="Earnings Previous 180 days", mode='lines+markers'))
            fig9.update_layout(title="Expenses by day in the last 180 days")
            st.plotly_chart(fig9, use_container_width=True)

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
        st.subheader("Expenses per Category")
        expenses_by_category = self.data.groupby(self.category_column)[self.debit_column].sum().reset_index()
        fig2 = px.pie(expenses_by_category, values=self.debit_column, names=self.category_column)
        st.plotly_chart(fig2, use_container_width=True)

        # Monthly earnings and expenses
        st.subheader("Monthly Earnings and Expenses")
        # Bar chart with expenses per category per month
        expenses_by_category_month = self.data.groupby([self.data[self.date_column].dt.to_period('M'), self.category_column])[self.debit_column].sum().reset_index()
        expenses_by_category_month[self.date_column] = expenses_by_category_month[self.date_column].astype(str)
        fig3 = px.bar(expenses_by_category_month, x=self.date_column, y=self.debit_column, color=self.category_column)
        fig3.update_layout(title="Expenses per Category per Month",legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="left",
            x=0,
            title=dict(text="Category")
        ))
        st.plotly_chart(fig3, use_container_width=True)
    
        # Bar chart with earnings per month
        earnings_by_month = self.data.groupby(self.data[self.date_column].dt.to_period('M'))[self.credit_column].sum().reset_index()
        earnings_by_month[self.date_column] = earnings_by_month[self.date_column].astype(str)
        fig4 = px.bar(earnings_by_month, x=self.date_column, y=self.credit_column, title='Earnings per Month')
        st.plotly_chart(fig4, use_container_width=True)

        # cumulative daily expenses
        # get the unique months of the year from the data
        months_of_year = self.data[self.date_column].dt.strftime('%B %Y').unique()
        # create an empty figure
        fig4 = go.Figure()
        # loop through each month of the year and add a line to the figure
        for month_of_year in months_of_year:
            # filter the data by the month of the year
            expenses_by_month_of_year = self.data[self.data[self.date_column].dt.strftime('%B %Y') == month_of_year]
            expenses_by_day = expenses_by_month_of_year.groupby(expenses_by_month_of_year[self.date_column].dt.to_period('D'))[self.debit_column].sum().reset_index()
            expenses_by_day[self.date_column] = expenses_by_day[self.date_column].astype(str)
            # use cumsum() to get the cumulative sum of the debit column
            expenses_by_day[self.debit_column] = expenses_by_day[self.debit_column].cumsum()
            # add a line to the figure with the month of the year as the legend
            fig4.add_trace(go.Scatter(x=expenses_by_day[self.date_column], y=expenses_by_day[self.debit_column], name=month_of_year))
        # add a title to the plot
        fig4.update_layout(title="Cumulative Daily Expenses by Month of Year")
        st.plotly_chart(fig4, use_container_width=True)
        

if __name__ == "__main__":
    app = FinancialApp()
    app.run()