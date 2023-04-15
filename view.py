import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
import datetime as dt
import pandas as pd

class FinancialView:
    def __init__(self):
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
        avg_expenses = self.data[self.debit_column].mean() * 30.437  # Assuming 30.437 days average per month
        st.subheader("Recommended Salary Calculator")
        coli1, coli2, coli3 = st.columns([2,1,1])
        with coli1:
            st.write(f'''
                    How much would you like to save each month? This is taking into account a value of {self.currency}{self.savings} over your average monthly expenses.
                    ''')
        with coli2:
            st.metric(value=f"{self.currency}{avg_expenses:,.2f}", label="Average Monthly Expenses")
        with coli3:
            
            recommended_salary = avg_expenses + self.savings  # Assuming a 25% buffer
            st.metric(value=f"{self.currency}{recommended_salary:,.2f}", delta=f"{self.savings / avg_expenses * 100:,.2f}%" , label="Recommended Salary")

        self.show_charts()

    def show_charts(self):
        """Show charts of the financial data."""
        st.subheader("Cumulative variation of earnings and expenses")
        tab, tab0,tab1, tab2 = st.tabs(["7 days","15 days", "30 days", "180 days"])
        today = pd.Timestamp("today").normalize()
        with tab:
            last_7_days = today - pd.Timedelta(days=7)
            previous_7_days = last_7_days - pd.Timedelta(days=7)
            colr1, colr2 = st.columns(2)
            with colr1:
                # show metric of the total expenses for the last 7 days with delta in relation to the previous 7 days
                delta_expenses = 1/(self.data[(self.data[self.date_column] >= previous_7_days) & (self.data[self.date_column] < last_7_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= last_7_days) & (self.data[self.date_column] < today)][self.debit_column].sum())-1
                st.metric(label="Total Expenses Last 7 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_7_days) & (self.data[self.date_column] < today)][self.debit_column].sum()}", delta=f"{delta_expenses*100}%", delta_color="inverse")
            with colr2:
                # show metric of the total earnings for the last 7 days with delta in relation to the previous 7 days
                delta_earnings = 1/(self.data[(self.data[self.date_column] >= previous_7_days) & (self.data[self.date_column] < last_7_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= last_7_days) & (self.data[self.date_column] < today)][self.credit_column].sum())-1
                st.metric(label="Total Earnings Last 7 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_7_days) & (self.data[self.date_column] < today)][self.credit_column].sum()}", delta=f"{delta_earnings*100}%")

            data_last_7_days = self.process_dates(last_7_days, today)
            data_previous_7_days = self.process_dates(previous_7_days, last_7_days)

            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=data_last_7_days["day"], y=data_last_7_days[self.debit_column], name="Last 7 days", mode='lines+markers'))
            fig5.add_trace(go.Scatter(x=data_previous_7_days["day"], y=data_previous_7_days[self.debit_column], name="Previous 7 days", mode='lines+markers'))
            fig5.add_trace(go.Scatter(x=data_last_7_days["day"], y=data_last_7_days[self.credit_column], name="Earnigns Last 7 days", mode='lines+markers'))
            # add a line with the expenses for the previous 7 days
            fig5.add_trace(go.Scatter(x=data_previous_7_days["day"], y=data_previous_7_days[self.credit_column], name="Earnings Previous 7 days", mode='lines+markers'))
            fig5.update_layout(title="Total Expenses for the Last 7 days")
            st.plotly_chart(fig5, use_container_width=True)
        with tab0:
            last_15_days = today - pd.Timedelta(days=15)
            previous_15_days = last_15_days - pd.Timedelta(days=15)
            colr1, colr2 = st.columns(2)
            with colr1:
                # show metric of the total expenses for the last 15 days with delta in relation to the previous 15 days
                delta_expenses = 1/(self.data[(self.data[self.date_column] >= previous_15_days) & (self.data[self.date_column] < last_15_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= last_15_days) & (self.data[self.date_column] < today)][self.debit_column].sum())-1
                st.metric(label="Total Expenses Last 15 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_15_days) & (self.data[self.date_column] < today)][self.debit_column].sum()}", delta=f"{delta_expenses*100}%", delta_color="inverse")
            with colr2:
                # show metric of the total earnings for the last 15 days with delta in relation to the previous 15 days
                delta_earnings = 1/(self.data[(self.data[self.date_column] >= previous_15_days) & (self.data[self.date_column] < last_15_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= last_15_days) & (self.data[self.date_column] < today)][self.credit_column].sum())-1
                st.metric(label="Total Earnings Last 15 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_15_days) & (self.data[self.date_column] < today)][self.credit_column].sum()}", delta=f"{delta_earnings*100}%")

            data_last_15_days = self.process_dates(last_15_days, today)
            data_previous_15_days = self.process_dates(previous_15_days, last_15_days)
            fig6 = go.Figure()
            fig6.add_trace(go.Scatter(x=data_last_15_days["day"], y=data_last_15_days[self.debit_column], name="Last 15 days", mode='lines+markers'))
            fig6.add_trace(go.Scatter(x=data_previous_15_days["day"], y=data_previous_15_days[self.debit_column], name="Previous 15 days", mode='lines+markers'))
            fig6.add_trace(go.Scatter(x=data_last_15_days["day"], y=data_last_15_days[self.credit_column], name="Earnigns Last 15 days", mode='lines+markers'))
            # add a line with the expenses for the previous 15 days
            fig6.add_trace(go.Scatter(x=data_previous_15_days["day"], y=data_previous_15_days[self.credit_column], name="Earnings Previous 15 days", mode='lines+markers'))
            fig6.update_layout(title="Total Expenses for the Last 15 days")
            st.plotly_chart(fig6, use_container_width=True)
        with tab1:
            last_30_days = today - pd.Timedelta(days=30)
            previous_30_days = last_30_days - pd.Timedelta(days=30)
            colr1, colr2 = st.columns(2)
            with colr1:
                # show metric of the total expenses for the last 30 days with delta in relation to the previous 30 days
                delta_expenses = 1/(self.data[(self.data[self.date_column] >= previous_30_days) & (self.data[self.date_column] < last_30_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= last_30_days) & (self.data[self.date_column] < today)][self.debit_column].sum())-1
                st.metric(label="Total Expenses Last 30 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_30_days) & (self.data[self.date_column] < today)][self.debit_column].sum()}", delta=f"{delta_expenses*100}%", delta_color="inverse")
            with colr2:
                # show metric of the total earnings for the last 30 days with delta in relation to the previous 30 days
                delta_earnings = 1/(self.data[(self.data[self.date_column] >= previous_30_days) & (self.data[self.date_column] < last_30_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= last_30_days) & (self.data[self.date_column] < today)][self.credit_column].sum())-1
                st.metric(label="Total Earnings Last 30 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_30_days) & (self.data[self.date_column] < today)][self.credit_column].sum()}", delta=f"{delta_earnings*100}%")

            data_last_30_days = self.process_dates(last_30_days, today)
            data_previous_30_days = self.process_dates(previous_30_days, last_30_days)

            fig8 = go.Figure()
            fig8.add_trace(go.Scatter(x=data_last_30_days["day"], y=data_last_30_days[self.debit_column], name="Expenses Last 30 days", mode='lines+markers'))
            fig8.add_trace(go.Scatter(x=data_previous_30_days["day"], y=data_previous_30_days[self.debit_column], name="Expenses Previous 30 days", mode='lines+markers'))
            # add a line with the earnings for the last 30 days
            fig8.add_trace(go.Scatter(x=data_last_30_days["day"], y=data_last_30_days[self.credit_column], name="Earnigns Last 30 days", mode='lines+markers'))
            # add a line with the expenses for the previous 30 days
            fig8.add_trace(go.Scatter(x=data_previous_30_days["day"], y=data_previous_30_days[self.credit_column], name="Earnings Previous 30 days", mode='lines+markers'))
            fig8.update_layout(title="Expenses by day in the last 30 days")
            st.plotly_chart(fig8, use_container_width=True)
        
        with tab2:
            last_180_days = today - pd.Timedelta(days=180)
            previous_180_days = last_180_days - pd.Timedelta(days=180)
            colr1, colr2 = st.columns(2)
            with colr1:
                # show metric of the total expenses for the last 180 days with delta in relation to the previous 180 days
                delta_expenses = 1/(self.data[(self.data[self.date_column] >= previous_180_days) & (self.data[self.date_column] < last_180_days)][self.debit_column].sum())*(self.data[(self.data[self.date_column] >= last_180_days) & (self.data[self.date_column] < today)][self.debit_column].sum())-1
                st.metric(label="Total Expenses Last 180 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_180_days) & (self.data[self.date_column] < today)][self.debit_column].sum()}", delta=f"{delta_expenses*100}%", delta_color="inverse")
            with colr2:
                # show metric of the total earnings for the last 180 days with delta in relation to the previous 180 days
                delta_earnings = 1/(self.data[(self.data[self.date_column] >= previous_180_days) & (self.data[self.date_column] < last_180_days)][self.credit_column].sum())*(self.data[(self.data[self.date_column] >= last_180_days) & (self.data[self.date_column] < today)][self.credit_column].sum())-1
                st.metric(label="Total Earnings Last 180 days", value=f"{self.currency}{self.data[(self.data[self.date_column] >= last_180_days) & (self.data[self.date_column] < today)][self.credit_column].sum()}", delta=f"{delta_earnings*100}%")

            data_last_180_days = self.process_dates(last_180_days, today)
            data_previous_180_days = self.process_dates(previous_180_days, last_180_days)

            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=data_last_180_days["day"], y=data_last_180_days[self.debit_column], name="Last 180 days", mode='lines+markers'))
            fig9.add_trace(go.Scatter(x=data_previous_180_days["day"], y=data_previous_180_days[self.debit_column], name="Previous 180 days", mode='lines+markers'))
            # add a line with the earnings for the last 180 days
            fig9.add_trace(go.Scatter(x=data_last_180_days["day"], y=data_last_180_days[self.credit_column], name="Earnigns Last 180 days", mode='lines+markers'))
            # add a line with the expenses for the previous 180 days
            fig9.add_trace(go.Scatter(x=data_previous_180_days["day"], y=data_previous_180_days[self.credit_column], name="Earnings Previous 180 days", mode='lines+markers'))
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