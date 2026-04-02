from typing import Any

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import seaborn as sns
from ridgeplot import ridgeplot

#NEED TO MAKE DOMAIN SPECIFIC FUNCTIONS

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
    # default was -50, 400
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
    fig, ax = plot_line(df, "deliveryStartBA", "DAM_price", "DAM price over 10.2025", "", "Price (€/MWh)",
                            label="DAM15")
    plot_line(df, "deliveryStartBA", "IDM_price", "IDM price over 10.2025", "", "Price (€/MWh)",
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
        x='hourBA',
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

        subset = df[df['hourBA'] == hour]
        sns.violinplot(
            data=subset,
            x='quarterHourBA',
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

    hours = sorted(df['hourBA'].unique())

    samples = [
        df.loc[df['hourBA'] == h, value_col].dropna().values
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