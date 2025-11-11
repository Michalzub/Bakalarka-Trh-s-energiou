import requests
import pandas as pd
import matplotlib.pyplot as plt


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


octoberDAMResponse = requests.get("https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-10-01&deliveryDayTo=2025-10-31")
septemberDAMResponse = requests.get("https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-09-01&deliveryDayTo=2025-09-30")
#novemberDAMResponse = requests.get("https://test-isot.okte.sk/api/v1/dam/results?deliveryDayFrom=2025-08-01&deliveryDayTo=2025-08-31")

octoberDAM = pd.DataFrame(octoberDAMResponse.json())
septemberDAM = pd.DataFrame(septemberDAMResponse.json())
#novemberDAM = pd.DataFrame(novemberDAMResponse.json())

#octoberIDMResponse = requests.get("https://test-isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2024-09-1&deliveryDayTo=2024-10-31")
#septemberIDMResponse = requests.get("https://test-isot.okte.sk/api/v1/idm/results?deliveryDayFrom=2025-09-1&deliveryDayTo=2025-09-30")

#octoberIDM = pd.DataFrame(octoberIDMResponse.json())
#septemberIDM = pd.DataFrame(septemberIDMResponse.json())

#print(type(octoberDAM['deliveryStart'][0]))

#octoberDAM['dateStart'] = pd.to_datetime(octoberDAM['deliveryStart'])
#print(type(octoberDAM['dateStart'][0]))
#octoberDAM['dateEnd'] = pd.to_datetime(octoberDAM['deliveryEnd'])
#octoberDAM['hourlyPeriod'] = octoberDAM.apply(hourly_period, axis=1)
#print(octoberDAM)

#octoberDAYS = octoberDAM.groupby('deliveryDay')['price'].count()

#octoberHP = octoberDAM.groupby('hourlyPeriod')['price'].mean()
print(septemberDAM.nunique().loc[['deliveryDay']])
print(octoberDAM.nunique().loc[['deliveryDay']])
# print(novemberDAM.nunique().loc[['deliveryDay']])
# print(octoberIDM['deliveryDay'].min())
# print(octoberIDM['deliveryDay'].max())
# print(septemberIDM['deliveryDay'].min())
# print(septemberIDM['deliveryDay'].max())
# print(octoberIDM.nunique().loc[['deliveryDay']])
# print(septemberIDM.nunique().loc[['deliveryDay']])
#octoberDAM.plot(x='deliveryDay', y='price', kind='line')

#plt.show()







