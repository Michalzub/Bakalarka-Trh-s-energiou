import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import json



septemberDAM = pd.read_json('septemberDAMJSON.json')
octoberDAM = pd.read_json('octoberDAMJSON.json')
septemberIDM = pd.read_json('septemberIDMJSON.json')
octoberIDM = pd.read_json('octoberIDMJSON.json')
