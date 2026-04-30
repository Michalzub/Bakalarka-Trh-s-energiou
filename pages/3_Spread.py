from datetime import datetime, date, timedelta, time

import pandas as pd
import streamlit as st

import analyser_module as am
import visualizer_module as vm
import data_access_module as da
import data_processor as dp

@st.cache_data
def load_data(start_date, end_date, market_type):
    df = da.get_okte_data_simple(market_type, start_date, end_date)
    return dp.prep_okte_data(df)


def get_date_range(start_date: date, range_option: str) -> tuple[date, date]:
    if range_option == "1 deň":
        return start_date, start_date

    elif range_option == "2 dni":
        return start_date, start_date + timedelta(days=1)

    elif range_option == "3 dni":
        return start_date, start_date + timedelta(days=2)

    elif range_option == "1 mesiac":
        range_start = start_date.replace(day=1)
        next_month = (range_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        range_end = next_month - timedelta(days=1)
        return range_start, range_end

    elif range_option == "3 mesiace":
        range_start = start_date.replace(day=1)

        month_index = range_start.month - 1 + 3
        year = range_start.year + month_index // 12
        month = month_index % 12 + 1

        next_period = date(year, month, 1)
        range_end = next_period - timedelta(days=1)

        return range_start, range_end

    else:
        return start_date, start_date


def get_dam_mtu_for_date(selected_date: date) -> int:
    return 60 if (selected_date.year, selected_date.month) < (2025, 10) else 15


def should_aggregate_by_period(range_option: str) -> bool:
    return range_option in ["1 mesiac", "3 mesiace"]


st.set_page_config(
    page_title="Kalkulačka na batériovú arbitráž",
    layout="wide"
)

left, center, right = st.columns([2, 4, 2])

with center:
    st.title("Kalkulačka na batériovú arbitráž")
    st.caption("Vypočíta optimálnu stratégiu na obchodovanie.")

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
            options=["1 deň", "2 dni", "3 dni", "1 mesiac", "3 mesiace"],
            index=0,
        )

    with col3:
        market_type = st.selectbox("Typ trhu", ["DAM", "IDM"])

    start_date, end_date = get_date_range(selected_start_date, selected_range)
    auto_dam_mtu = get_dam_mtu_for_date(start_date)

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

    aggregate_periods = should_aggregate_by_period(selected_range)

    st.caption(f"Vybraný rozsah: {start_date} → {end_date}")

    if aggregate_periods:
        st.info(
            "Pri rozsahu 1 mesiac alebo 3 mesiace sa dáta pred výpočtom agregujú podľa periódy. "
            "Výsledok teda predstavuje optimalizáciu nad priemerným denným profilom cien."
        )

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
            max_value=10.0,
            value=0.5,
            step=0.25,
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
            value=50.0,
            step=10.0,
            format="%.2f",
            help="Náklady za distribúciu za každé nabitie.",
        )

    load_clicked = st.button("Načítať dataset")

    if load_clicked:
        dt1 = datetime.combine(start_date, time.min)
        dt2 = datetime.combine(end_date, time.min)

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

            title = f"Simulácia spreadového obchodovania s batériou | {start_date} - {end_date}"

            if aggregate_periods:
                df = dp.remove_nonstandard_days(df)
                df = dp.groupby_period_mean(df,'price')
                title = f"Simulácia spreadového obchodovania s batériou podľa indexu periódy dňa | {start_date} - {end_date}"

            result = am.calculate_battery_arbitrage(
                df=df,
                max_soc_units=max_soc_units,
                unit_size=unit_size,
                efficiency=efficiency,
                distribution_cost=distribution_cost,
            )

            st.success("Dataset načítaný a optimálna stratégia vypočítaná.")

            m1, m2 = st.columns(2)
            m1.metric("Počet periód", len(result["df"]["price"]))

            if aggregate_periods:
                m2.metric("Zisk modelového dňa", f"{result['profit']:.2f} €")
            else:
                m2.metric("Zisk", f"{result['profit']:.2f} €")

            m3, m4 = st.columns(2)
            m3.metric("Max SOC units", max_soc_units)
            m4.metric("Efektivita", f"{efficiency:.2%}")

            m5 = st.columns(1)[0]
            m5.metric("Cena distribúcie", f"{distribution_cost:.2f} €/MWh")

            st.subheader("Vizualizácia")

            fig = vm.plot_battery_dp_result(result, mtu, title)
            st.pyplot(fig, use_container_width=True)

            with st.expander("Náhľad datasetu", expanded=True):
                tab1, tab2 = st.tabs(["Akčné body", "Dáta"])

                with tab1:
                    st.dataframe(vm.battery_output_dataframe(result))

                with tab2:
                    st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Nepodarilo sa načítať dataset alebo spracovať battery arbitrage: {e}")

    st.divider()