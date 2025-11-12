import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as md
import matplotlib.ticker as mticker

def format_time(x, pos=None):
    hours = int(x)
    minutes = int((x - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"

def hourly_period(row):
    time = row['dateStart'].minute
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

#DAM
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

octoberDays = octoberDAM.groupby('deliveryDay')[['price', 'deliveryStart', 'deliveryEnd', 'timeStart']]
septemberDays = septemberDAM.groupby('deliveryDay')[['price', 'deliveryStart', 'deliveryEnd', 'timeStart']]

ax = plt.gca()

for day, group in octoberDays:
    group = group.sort_values('timeStart')
    ax.step(group['timeStart'], group['price'], label=str(day), color='blue', alpha=0.75, where='post')

for day, group in septemberDays:
    group = group.sort_values('timeStart')
    ax.step(group['timeStart'], group['price'], label=str(day), color='orange', alpha=0.75, where='post')



plt.show()

#
# plt.xlabel('Delivery Start')
# plt.ylabel('Price')
# plt.show()

#IDM
#octoberIDMResponse = requests.get("https://test-isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2024-09-1&deliveryDayTo=2024-10-31")
#septemberIDMResponse = requests.get("https://test-isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2025-09-1&deliveryDayTo=2025-09-30")
#octoberIDM = pd.DataFrame(octoberIDMResponse.json())
#septemberIDM = pd.DataFrame(septemberIDMResponse.json())

#print(type(octoberDAM['deliveryStart'][0]))


#print(type(octoberDAM['dateStart'][0]))
#octoberDAM['dateEnd'] = pd.to_datetime(octoberDAM['deliveryEnd'])
#octoberDAM['hourlyPeriod'] = octoberDAM.apply(hourly_period, axis=1)
#print(octoberDAM)



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







