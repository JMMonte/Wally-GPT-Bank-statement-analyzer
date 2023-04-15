nina = 1
nani = 2 * nina
nota = 1/nani
 
import datetime as dt
import streamlit as st


today = dt.datetime.now()

st.title(f"Hei, Nina! {today}")
dance = st.button("Klikk her")

if dance:
    st.write(f"Du er {nota} år gammel")
