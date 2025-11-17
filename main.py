import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import json


def hourly_period(row):
    time = row['deliveryStart'].minute
    if time == 00:
        return 1
    elif time == 15:
        return 2
    elif time == 30:
        return 3
    elif time == 45:
        return 4
    else:
        return 0

#------------------------------------------------Data collection method--------------------------------------------------------------------
def collect_data():
    septemberDAMResponse = requests.get("https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-09-01&deliveryDayTo=2025-09-30")
    octoberDAMResponse = requests.get("https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-10-01&deliveryDayTo=2025-10-31")
    with open('septemberDAMJSON.json', 'w', encoding='utf-8') as f:
        json.dump(septemberDAMResponse.json(), f)
    with open('octoberDAMJSON.json', 'w', encoding='utf-8') as f:
        json.dump(octoberDAMResponse.json(), f)

    septemberIDMResponse = requests.get("https://isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2025-09-1&deliveryDayTo=2025-09-30")
    octoberIDMResponse = requests.get("https://isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2025-10-1&deliveryDayTo=2025-10-31")
    with open('septemberIDMJSON.json', 'w', encoding='utf-8') as f:
        json.dump(septemberIDMResponse.json(), f)
    with open('octoberIDMJSON.json', 'w', encoding='utf-8') as f:
        json.dump(octoberIDMResponse.json(), f)


#-------------------------------------------Data collection call--------------------------------------------------------------

#collect_data()

#------------------------------------------------DAM SETUP--------------------------------------------------------------------

septemberDAM = pd.read_json('septemberDAMJSON.json')
octoberDAM = pd.read_json('octoberDAMJSON.json')

septemberDAM['deliveryDay'] = pd.to_datetime(septemberDAM['deliveryDay'])
septemberDAM['deliveryStart'] = pd.to_datetime(septemberDAM['deliveryStart'])
septemberDAM['deliveryEnd'] = pd.to_datetime(septemberDAM['deliveryEnd'])
septemberDAM['timeStart'] = septemberDAM['deliveryStart'].dt.hour + septemberDAM['deliveryStart'].dt.minute/60

octoberDAM['deliveryDay'] = pd.to_datetime(octoberDAM['deliveryDay'])
octoberDAM['deliveryStart'] = pd.to_datetime(octoberDAM['deliveryStart'])
octoberDAM['deliveryEnd'] = pd.to_datetime(octoberDAM['deliveryEnd'])
octoberDAM['timeStart'] = octoberDAM['deliveryStart'].dt.hour + octoberDAM['deliveryStart'].dt.minute/60

#-------------------------------------------OCTOBER VS SEPTEMBER-------------------------------------------

septemberDays = septemberDAM.groupby('deliveryDay')[['price', 'deliveryStart', 'deliveryEnd', 'timeStart']]
octoberDays = octoberDAM.groupby('deliveryDay')[['price', 'deliveryStart', 'deliveryEnd', 'timeStart']]

dovs, dovsax = plt.subplots()

for day, group in septemberDays:
    group = group.sort_values('timeStart')
    dovsax.step(group['timeStart'], group['price'], label=str(day), color='orange', alpha=0.75, where='post')

for day, group in octoberDays:
    group = group.sort_values('timeStart')
    dovsax.step(group['timeStart'], group['price'], label=str(day), color='blue', alpha=0.75, where='post')



dovsax.set_title("DAM Price over time")
dovsax.set_xlabel('Delivery Start')
dovsax.set_ylabel('Price')
dovsax.yaxis.set_major_formatter("{x:,.2f}€")
dovsax.xaxis.set_major_locator(mticker.MultipleLocator(1))
dovsax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f"{int(x):02d}:00"))
dovsax.tick_params(axis='x', rotation=90)
legend_elements = [
    Line2D([0], [0], color='blue', lw=2, label='September (60min period)'),
    Line2D([0], [0], color='orange', lw=2, label='October (15min period)')
]
plt.legend(handles=legend_elements)
plt.tight_layout()
plt.show()


# summary comparison------------------------------
september_summary = septemberDAM[['price']].describe()
october_summary = octoberDAM[['price']].describe()

compare = pd.concat([september_summary, october_summary], axis=1)
compare.columns = ['September', 'October']
print("---------october vs september summary comparison------------")
print(compare)
print("")
# ------------------------------------------------

september_daily_summary = septemberDAM.groupby('deliveryDay')['price'].agg(
    min_price='min',
    max_price='max',
    mean_price='mean',
    median_price='median',
    std_price='std'
).reset_index()
print("---------september daily summary------------")
print(september_daily_summary)
print("")

october_daily_summary = octoberDAM.groupby('deliveryDay')['price'].agg(
    min_price='min',
    max_price='max',
    mean_price='mean',
    median_price='median',
    std_price='std'
).reset_index()
print("---------october daily summary------------")
print(october_daily_summary)
print("")

#--------------------------------15 MINUTE PERIOD STATS---------------------------------------------------

fmp, fmpax = plt.subplots()

octoberDAM['hourlyPeriod'] = octoberDAM.apply(hourly_period, axis=1)

hourlyPeriodsSummary = octoberDAM.groupby('hourlyPeriod')['price'].agg(
    mean_price='mean',
    median_price='median',
    std_price='std'
)
print("---------15 min periods summary------------")
print(hourlyPeriodsSummary)
print("")

fmpax.set_title('DAM average price per 15 minute period')
fmpax.set_xlabel('15-minute period')
fmpax.set_ylabel('Price')
fmpax.yaxis.set_major_formatter("{x:,.2f}€")
fmpax.set_ylim(min(hourlyPeriodsSummary['mean_price']) * 0.95,
             max(hourlyPeriodsSummary['mean_price']) * 1.05)
fmpax.set_xticks(hourlyPeriodsSummary.index)
fmpax.set_xticklabels(['XX:00', 'XX:15', 'XX:30', 'XX:45'])

plt.bar(hourlyPeriodsSummary.index, hourlyPeriodsSummary['mean_price'], color=['tab:red', 'tab:blue', 'tab:green', 'tab:orange'])
plt.tight_layout()

plt.show()

#----------------------------------OCTOBER VS SEPTEMBER RESAMPLED---------------------------------------

september_hourly = septemberDAM.set_index('deliveryStart')['price'].resample('h').mean().reset_index()
october_hourly = octoberDAM.set_index('deliveryStart')['price'].resample('h').mean().reset_index()

september_hourly['deliveryDay'] = september_hourly['deliveryStart'].dt.date
october_hourly['deliveryDay'] = october_hourly['deliveryStart'].dt.date

september_hourly['timeStart'] = september_hourly['deliveryStart'].dt.hour
october_hourly['timeStart'] = october_hourly['deliveryStart'].dt.hour

septemberDayR = september_hourly.groupby('deliveryDay')[['price', 'timeStart']]
octoberDayR = october_hourly.groupby('deliveryDay')[['price', 'timeStart']]

drovs, drovsax = plt.subplots()

for day, group in septemberDayR:
    group = group.sort_values('timeStart')
    drovsax.step(group['timeStart'], group['price'], label=str(day), color='orange', alpha=0.75, where='post')

for day, group in octoberDayR:
    group = group.sort_values('timeStart')
    drovsax.step(group['timeStart'], group['price'], label=str(day), color='blue', alpha=0.75, where='post')

drovsax.set_title("DAM Price over day RESAMPLED to 60min")
drovsax.set_xlabel('Delivery Start')
drovsax.set_ylabel('Price')
drovsax.yaxis.set_major_formatter("{x:,.2f}€")
drovsax.xaxis.set_major_locator(mticker.MultipleLocator(1))
drovsax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f"{int(x):02d}:00"))
drovsax.tick_params(axis='x', rotation=90)
legend_elements = [
    Line2D([0], [0], color='blue', lw=2, label='September (60min period)'),
    Line2D([0], [0], color='orange', lw=2, label='October (60min period)')
]
plt.legend(handles=legend_elements)
plt.tight_layout()
plt.show()

#--------------------------------------------IDM SETUP----------------------------------------------

septemberIDM = pd.read_json('septemberIDMJSON.json')
octoberIDM = pd.read_json('octoberIDMJSON.json')

#-----------------------------------------IDM stats-------------------------------------------------

septemberIDM['deliveryDay'] = pd.to_datetime(septemberIDM['deliveryDay'])
septemberIDM['deliveryStart'] = pd.to_datetime(septemberIDM['deliveryStart'])
septemberIDM['deliveryEnd'] = pd.to_datetime(septemberIDM['deliveryEnd'])
septemberIDM['timeStart'] = septemberIDM['deliveryStart'].dt.hour + septemberIDM['deliveryStart'].dt.minute/60

octoberIDM['deliveryDay'] = pd.to_datetime(octoberIDM['deliveryDay'])
octoberIDM['deliveryStart'] = pd.to_datetime(octoberIDM['deliveryStart'])
octoberIDM['deliveryEnd'] = pd.to_datetime(octoberIDM['deliveryEnd'])
octoberIDM['timeStart'] = octoberIDM['deliveryStart'].dt.hour + octoberIDM['deliveryStart'].dt.minute/60

octoberIDMstats = octoberIDM[['priceAverage', 'minimalPrice', 'maximalPrice', 'lastPrice']].describe()
septemberIDMstats = septemberIDM[['priceAverage', 'minimalPrice', 'maximalPrice', 'lastPrice']].describe()

print("---------september IDM summary------------")
print(septemberIDMstats)
print("")
print("---------october IDM summary------------")
print(octoberIDMstats)
print("")