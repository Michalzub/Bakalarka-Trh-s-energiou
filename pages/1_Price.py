from datetime import datetime, date, time, timedelta

import pandas as pd
import streamlit as st

import visualizer_module as viz
import data_access_module as da
import data_processor as dp
import analyser_module as am

PAGE_ID = "price"
MTU_CHANGE_DATE = date(2025, 10, 1)

st.set_page_config(page_title="Analýza cien", layout="wide")


def load_data(start_date, end_date, market_type):
    df = da.get_okte_data_simple(market_type, start_date, end_date)
    return dp.prep_okte_data(df)


def get_date_range(start_date: date, range_option: str) -> tuple[date, date]:
    if range_option == "1 deň":
        return start_date, start_date

    elif range_option == "3 dni":
        return start_date, start_date + timedelta(days=2)

    elif range_option == "7 dní":
        return start_date, start_date + timedelta(days=6)

    elif range_option == "Celý mesiac":
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
    return 60 if selected_date < MTU_CHANGE_DATE else 15


def crosses_dam_mtu_change(start_date: date, end_date: date) -> bool:
    return start_date < MTU_CHANGE_DATE <= end_date


if PAGE_ID not in st.session_state:
    st.session_state[PAGE_ID] = {"datasets": {}}

if "datasets" not in st.session_state[PAGE_ID]:
    st.session_state[PAGE_ID]["datasets"] = {}

datasets = st.session_state[PAGE_ID]["datasets"]

left, center, right = st.columns([2, 4, 2])

with center:
    st.title("Analýza cien")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_start_date = st.date_input(
            "Dátum začiatku",
            value=date(2025, 10, 1),
            min_value=date(2020, 1, 1),
            max_value=date(2026, 12, 31),
            key=f"{PAGE_ID}_start"
        )

    with col2:
        selected_range = st.selectbox(
            "Časový rozsah",
            options=["1 deň", "3 dni", "7 dní", "Celý mesiac", "3 mesiace"],
            index=3,
            key=f"{PAGE_ID}_range"
        )

    with col3:
        market_type = st.selectbox(
            "Typ trhu",
            ["DAM", "IDM"],
            key=f"{PAGE_ID}_market"
        )

    start_date, end_date = get_date_range(selected_start_date, selected_range)
    auto_dam_mtu = get_dam_mtu_for_date(start_date)

    with col4:
        if market_type == "DAM":
            mtu = st.selectbox(
                "MTU",
                options=[auto_dam_mtu],
                index=0,
                disabled=True,
                key=f"{PAGE_ID}_mtu_dam"
            )
        else:
            mtu = st.selectbox(
                "MTU",
                options=[60, 15],
                index=0,
                key=f"{PAGE_ID}_mtu_idm"
            )

    invalid_range = market_type == "DAM" and crosses_dam_mtu_change(start_date, end_date)

    st.caption(f"Vybraný rozsah: {start_date} → {end_date}")

    if invalid_range:
        st.error(
            "Vybraný DAM rozsah prechádza cez 1. 10. 2025, kedy sa zmenilo DAM MTU. "
            "Takýto rozsah nie je možné načítať naraz. Vyber rozsah celý pred 1. 10. 2025 "
            "alebo celý od 1. 10. 2025 vrátane."
        )

    load_clicked = st.button(
        "Načítať dataset",
        key=f"{PAGE_ID}_load",
        disabled=invalid_range
    )

    if load_clicked:

        if market_type == "DAM":
            effective_market_type = "DAM"
        else:
            effective_market_type = f"IDM{mtu}"

        try:
            with st.spinner("Načítavam dáta..."):
                df = load_data(start_date, end_date, effective_market_type)

            key = (
                f"{market_type} | {start_date} → {end_date}"
                f" | MTU {mtu}"
            )

            datasets[key] = {
                "df": df,
                "mtu": mtu,
                "market_type": market_type
            }

            st.success(f"Dataset načítaný: {key}")

        except Exception as e:
            st.error(f"Nepodarilo sa načítať dataset: {e}")

    st.subheader("Načítané datasety")

    if not datasets:
        st.info("Zatiaľ nie sú načítané žiadne datasety.")
    else:
        for key in list(datasets.keys()):
            col1, col2 = st.columns([8, 1])

            with col1:
                st.write(key)

            with col2:
                if st.button("❌", key=f"{PAGE_ID}_remove_{key}"):
                    del datasets[key]
                    st.rerun()

    if datasets:
        st.divider()

        with st.expander("Globálny prehľad štatistík"):
            overall_tab1, overall_tab2 = st.tabs([
                "Cena",
                "Medziperiodné rozdiely cien"
            ])

            with overall_tab1:
                all_price_summaries = {}
                all_price_quantiles = {}

                for key, dataset in datasets.items():
                    try:
                        all_price_summaries[key] = am.price_summary_statistics(dataset["df"])
                        all_price_quantiles[key] = am.calculate_quantiles(dataset["df"], "price")
                    except Exception as e:
                        st.error(f"Chyba pri spracovaní datasetu {key}: {e}")
                        continue

                if all_price_summaries:
                    st.markdown("### Základné štatistiky")
                    st.dataframe(
                        pd.DataFrame(all_price_summaries),
                        use_container_width=True
                    )
                if all_price_quantiles:
                    st.markdown("### Kvantily")
                    st.dataframe(
                        pd.DataFrame(all_price_quantiles),
                        use_container_width=True
                    )

            with overall_tab2:
                all_diff_summaries = {}

                for key, dataset in datasets.items():
                    try:
                        all_diff_summaries[key] = am.price_diff_summary_statistics(dataset["df"])
                    except Exception as e:
                        st.error(f"Chyba pri spracovaní datasetu {key}: {e}")
                        continue

                if all_diff_summaries:
                    st.markdown("### Základné štatistiky")
                    st.dataframe(
                        pd.DataFrame(all_diff_summaries),
                        use_container_width=True
                    )

    if datasets:
        st.divider()
        st.subheader("Vizualizácia a dáta")

        for key, dataset in datasets.items():
            df = dataset["df"]
            dataset_mtu = dataset["mtu"]
            dataset_market_type = dataset["market_type"]

            with st.expander(key, expanded=True):

                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "Priebeh",
                    "Štatistiky cien",
                    "Štatistiky rozdielov",
                    "Intraday ceny",
                    "Intraday rozdiely",
                    "Dáta"
                ])

                with tab1:
                    try:
                        fig, ax = viz.plot_line(
                            df=df,
                            x="deliveryStart",
                            y="price",
                            title=f"Priebeh cien {key}",
                            xname="Čas dodávky",
                            yname="Cena (€/MWh)"
                        )
                        st.pyplot(fig)

                    except Exception as e:
                        st.error(f"Nepodarilo sa vykresliť graf: {e}")

                with tab2:
                    try:
                        st.markdown("### Základné štatistiky cien")

                        price_summary = am.price_summary_statistics(df)

                        st.dataframe(
                            pd.DataFrame(price_summary, index=["Hodnota"]).T,
                            use_container_width=True
                        )

                        st.markdown("### Kvantily cien")

                        price_quantiles = am.calculate_quantiles(df, "price")

                        st.dataframe(
                            pd.DataFrame(price_quantiles, index=["Cena €/MWh"]).T,
                        )

                    except Exception as e:
                        st.error(f"Nepodarilo sa vypočítať štatistiky cien: {e}")

                with tab3:
                    try:
                        st.markdown("### Štatistiky medziperiodných rozdielov cien")

                        diff_summary = am.price_diff_summary_statistics(df)

                        st.dataframe(
                            pd.DataFrame(diff_summary, index=["Hodnota"]).T,
                        )

                    except Exception as e:
                        st.error(f"Nepodarilo sa vypočítať štatistiky rozdielov cien: {e}")

                with tab4:
                    try:
                        fig = viz.plot_intraday_period(
                            df,
                            dataset_mtu,
                            f"Priemerná cena za periódu dňa {key}"
                        )
                        st.pyplot(fig)

                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať intraday priebeh: {e}")

                    try:
                        if dataset_mtu == 60:
                            fig, ax = viz.plot_hour_boxplot(
                                df=df,
                                column="price",
                                title="Boxplot cien podľa hodiny",
                                ylabel="Cena (€/MWh)"
                            )
                        else:
                            fig, ax = viz.plot_quarter_boxplots(
                                df=df,
                                column="price",
                                ylabel="Cena (€/MWh)",
                                title=f"Box plot cien za štvrť hodinu dňa {key}"
                            )

                        st.pyplot(fig)

                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať boxplot cien: {e}")

                    try:
                        if dataset_mtu == 60:
                            time_summary = am.calculate_time_summary(
                                df=df,
                                quarter=False,
                                column="price"
                            )
                        else:
                            time_summary = am.calculate_time_summary(
                                df=df,
                                quarter=True,
                                column="price"
                            )

                        st.dataframe(time_summary, use_container_width=True)

                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať súhrn cien podľa času: {e}")

                with tab5:
                    try:
                        if dataset_mtu == 60:
                            fig, ax = viz.plot_hour_boxplot(
                                df=df,
                                column="price_diff",
                                title=f"Boxplot medziperiodných rozdielov podľa hodiny {key}",
                                ylabel="Zmena ceny (€/MWh)"
                            )
                        else:
                            fig, ax = viz.plot_quarter_boxplots(
                                df=df,
                                column="price_diff",
                                ylabel="Zmena ceny (€/MWh)",
                                title=f"Boxplot medziperiodných rozdielov podľa štvrť hodiny {key}",
                            )

                        st.pyplot(fig)

                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať boxplot rozdielov: {e}")

                    try:
                        if dataset_mtu == 60:
                            time_summary = am.calculate_time_summary(
                                df=df,
                                quarter=False,
                                column="price_diff"
                            )
                        else:
                            time_summary = am.calculate_time_summary(
                                df=df,
                                quarter=True,
                                column="price_diff"
                            )

                        st.dataframe(time_summary, use_container_width=True)

                    except Exception as e:
                        st.error(f"Nepodarilo sa vygenerovať súhrn rozdielov podľa času: {e}")

                with tab6:
                    st.dataframe(df, use_container_width=True)