from datetime import datetime, date, time, timedelta

import pandas as pd
import streamlit as st

import visualizer_module as viz
import data_access_module as da
import data_manager as dm
import analyser_module as am


st.set_page_config(page_title="Analytický modul trhu s elektrinou", layout="wide")

@st.cache_data
def load_data(start_date, end_date, market_type):
    df = da.get_okte_data_simple(market_type, start_date, end_date)
    return dm.prep_okte_data(df)


def get_range_end(start_date: date, range_option: str) -> date:
    if range_option == "1 deň":
        return start_date
    elif range_option == "3 dni":
        return start_date + timedelta(days=2)
    elif range_option == "7 dní":
        return start_date + timedelta(days=6)
    elif range_option == "Celý mesiac":
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        return next_month - timedelta(days=1)
    else:
        return start_date


def get_dam_mtu_for_date(selected_date: date) -> int:
    return 60 if (selected_date.year, selected_date.month) < (2025, 10) else 15


if "datasets" not in st.session_state:
    st.session_state.datasets = {}



left, center, right = st.columns([2, 4, 2])
with center:
    if st.button("Clear cache"):
        st.cache_data.clear()
        st.rerun()
    st.title("Analytický modul trhu s elektrinou")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_start_date = st.date_input(
            "Dátum začiatku",
            value=date(2025, 10, 1),
            min_value=date(2020, 1, 1),
            max_value=date(2026, 12, 31),
        )

    with col2:
        selected_range = st.selectbox(
            "Časový rozsah",
            options=["1 deň", "3 dni", "7 dní", "Celý mesiac"],
            index=3
        )

    with col3:
        market_type = st.selectbox("Typ trhu", ["DAM", "IDM"])

    auto_dam_mtu = get_dam_mtu_for_date(selected_start_date)

    with col4:
        if market_type == "DAM":
            mtu = st.selectbox(
                "MTU",
                options=[auto_dam_mtu],
                index=0,
                disabled=True
            )
        else:
            mtu = st.selectbox(
                "MTU",
                options=[60, 15],
                index=0
            )

    end_date = get_range_end(selected_start_date, selected_range)
    st.caption(f"Vybraný rozsah: {selected_start_date} → {end_date}")

    load_clicked = st.button("Načítať dataset")


    if load_clicked:
        dt1 = datetime.combine(selected_start_date, time.min)
        dt2 = datetime.combine(end_date, time.max)

        if market_type == "DAM":
            effective_market_type = "DAM"
        else:
            effective_market_type = f"IDM{mtu}"

        try:
            with st.spinner("Načítavam dáta..."):
                df = load_data(dt1, dt2, effective_market_type)

            key = (
                f"{market_type} | {selected_start_date} → {end_date}"
                f" | MTU {mtu}"
            )
            st.session_state.datasets[key] = df
            st.success(f"Dataset načítaný: {key}")
        except Exception as e:
            st.error(f"Nepodarilo sa načítať dataset: {e}")


    st.subheader("Načítané datasety")

    if not st.session_state.datasets:
        st.info("Zatiaľ nie sú načítané žiadne datasety.")
    else:
        for key in list(st.session_state.datasets.keys()):
            col1, col2 = st.columns([8, 1])

            with col1:
                st.write(key)

            with col2:
                if st.button("❌", key=f"remove_{key}"):
                    del st.session_state.datasets[key]
                    st.rerun()


    if st.session_state.datasets:
        st.divider()
        st.subheader("Grafy a štatistiky")

        for key, df in st.session_state.datasets.items():
            with st.expander(key, expanded=True):

                tab1, tab2, tab3, tab4 = st.tabs(["Graf", "Súhrnné štatistiky", "Kvantily", "Dáta"])

                with tab1:
                    try:
                        fig, _ = viz.plot_line(df, x="deliveryStart", y="price")
                        st.pyplot(fig)
                    except Exception as e:
                        st.error(f"Nepodarilo sa vykresliť graf: {e}")
                        st.write("Dostupné stĺpce:", list(df.columns))

                with tab2:
                    try:
                        summary = am.price_summary_statistics(df)

                        summary_df = pd.DataFrame(
                            list(summary.items()),
                            columns=["Štatistika", "Hodnota"]
                        )

                        no_unit_stats = {"count", "Skewness", "Kurtosis", "Coef_of_Var"}

                        def format_value(row):
                            stat = str(row["Štatistika"])
                            val = row["Hodnota"]

                            if not isinstance(val, (int, float)):
                                return val
                            if stat in no_unit_stats:
                                return f"{val:.2f}"
                            return f"{val:.2f} €/MWh"

                        summary_df["Hodnota"] = summary_df.apply(format_value, axis=1)

                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať súhrn: {e}")

                with tab3:
                    try:
                        quantiles = am.calculate_quantiles(df, 'price')

                        quantiles_df = pd.DataFrame(
                            list(quantiles.items()),
                            columns=["Kvantil", "Hodnota"]
                        )

                        def format_quantile_value(val):
                            if not isinstance(val, (int, float)):
                                return val
                            return f"{val:,.2f} €/MWh"

                        quantiles_df["Hodnota"] = quantiles_df["Hodnota"].apply(format_quantile_value)

                        st.dataframe(quantiles_df, use_container_width=True, hide_index=True)
                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať kvantily: {e}")

                with tab4:
                    st.dataframe(df, use_container_width=True)