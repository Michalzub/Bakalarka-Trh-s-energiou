import streamlit as st

from matplotlib import pyplot as plt
from datetime import datetime, date

import data_access_module as da
import data_manager as dm
import visualizer_module as viz
import analyser_module as am


@st.cache_data
def load_time_span_data(start_date, end_date):
    st.write("Loading:", start_date, end_date)

    DAM = da.get_okte_data_simple(
            "DAM",
            start_date,
            end_date
        )


    DAM = dm.prep_okte_data(DAM)
    return DAM


with st.form("date_range_form"):
    date_range = st.date_input(
        "Select date range",
        value=(date(2025, 10, 1), date(2025, 10, 31))
    )
    submitted = st.form_submit_button("Load")

if submitted:
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        d1 = date(2025, 10, 1)
        d2 = date(2025, 10, 31)
        dt1 = datetime(2025, 10, 1, 0, 0, 0)
        dt2 = datetime(2025, 10, 31, 23, 59, 59)
        dam_data = load_time_span_data(d1, d2)

        fig, _ = viz.plot_line(dam_data, x="deliveryStartBA", y="price")
        st.pyplot(fig)
    else:
        st.error("Please select both dates.")