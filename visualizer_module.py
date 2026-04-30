import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np

def plot_line(
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = None,
        xname: str = None,
        yname: str = None,
):
    df = df.copy()

    if xname is None:
        xname = x

    if yname is None:
        yname = y

    fig, ax = plt.subplots(figsize=(16, 5))

    ax.plot(df[x], df[y])

    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xname)
    ax.set_ylabel(yname)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    plt.close(fig)

    return fig, ax

def add_intermarket_spread_scatter(
        df: pd.DataFrame,
        title: str = None,
        visibility_lines: bool = True,
):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.plot([-50, 400], [-50, 400], color='red', linestyle='--', linewidth=1, label='x=y')
    if visibility_lines:
        ax.plot([-50, 400], [-0, 450], color='gray', linestyle='--', linewidth=1, label='x=y')
        ax.plot([0, 400], [-50, 350], color='gray', linestyle='--', linewidth=1, label='x=y')
    ax.scatter(df['DAM_price'], df['IDM_price'], alpha=0.5)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Cena DAM (€/MWh)")
    ax.set_ylabel("Cena IDM (€/MWh)")
    ax.set_xlim(-50, 400)
    ax.set_ylim(-50, 400)
    ax.grid(True)
    plt.close(fig)
    return fig, ax

def battery_output_dataframe(result):
    rows = []

    df = result["df"]
    soc_path = result["soc_path"]
    unit_size = result["unit_size"]

    if "deliveryStart" in df.columns:
        time_col = "deliveryStart"
        time_label = "Začiatok dodávky"
    else:
        time_col = None
        time_label = "Index"

    for t, _, action in result["action_points"]:
        if time_col is None:
            time_value = t
        else:
            time_value = df.loc[t, time_col]
        rows.append({
            time_label: time_value,
            "Cena (€/MWh)": df.loc[t, "price"],
            "Akcia": action,
            "Stav (jednotky)": soc_path[t + 1],
            "Stav nabitia (MWh)": soc_path[t + 1] * unit_size
        })

    return pd.DataFrame(rows)


def plot_weekday_bar(df: pd.DataFrame, title:str, ylabel:str):

    days = ['Po', 'Ut', 'St', 'Št', 'Pi', 'So', 'Ne']

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ['blue', 'blue', 'blue', 'blue', 'blue', 'orange', 'orange']
    ax.bar([days[i] for i in df.index], df.values, color=colors)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel('Deň v týždni')
    ax.set_ylabel(ylabel)

    plt.close(fig)
    return fig, ax

def plot_hourly_line(df, title:str):
    df = df.copy()

    hourly = df.groupby('hour')['price'].mean()

    fig, ax = plt.subplots(figsize=(8, 4))
    plt.plot(hourly.index, hourly.values)

    ax.set_xlabel('Hodina')
    ax.set_ylabel('Priemerná cena (€/MWh)')
    ax.set_title(title,fontsize=14)
    ax.set_xticks(range(0, 24))
    ax.grid(True)

    plt.close(fig)


def plot_intraday_period(df, MTU, title):
    if MTU == 60:
        periodCount = 24
        hourlyJump = 1
    else:
        periodCount = 96
        hourlyJump = 4

    y = df.groupby("period")["price"].mean()
    y = y.reindex(range(1, periodCount + 1))

    fig, ax = plt.subplots(figsize=(16, 5))

    ax.plot(y.index, y.values, marker="o")

    for i in range(1, periodCount + 1, hourlyJump):
        ax.axvline(x=i, linestyle="--", alpha=0.3)

    tick_positions = range(1, periodCount + 1, hourlyJump)
    tick_labels = range(1, periodCount + 1, hourlyJump)

    ax.set_xlabel(f"perióda (1–{periodCount})")
    ax.set_ylabel("Priemerná cena (€/MWh)")
    ax.set_xticks(list(tick_positions))
    ax.set_xticklabels(list(tick_labels))
    ax.set_title(title, fontsize=14)

    fig.tight_layout()
    return fig

def plot_quarter_boxplots(df, column: str,ylabel: str, title:str ="Boxplot", ylimits=None):
    df = df.copy()

    quarter_order = [0, 1, 2, 3]

    fig, axes = plt.subplots(6, 4, figsize=(18, 24), sharey=True)
    axes = axes.flatten()

    for h in range(24):
        ax = axes[h]

        df_h = df[df['hour'] == h]

        sns.boxplot(
            data=df_h,
            x='quarterHour',
            y=column,
            order=quarter_order,
            ax=ax
        )

        ax.set_xticks([0, 1, 2, 3])
        ax.set_xticklabels([
                f"{h:02d}:00",
                f"{h:02d}:15",
                f"{h:02d}:30",
                f"{h:02d}:45"
            ],
            fontsize=14
        )

        ax.tick_params(axis='y', labelsize=14)
        ax.tick_params(axis='x', labelsize=14)

        ax.axhline(0, color='black', linestyle='--', linewidth=1)

        if ylimits is not None:
            ax.set_ylim(ylimits[0], ylimits[1])

        ax.set_title(f'Hodina {h:02d}', fontsize=18)
        ax.set_xlabel('')
        ax.set_ylabel(ylabel if h % 4 == 0 else '', fontsize=16)

    for i in range(24, len(axes)):
        fig.delaxes(axes[i])

    fig.suptitle(title,fontsize=24)

    fig.tight_layout(rect=[0, 0, 1, 0.99])
    return fig, ax

def plot_hour_boxplot(df, column, title: str, ylabel: str, ylimits=None):
    fig, ax = plt.subplots(figsize=(16, 5))
    sns.boxplot(data=df, x='hour', y=column, ax=ax)
    ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('Hour of Day (Europe/Bratislava)')
    ax.set_ylabel(ylabel)

    if ylimits is not None:
        ax.set_ylim(ylimits[0], ylimits[1])

    return fig, ax

def plot_battery_dp_result(result, MTU, title:str):
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
        color="blue",
        label="Cena elektriny (€/MWh)",
        linewidth=2,
        alpha=0.7
    )

    for t, price, action_type in action_points:
        if action_type == "charge":
            ax1.scatter(t, price, color="green", marker="^", s=100)
        else:
            ax1.scatter(t, price, color="red", marker="v", s=100)

    ax1.scatter([], [], color="green", marker="^", s=120, label="Nákup (Charge)")
    ax1.scatter([], [], color="red", marker="v", s=120, label="Predaj (Discharge)")

    ax1.set_xlabel(f"Perióda ({MTU}-min intervaly)")
    ax1.set_ylabel("Cena (€/MWh)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.step(range(len(soc_path)),
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

    plt.title(f"{title} (Zisk: {profit:.2f} €)", fontsize=14)
    plt.close(fig)
    return fig