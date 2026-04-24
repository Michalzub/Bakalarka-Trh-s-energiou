from datetime import datetime, date, timedelta, time

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

import analyser_module as am
import visualizer_module as vm
import data_access_module as da
import data_manager as dm


st.set_page_config(
    page_title="Kalkulačka na batériovú arbitráž",
    layout="wide"
)

left, center, right = st.columns([2, 4, 2])
with center:
    st.title("Kalkulačka na batériovú arbitráž")
    st.caption("Vypočíta optimálnu stratégiu na obchodovanie.")


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
        return start_date


    def get_dam_mtu_for_date(selected_date: date) -> int:
        return 60 if (selected_date.year, selected_date.month) < (2025, 10) else 15


    if st.button("Clear cache"):
        st.cache_data.clear()
        st.rerun()

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
            index=0,
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
                disabled=True,
            )
        else:
            mtu = st.selectbox(
                "MTU",
                options=[60, 15],
                index=0,
            )

    end_date = get_range_end(selected_start_date, selected_range)
    st.caption(f"Vybraný rozsah: {selected_start_date} → {end_date}")


    st.subheader("Nastavenia batérie")

    b1, b2, b3, b4 = st.columns(4)

    with b1:
        max_soc_units = st.number_input(
            "Max SOC units",
            min_value=1,
            max_value=100,
            value=2,
            step=1,
            help="Maximálny počet energetických jednotiek v batérii.",
        )

    with b2:
        unit_size = st.number_input(
            "Veľkosť jednotky (MWh)",
            min_value=0.01,
            max_value=100.0,
            value=0.5,
            step=0.1,
            format="%.2f",
            help="Kapacita jednej jednotky batérie.",
        )

    with b3:
        efficiency = st.number_input(
            "Efektivita",
            min_value=0.01,
            max_value=1.0,
            value=0.90,
            step=0.01,
            format="%.2f",
            help="Účinnosť batérie v rozsahu 0 až 1.",
        )

    with b4:
        distribution_cost = st.number_input(
            "Distribučné poplatky (€/MWh)",
            min_value=0.0,
            max_value=1000.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            help="Náklady za distribúciu za každé nabitie/vybitie.",
        )

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

            if df.empty:
                st.error("Načítaný dataset je prázdny.")
                st.stop()

            result = am.calculate_battery_dp(
                df,
                max_soc_units=max_soc_units,
                unit_size=unit_size,
                efficiency=efficiency,
                distribution_cost=distribution_cost,
            )

            st.success("Dataset načítaný a optimálna stratégia vypočítaná.")

            m1, m2 = st.columns(2)
            m1.metric("Počet periód", len(result["df"]["price"]))
            m2.metric("Zisk", f"{result['profit']:.2f} €")

            m3, m4 = st.columns(2)
            m3.metric("Max SOC units", max_soc_units)
            m4.metric("Efektivita", f"{efficiency:.2%}")

            m5 = st.columns(1)[0]
            m5.metric("Cena distribúcie", f"{distribution_cost:.2f} €/MWh")

            st.subheader("Vizualizácia")

            fig = vm.plot_battery_dp_result(result)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            with st.expander("Náhľad datasetu", expanded=True):
                tab1, tab2 = st.tabs(["Akčné body", "Dáta"])
                with tab1:
                    st.dataframe(vm.battery_output_dataframe(result), use_container_width=True)
                with tab2:
                    st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Nepodarilo sa načítať dataset alebo spracovať battery arbitrage: {e}")


    st.divider()