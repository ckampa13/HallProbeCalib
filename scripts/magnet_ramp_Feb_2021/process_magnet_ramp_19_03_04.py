import numpy as np
import pandas as pd
import os
from dateutil import parser
from datetime import datetime

datadir = '/home/ckampa/Dropbox/mu2e/fms/thomas/19-03-04 After transformer repair, restart monitoring/'
files = [f for f in os.listdir(datadir) if f[-4:]=='.csv']

headers = []

for f in files:
    with open(datadir+f, 'r') as myfile:
        headers.append([s.strip(" ").rstrip('\n') for s in str.split(next(myfile), ',')])

good_headers = headers[-1]+['ADC','B_nom'] # kludge

df = []
for i,f in enumerate(files):
    df_ = pd.read_csv(datadir+f, skiprows=1, names=headers[i])
    df_['ADC'] = int(f[14:20])
    df_['B_nom'] = float(f[:4])
    df.append(df_[good_headers])

df = pd.concat(df, ignore_index=True)
df['Magnet Current [A]'] = df['Magnet Current [V]'] / 10. * 340.
dates= [parser.parse(row.Time) for row in df.itertuples()]
df['Datetime'] = pd.to_datetime(dates)
df.sort_values(by=['Datetime'], inplace=True)
df = df.set_index('Datetime')
df['seconds_delta'] = (df.index - df.index[0]).total_seconds()
df['hours_delta'] = (df.index - df.index[0]).total_seconds()/60**2
df['days_delta'] = (df.index - df.index[0]).total_seconds()/(24*60**2)
# filter weird current measurements (low field)
# df = df[(df['Magnet Current [A]'] > 180.) & (df['NMR [T]'] > 0.9)].copy()
df = df[(df['Magnet Current [A]'] > 200.) & (df['NMR [T]'] > 0.9)].copy()
# and one more outlier
df = df[~np.isclose(df['Magnet Current [A]'], 216.06)].copy()
# cut out when NMR changing quickly
keep_mask = (np.abs(df['NMR [T]'].diff(30)) < 5e-7)
df = df[keep_mask].copy()
keep_mask = (np.abs(df['NMR [T]'].diff(30)/df['seconds_delta'].diff(30)) < 5e-7)
df = df[keep_mask].copy()

# check Hall probes
probes = [c[:-6] for c in df.columns if "Raw_X" in c]
# print(probes)
for p in probes:
    # print(p)
    df[f'{p}_Cal_Bmag'] = (df[f'{p}_Cal_X']**2 + df[f'{p}_Cal_Y']**2 + df[f'{p}_Cal_Z']**2)**(1/2)
    # df.eval(f'{p}_Cal_Bmag = ({p}_Cal_X**2 + {p}_Cal_Y**2 + {p}_Cal_Z**2)**(1/2)', inplace=True)
    # B = df[f'{p}_Cal_Bmag'].mean()
    # print(f'{p}_Cal_Bmag = {B} T')
    B = df[f'{p}_Cal_Bmag'].max()
    print(f'max({p}_Cal_Bmag) = {B} T')

df.to_pickle('/home/ckampa/Coding/hallprobecalib_extras/datafiles/magnet_ramping/ramp00_FNAL_2019-03-04.pkl')
