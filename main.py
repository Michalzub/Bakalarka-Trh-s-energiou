import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
import matplotlib.ticker as mticker


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

#------------------------------------------------DAM SETUP--------------------------------------------------------------------
octoberDAMResponse = requests.get("https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-10-01&deliveryDayTo=2025-10-31")
septemberDAMResponse = requests.get("https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-09-01&deliveryDayTo=2025-09-30")
octoberDAM = pd.DataFrame(octoberDAMResponse.json())
septemberDAM = pd.DataFrame(septemberDAMResponse.json())

octoberDAM['deliveryDay'] = pd.to_datetime(octoberDAM['deliveryDay'])
octoberDAM['deliveryStart'] = pd.to_datetime(octoberDAM['deliveryStart'])
octoberDAM['deliveryEnd'] = pd.to_datetime(octoberDAM['deliveryEnd'])
octoberDAM['timeStart'] = octoberDAM['deliveryStart'].dt.hour + octoberDAM['deliveryStart'].dt.minute/60

septemberDAM['deliveryDay'] = pd.to_datetime(septemberDAM['deliveryDay'])
septemberDAM['deliveryStart'] = pd.to_datetime(septemberDAM['deliveryStart'])
septemberDAM['deliveryEnd'] = pd.to_datetime(septemberDAM['deliveryEnd'])
septemberDAM['timeStart'] = septemberDAM['deliveryStart'].dt.hour + septemberDAM['deliveryStart'].dt.minute/60

#-------------------------------------------OCTOBER VS SEPTEMBER-------------------------------------------

octoberDays = octoberDAM.groupby('deliveryDay')[['price', 'deliveryStart', 'deliveryEnd', 'timeStart']]
septemberDays = septemberDAM.groupby('deliveryDay')[['price', 'deliveryStart', 'deliveryEnd', 'timeStart']]

ovs, ovsax = plt.subplots()

for day, group in octoberDays:
    group = group.sort_values('timeStart')
    ovsax.step(group['timeStart'], group['price'], label=str(day), color='blue', alpha=0.75, where='post')

for day, group in septemberDays:
    group = group.sort_values('timeStart')
    ovsax.step(group['timeStart'], group['price'], label=str(day), color='orange', alpha=0.75, where='post')


ovsax.set_xlabel('Delivery Start')
ovsax.set_ylabel('Price')
ovsax.yaxis.set_major_formatter("{x:,.2f}€")
ovsax.xaxis.set_major_locator(mticker.MultipleLocator(1))
ovsax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f"{int(x):02d}:00"))
ovsax.tick_params(axis='x', rotation=90)
plt.tight_layout()

plt.show()

october_summary = octoberDAM.groupby('deliveryDay')['price'].agg(
    min_price='min',
    max_price='max',
    mean_price='mean',
    median_price='median',
    std_price='std'
).reset_index()

print(october_summary)

september_summary = septemberDAM.groupby('deliveryDay')['price'].agg(
    min_price='min',
    max_price='max',
    mean_price='mean',
    median_price='median',
    std_price='std'
).reset_index()

print(september_summary)

#--------------------------------15 MINUTE PERIOD STATS---------------------------------------------------

fmp, fmpax = plt.subplots()

octoberDAM['hourlyPeriod'] = octoberDAM.apply(hourly_period, axis=1)

hourlyPeriodsSummary = octoberDAM.groupby('hourlyPeriod')['price'].agg(
    mean_price='mean',
    median_price='median',
    std_price='std'
)
print(hourlyPeriodsSummary)

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


#----------------------------------------------------

#IDM
#octoberIDMResponse = requests.get("https://test-isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2024-09-1&deliveryDayTo=2024-10-31")
#septemberIDMResponse = requests.get("https://test-isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2025-09-1&deliveryDayTo=2025-09-30")
#octoberIDM = pd.DataFrame(octoberIDMResponse.json())
#septemberIDM = pd.DataFrame(septemberIDMResponse.json())

#print(type(octoberDAM['deliveryStart'][0]))






#octoberHP = octoberDAM.groupby('hourlyPeriod')['price'].mean()
#print(septemberDAM.nunique().loc[['deliveryDay']])
#print(octoberDAM.nunique().loc[['deliveryDay']])
# print(novemberDAM.nunique().loc[['deliveryDay']])
# print(octoberIDM['deliveryDay'].min())
# print(octoberIDM['deliveryDay'].max())
# print(septemberIDM['deliveryDay'].min())
# print(septemberIDM['deliveryDay'].max())
# print(octoberIDM.nunique().loc[['deliveryDay']])
# print(septemberIDM.nunique().loc[['deliveryDay']])
#octoberDAM.plot(x='deliveryDay', y='price', kind='line')

#plt.show()







