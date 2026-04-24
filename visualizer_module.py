from typing import Any

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import seaborn as sns
from ridgeplot import ridgeplot
import numpy as np

#NEED TO MAKE DOMAIN SPECIFIC FUNCTIONS

def add_dev_scatter(axis, title, data):
    axis.plot([-50, 400], [-50, 400], color='red', linestyle='--', linewidth=1, label='x=y')
    axis.plot([-50, 400], [-0, 450], color='gray', linestyle='--', linewidth=1, label='x=y')
    axis.plot([0, 400], [-50, 350], color='gray', linestyle='--', linewidth=1, label='x=y')
    axis.scatter(data['DAM_price'], data['IDM_price'], alpha=0.5)
    axis.set_title(title)
    axis.set_xlabel("DAM Price (€/MWh)")
    axis.set_ylabel("IDM Price (€/MWh)")
    axis.set_xlim(-50, 400)
    axis.set_ylim(-50, 400)
    axis.grid(True)


def plot_scatter(
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str | None = None,
        xname: str | None = None,
        yname: str | None = None,
        figsize: tuple[float,float] | None = (6, 6),
        limits: tuple[float,float] | None = (-50, 400),

) -> Figure:
    if xname is None:
        xname = x
    if yname is None:
        yname = y

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(df[x], df[y], alpha=0.5)
    ax.set_title(title)
    ax.set_xlabel(xname)
    ax.set_ylabel(yname)
    ax.set_xlim(limits)
    ax.set_ylim(limits)
    ax.grid(True)
    ax.plot(limits, limits, linestyle="--", color="gray")
    plt.close(fig)
    return fig

def plot_dam_idm_price_scatter(df: pd.DataFrame)-> Figure:
    return plot_scatter(df, "DAM_price", "IDM_price", xname="DAM Price (€/MWh)", yname="IDM Price (€/MWh)")

def plot_line(
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str | None = None,
        xname: str | None = None,
        yname: str | None = None,
        ax=None,
        figsize: tuple[float, float] | None = (14, 4),
        label= None,
) -> tuple[Figure, Axes]:
    if xname is None:
        xname = x
    if yname is None:
        yname = y

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    ax.plot(df[x], df[y], label = label)
    ax.set_title(title)
    ax.set_xlabel(xname)
    ax.set_ylabel(yname)
    ax.grid(True)
    plt.close(fig)
    return fig, ax

def plot_dam_idm_line(df: pd.DataFrame) -> Figure:
    fig, ax = plot_line(df, "deliveryStart", "DAM_price", "DAM price over 10.2025", "", "Price (€/MWh)",
                            label="DAM15")
    plot_line(df, "deliveryStart", "IDM_price", "IDM price over 10.2025", "", "Price (€/MWh)",
                  ax=ax, label="DAM15")
    ax.legend()
    return fig


def plot_box(
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str | None = None,
        xname: str | None = None,
        yname: str | None = None,
        figsize: tuple[float, float] | None = (6, 6),
        limits: tuple[float, float] | None = (-100, 100),
):
    if xname is None:
        xname = x
    if yname is None:
        yname = y

    fig, ax = plt.subplots(figsize=figsize)

    sns.boxplot(data=df, x=x, y=y, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xname)
    ax.set_ylabel(yname)
    ax.set_ylim(limits)
    plt.close(fig)
    return fig

def plot_dam_idm_spread_box(
        df: pd.DataFrame
):
    fig = plot_box(
        df,
        x='hour',
        y='dam_idm_spread',
        title="Deviation per hour of day October 2025",
        xname='Hour of Day (Europe/Bratislava)',
        yname='deviation (€/MWh)',
        figsize=(10, 8),
    )
    return fig

def plot_violin_quarterly_price(
        df: pd.DataFrame,
):
    fig, axes = plt.subplots(6, 4, figsize=(18, 24))
    axes = axes.flatten()

    for i, hour in enumerate(range(24)):
        ax = axes[i]

        subset = df[df['hour'] == hour]
        sns.violinplot(
            data=subset,
            x='quarterHour',
            y='price',
            hue='market',
            split=True,
            inner='quartile',
            cut=1,
            density_norm='width',
            ax=ax
        )
        ax.set_title(f'Hour {hour:02d}')
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xticklabels(['00–15', '15–30', '30–45', '45–60'])
        ax.set_xlabel('')
        ax.set_ylim(-50, 400)


        if i % 4 == 0:
            ax.set_ylabel('Price (€/MWh)')
        ax.grid(True)
    plt.close(fig)
    return fig

def plot_ridge_hourly(
        df: pd.DataFrame,
        value_col: str,
        title: str | None = None,
        xname: str | None = None,
) -> Figure:

    if xname is None:
        xname = value_col

    hours = sorted(df['hour'].unique())

    samples = [
        df.loc[df['hour'] == h, value_col].dropna().values
        for h in hours
    ]

    labels = [f"{h:02d}:00" for h in hours]

    fig = ridgeplot(
        samples=samples,
        labels=labels,
        bandwidth=3,
        colorscale="viridis",
        colormode="row-index",
        opacity=0.6,
    )

    fig.update_layout(
        title=title,
        height=1000,
        width=1200,
        font_size=14,
        yaxis_title="Hour",
        xaxis_title=xname,
        showlegend=False )
    return fig

#    df["qh"] = (df["deliveryStartBA"].dt.hour * 4 + df["deliveryStartBA"].dt.minute // 15)

#generic + domain

def plot_hist(
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str | None = None,
        xname: str | None = None,
        yname: str | None = None,
        figsize: tuple[float, float] | None = (3, 5),

):
    if xname is None:
        xname = x
    if yname is None:
        yname = y

    fig, ax = plt.subplots( figsize=figsize)

    #not like this
    qh_mean = df.groupby(x, as_index=True)[y].mean()


    ax.bar(qh_mean.index, qh_mean.values)
    ax.set_xticks(ticks=list(range(0, 96, 4)),)
    ax.set_title(title)
    ax.set_xlabel(xname)
    ax.set_ylabel(yname)
    plt.close(fig)
    return fig

def plot_battery_dp_result(result):
    df = result["df"]
    soc_path = result["soc_path"]
    action_points = result["action_points"]
    profit = result["profit"]
    unit_size = result["unit_size"]
    max_soc_units = result["max_soc_units"]
    prices = df['price']

    fig, ax1 = plt.subplots(figsize=(18, 7))

    ax1.plot(
        prices,
        color="royalblue",
        label="Cena elektriny (€/MWh)",
        linewidth=2,
        alpha=0.7
    )

    for t, price, action_type in action_points:
        if action_type == "charge":
            ax1.scatter(t, price, color="green", marker="^", s=120, zorder=5)
        else:
            ax1.scatter(t, price, color="red", marker="v", s=120, zorder=5)

    ax1.scatter([], [], color="green", marker="^", s=120, label="Nákup (Charge)")
    ax1.scatter([], [], color="red", marker="v", s=120, label="Predaj (Discharge)")

    ax1.set_xlabel("Perióda (15-min intervaly)")
    ax1.set_ylabel("Cena (€/MWh)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.step(
        range(len(soc_path)),
        np.array(soc_path) * unit_size,
        where="post",
        color="orange",
        alpha=0.5,
        label="SoC (MWh)"
    )
    ax2.set_ylabel("Stav nabitia (MWh)")
    ax2.set_ylim(0, (max_soc_units * unit_size) + 0.5)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left", frameon=True, shadow=True)

    for i in range(0, len(prices) + 1, 4):
        ax1.axvline(x=i, linestyle="--", color="gray", alpha=0.2)

    plt.title(f"DP Analýza: (Zisk: {profit:.2f} €)")
    return fig

def battery_output_dataframe(result):
    rows = []

    df = result["df"]
    soc_path = result["soc_path"]
    unit_size = result["unit_size"]

    for t, _, action in result["action_points"]:
        rows.append({
            "deliveryStart": df.loc[t, "deliveryStart"],
            "price": df.loc[t, "price"],
            "action": action,
            "soc_units": soc_path[t + 1],  # aligned with your previous logic
            "soc_mwh": soc_path[t + 1] * unit_size
        })

    return pd.DataFrame(rows)