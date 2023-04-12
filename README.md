# Financial Analysis App

This is a simple Streamlit app that reads a CSV file with financial data and performs some analysis on it.

## Installation

To install the required packages, run the following command in your terminal:

``` bash
pip install streamlit pandas numpy plotly chardet
```

Install requirements.txt

```bash
pip install -r requirements.txt
```

## Usage

To run the app, run the following command in your terminal:

``` bash
streamlit run app.py
```

Once the app is running, you can upload a CSV file by using the file uploader in the sidebar. You can also specify the delimiter and date format of your CSV file.

After uploading the file, you need to match the columns with the corresponding data (date column, debit column, credit column, balance column, and category column). You can also specify how much you would like to save per month.

Finally, you can click the "Process" button to process the data and see the summary and charts. The app shows a summary of the current month's earnings, expenses, and balance. It also calculates a recommended salary based on the average daily expenses and the savings per month. The charts show the cumulative earnings and spending, expenses per category, and expenses per category per month.

## Requirements

- streamlit
- pandas
- numpy
- plotly
- chardet

## License

This project is licensed under the MIT License - see the LICENSE file for details.
