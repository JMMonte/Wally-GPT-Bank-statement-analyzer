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

class FinancialModel:
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
    
    def process_dates(self, start_date, end_date):
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