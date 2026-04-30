from datetime import date, timedelta

import pandas as pd
import streamlit as st

import visualizer_module as viz
import data_access_module as da
import data_processor as dp
import analyser_module as am

PAGE_ID = "dam_idm_compare"
MTU_CHANGE_DATE = date(2025, 10, 1)

st.set_page_config(page_title="Porovnanie DAM a IDM", layout="wide")

def load_data(start_date, end_date, market_type):
    df = da.get_okte_data_simple(market_type, start_date, end_date)
    return dp.prep_okte_data(df)


def get_date_range(start_date: date, range_option: str) -> tuple[date, date]:
    if range_option == "7 dní":
        return start_date, start_date + timedelta(days=6)

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
    return 60 if selected_date < MTU_CHANGE_DATE else 15


def crosses_dam_mtu_change(start_date: date, end_date: date) -> bool:
    return start_date < MTU_CHANGE_DATE <= end_date


def merge_with_spread(dam_df: pd.DataFrame, idm_df: pd.DataFrame) -> pd.DataFrame:
    df = dp.merge_dam_idm_prices(dam_df, idm_df)
    df = dp.calculate_intermarket_spread(df)
    df = dp.add_time_features(df)
    return df


def build_comparison_variants(
        dam_df: pd.DataFrame,
        idm_df: pd.DataFrame,
        dam_mtu: int,
        idm_mtu: int
) -> dict:
    if dam_mtu == 60 and idm_mtu == 60:
        return {
            "DAM60 vs IDM60": {
                "df": merge_with_spread(dam_df, idm_df),
                "mtu": 60
            }
        }

    if dam_mtu == 60 and idm_mtu == 15:
        return {
            "DAM60 vs IDM15→60": {
                "df": merge_with_spread(
                    dam_df,
                    dp.aggregate_hour(idm_df, "price")
                ),
                "mtu": 60
            },
            "DAM60 hodinová referencia vs IDM15": {
                "df": merge_with_spread(
                    dp.replicate_hour_to_quarter(dam_df),
                    idm_df
                ),
                "mtu": 15
            }
        }

    if dam_mtu == 15 and idm_mtu == 15:
        return {
            "DAM15 vs IDM15": {
                "df": merge_with_spread(dam_df, idm_df),
                "mtu": 15
            }
        }

    if dam_mtu == 15 and idm_mtu == 60:
        return {
            "DAM15 vs IDM60 hodinová referencia": {
                "df": merge_with_spread(
                    dam_df,
                    dp.replicate_hour_to_quarter(idm_df)
                ),
                "mtu": 15
            },
            "DAM15→60 vs IDM60": {
                "df": merge_with_spread(
                    dp.aggregate_hour(dam_df, "price"),
                    idm_df
                ),
                "mtu": 60
            }
        }

    raise ValueError(f"Nepodporovaná kombinácia MTU: DAM{dam_mtu}, IDM{idm_mtu}")


def render_comparison(df: pd.DataFrame, dataset_mtu: int, title: str):
    try:
        corr = am.calculate_corr(df, "DAM_price", df, "IDM_price")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Korelačný koeficient cien", f"{corr:.4f}")

        with col2:
            st.metric("Počet spoločných periód", len(df))

    except Exception as e:
        st.error(f"Nepodarilo sa vypočítať koreláciu: {e}")

    tab1, tab2, tab3 = st.tabs([
        "Scatterplot",
        "Boxplot spreadu",
        "Dáta"
    ])

    with tab1:
        try:
            fig, ax = viz.add_intermarket_spread_scatter(
                df,
                title=f"Scatterplot cien {title}",
                visibility_lines=True
            )
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Nepodarilo sa vykresliť scatterplot: {e}")

    with tab2:
        try:
            if dataset_mtu == 60:
                fig, ax = viz.plot_hour_boxplot(
                    df=df,
                    column="spread",
                    title=f"Rozdelenia spreadu DAM - IDM podľa hodiny {title}",
                    ylabel="Spread DAM - IDM (€/MWh)"
                )
            else:
                fig, ax = viz.plot_quarter_boxplots(
                    df=df,
                    column="spread",
                    title=f"Rozdelenia spreadu DAM - IDM podľa štvrťhodiny {title}",
                    ylabel="Spread DAM - IDM (€/MWh)"
                )

            st.pyplot(fig)

        except Exception as e:
            st.error(f"Nepodarilo sa vykresliť boxplot rozdielov: {e}")

    with tab3:
        st.dataframe(df, use_container_width=True)


if PAGE_ID not in st.session_state:
    st.session_state[PAGE_ID] = {"datasets": {}}

if "datasets" not in st.session_state[PAGE_ID]:
    st.session_state[PAGE_ID]["datasets"] = {}

datasets = st.session_state[PAGE_ID]["datasets"]

left, center, right = st.columns([2, 4, 2])

with center:
    st.title("Porovnanie DAM a IDM")

    col1, col2, col3 = st.columns(3)

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
            options=["7 dní", "1 mesiac", "3 mesiace"],
            index=1,
            key=f"{PAGE_ID}_range"
        )

    start_date, end_date = get_date_range(selected_start_date, selected_range)
    dam_mtu = get_dam_mtu_for_date(start_date)
    invalid_range = crosses_dam_mtu_change(start_date, end_date)

    with col3:
        idm_mtu = st.selectbox(
            "IDM MTU",
            options=[60, 15],
            index=1 if dam_mtu == 15 else 0,
            key=f"{PAGE_ID}_idm_mtu"
        )

    date_label = f"{start_date} → {end_date}"

    st.caption(
        f"Vybraný rozsah: {date_label} | "
        f"DAM MTU {dam_mtu} | IDM MTU {idm_mtu}"
    )

    if invalid_range:
        st.error(
            "Vybraný rozsah prechádza cez 1. 10. 2025, kedy sa zmenilo DAM MTU. "
            "Vyber rozsah celý pred týmto dátumom alebo celý od 1. 10. 2025 vrátane."
        )

    load_clicked = st.button(
        "Načítať dataset",
        key=f"{PAGE_ID}_load",
        disabled=invalid_range
    )

    if load_clicked:
        try:
            with st.spinner("Načítavam dáta..."):
                dam_df = load_data(start_date, end_date, "DAM")
                idm_df = load_data(start_date, end_date, f"IDM{idm_mtu}")

                variants = build_comparison_variants(
                    dam_df=dam_df,
                    idm_df=idm_df,
                    dam_mtu=dam_mtu,
                    idm_mtu=idm_mtu
                )

            key = f"DAM{dam_mtu} vs IDM{idm_mtu} | {date_label}"

            datasets[key] = {
                "variants": variants,
                "dam_mtu": dam_mtu,
                "idm_mtu": idm_mtu,
                "date_label": date_label
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
        st.subheader("Vizualizácia a dáta")

        for key, dataset in datasets.items():
            variants = dataset["variants"]
            date_label = dataset["date_label"]

            with st.expander(key, expanded=True):

                if len(variants) == 1:
                    variant_name = list(variants.keys())[0]
                    variant = variants[variant_name]

                    st.markdown(f"### {variant_name}")

                    render_comparison(
                        df=variant["df"],
                        dataset_mtu=variant["mtu"],
                        title=f"{variant_name} | {date_label}"
                    )

                else:
                    variant_tabs = st.tabs(list(variants.keys()))

                    for tab, variant_name in zip(variant_tabs, variants.keys()):
                        variant = variants[variant_name]

                        with tab:
                            st.markdown(f"### {variant_name}")

                            render_comparison(
                                df=variant["df"],
                                dataset_mtu=variant["mtu"],
                                title=f"{variant_name} | {date_label}"
                            )