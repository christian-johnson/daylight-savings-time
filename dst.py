#
# dst.py
# Author: Christian Johnson
# Last modified: March 16, 2022
#
# NOTE: this code is only meant to apply to the continental US! You will get
# errors if you try to apply it to other locations
#

print('Loading libraries...')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
plt.rcParams['font.size'] = 14

import sys
import time
import calendar
from datetime import datetime, date
from astral import LocationInfo
from astral.sun import sun
from astral.geocoder import database, lookup

from tqdm import tqdm


colors = ["royalblue", "orange"] # Change to your colors of choice
cmap1 = LinearSegmentedColormap.from_list("mycmap", colors)

# Some numbers and names for plotting
month_lengths = np.array([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334])
month_names = ['January','February','March','April','May','June','July',
               'August','September','October','November','December']

def datetime_to_unix(timestamp):
    return (timestamp - pd.Timestamp('1970-01-01', tz = 'UTC'))/ pd.Timedelta('1s')

def daterange_to_unix(drange):
    return (drange - pd.Timestamp("1970-01-01", tz = 'UTC')) / pd.Timedelta('1s')

def dst_matrices(city, year = '2022'):
    """
    A function that finds the sunset and rise over the course of a year
    at a particular location.

    Inputs:
    - city: an astral LocationInfo object defining the city location, timezone, etc.
    - year: the year of interest, as a string

    Outputs:
    - An array M containing the data. The values of M are 0 if the sun has set,
      and 1 if the sun has risen.
      Dimensions of M are: 3x365x1440
        - 3 scenarios (standard DST, no DST, permanent DST)
        - 365 days per year
        - 1440 minutes per day

    Notes:
    - Each lat/lon location on Earth will have its own unique M
    - Time of day is given in the local time zone
    """

    print('Instantiating arrays...')
    jan1 = pd.to_datetime(date(int(year)-1,12,30), utc = None)
    dec31 = pd.to_datetime(date(int(year)+1,1,2), utc = None)
    drange = pd.date_range(jan1, dec31, freq = '60s', tz = city.timezone)[:-1]
    jan1_idx2_tz = np.argmin(np.abs([drange - pd.Timestamp('01JAN2022', tz = city.timezone)]))
    dec31_idx2_tz = np.argmin(np.abs([drange - pd.Timestamp('01JAN2023', tz = city.timezone)]))
    offset = (drange[0].utcoffset().days*86400 + drange[0].utcoffset().seconds)/60. # in minutes

    # A year plus 2 days on either side to account for any edge cases
    pre_jan1 = pd.to_datetime(date(int(year)-1,12,30), utc = True)
    post_dec31 = pd.to_datetime(date(int(year)+1,1,2), utc = True)
    extended_drange = pd.date_range(pre_jan1, post_dec31, freq = '1D', tz = 'UTC')
    extended_drange_s = pd.date_range(pre_jan1, post_dec31, freq = '60s', tz = 'UTC')[:-1]
    a = daterange_to_unix(extended_drange_s)[:-1]

    jan1_idx_unix = np.argmin(np.abs([a - datetime_to_unix(pd.Timestamp('01JAN2022', tz = city.timezone))]))
    dec31_idx_unix = np.argmin(np.abs([a - datetime_to_unix(pd.Timestamp('01JAN2023', tz = city.timezone))]))

    # A mapping from unix seconds to time of day
    # This could probably (definitely) be cleaned up some...
    dst_minutes = np.array(drange.hour*60+drange.minute)
    ext_dst_minutes = np.array((extended_drange_s).hour*60+(extended_drange_s).minute)
    transformed = (2*ext_dst_minutes - dst_minutes)%1440

    M = np.zeros((3, (len(extended_drange)-1) * 1440)) # Unraveled, we'll ravel it later

    print('Computing sunrise/sunset and DST hours...')
    for d in tqdm(extended_drange):
        s = sun(city.observer, date = d, tzinfo = city.timezone)

        beginning = np.argmin(np.abs(daterange_to_unix(drange) - datetime_to_unix(d))) - int(offset)
        end = np.argmin(np.abs(daterange_to_unix(drange) - datetime_to_unix(d) - 86400)) - int(offset)
        daylight_local = np.where(np.logical_and(drange[beginning:end]>s['sunrise'], drange[beginning:end]<s['sunset']))
        M[0][np.arange(beginning, end, 1)[np.argsort(transformed[beginning:end])][daylight_local[0]]] = 1.

        sunrise = datetime_to_unix(s['sunrise'])
        sunset = datetime_to_unix(s['sunset'])

        daylight_unix = np.where(np.logical_and(a>sunrise, a<sunset))
        M[1, daylight_unix] = 1.

    M = np.array([M[0][jan1_idx2_tz:dec31_idx2_tz].reshape(365, 1440),
                  M[1][jan1_idx_unix:dec31_idx_unix].reshape(365, 1440),
                 M[1][jan1_idx_unix-60:dec31_idx_unix-60].reshape(365, 1440)])
    return M

def month_lines(ax, year):
    month_idx = []
    for i,month in enumerate(month_names):
        ax.axhline(date(year, i+1, 1).timetuple().tm_yday, ls = '--', c = 'k', lw = 1.)
    return

def plot_dst(city, hgrid = True, year = '2022'):
    fig = plt.figure(figsize = [25,10])
    plt.suptitle(city.name)
    M = dst_matrices(city, year)
    print('Plotting...')

    plt.subplot(131)
    plt.imshow(M[0], aspect = 5, cmap = cmap1)
    plt.title('Standard DST')
    plt.xticks(np.array([0, 240, 480, 720, 960, 1200]),
                ['12AM','4AM','8AM','12PM','4PM','8PM'])
    plt.yticks(month_lengths, month_names)
    plt.axvline(480, ls = '--', c = 'k', lw = 2.)
    plt.axvline(1200, ls = '--', c = 'k', lw = 2.)

    if hgrid:
        month_lines(plt.gca(), year = int(year))
    plt.subplot(132)
    plt.title('No DST')
    plt.imshow(M[1], aspect = 5, cmap = cmap1)
    plt.xticks(np.array([0, 240, 480, 720, 960, 1200]),
                ['12AM','4AM','8AM','12PM','4PM','8PM'])
    plt.axvline(480, ls = '--', c = 'k', lw = 2.)
    plt.axvline(1200, ls = '--', c = 'k', lw = 2.)
    plt.yticks([], [])
    if hgrid:
        month_lines(plt.gca(), year = int(year))

    plt.subplot(133)
    plt.title('Permanent DST')
    plt.imshow(M[2], aspect = 5, cmap = cmap1)
    plt.yticks([], [])
    plt.axvline(480, ls = '--', c = 'k', lw = 2.)
    plt.axvline(1200, ls = '--', c = 'k', lw = 2.)

    plt.xticks(np.array([0, 240, 480, 720, 960, 1200]),
                ['12AM','4AM','8AM','12PM','4PM','8PM'])
    if hgrid:
        month_lines(plt.gca(), year = int(year))

    plt.subplots_adjust(wspace = -0.05)
    plt.savefig('figures/'+city.name + '.pdf', bbox_inches = 'tight')
    print('Done!')
    return

if __name__ == "__main__":
    city = lookup(sys.argv[1], database())
    if len(sys.argv) >2:
        year = sys.argv[2]
        plot_dst(city = city, year = year)
    else:
        plot_dst(city = city, year = date.today().year)
