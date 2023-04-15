import pandas as pd
import plotly.express as px
import streamlit as st

class FinancialDataProcessor:
    def __init__(self, file, delimiter):
        self.data = self.read_csv(file, delimiter)
        
    def read_csv(self, file, delimiter):
        return pd.read_csv(file, delimiter=delimiter)

    def process_data(self, date_column, debit_column, credit_column, date_format):
        self.data[date_column] = pd.to_datetime(self.data[date_column], format=date_format)
        self.data.set_index(date_column, inplace=True)
        return self.data

    def group_by_time(self, time):
        return self.data.groupby(pd.Grouper(freq=time)).sum()

    def plot_data(self, data, x, y, title, color=None):
        fig = px.line(data, x=x, y=y, title=title, color=color)
        fig.show()

if __name__ == "__main__":
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key='file', accept_multiple_files=False)
    delimiter = ';'
    data_processor = FinancialDataProcessor(file, delimiter)
    processed_data = data_processor.process_data('Date', 'Debit', 'Credit', '%d-%m-%Y')
    
    # Plot an example graph
    grouped_data = data_processor.group_by_time('M')
    data_processor.plot_data(grouped_data, x=grouped_data.index, y=['Debit', 'Credit'], title='Monthly Debit and Credit', color='variable')