# =============================================================================
# Plots graphs comparing cases and deaths data for COVID-19 using data from
# Johns Hopkins Universtiy.
#
# Email: mwt.barnes@outlook.com
# =============================================================================

import country_converter as coco
from datetime import date
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import random
import re

URL_cases = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
URL_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
URL_excess = "https://raw.githubusercontent.com/TheEconomist/covid-19-excess-deaths-tracker/master/output-data/excess-deaths/all_weekly_excess_deaths.csv"

# -----------
# Deaths data
# -----------

deaths = pd.read_csv(URL_deaths)

# Each column from column 5 is date. These are melted into a single date column
deaths = pd.melt(deaths,
                 id_vars=['Province/State','Country/Region'],
                 value_vars=deaths.columns[4:])

deaths.columns = ['province_state', 'country', 'date', 'deaths']

deaths['date'] = pd.to_datetime(deaths['date'], format='%m/%d/%y')

# Drop data for the two cruise liners
deaths = deaths[~deaths['country'].isin(['Diamond Princess', 'MS Zaandam'])]

# Group deaths by country as some countries as split into regions / states
deaths = deaths.groupby(['country', 'date'], as_index=False)['deaths'].sum()

# ------------------------------------------
# Population and continent data + flag emoji
# ------------------------------------------

# Use country converter to get iso3 codes. This is done in a seprate dataframe
# and then merged to avoid running the country converter regex on the same
# country for every date.
iso3 = pd.DataFrame(
    {
        'country': deaths['country'].unique(),
        'iso3': coco.convert(list(deaths['country'].unique()), to='ISO3')
    }
)
deaths = deaths.merge(iso3, on='country', how='left')

countries_data = pd.read_csv('data/countries_matthew.csv',
                             usecols=['iso3', 'population_2019', 'OECD',
                                      'EU_EEA', 'continent', 'flag']
                            )

deaths = deaths.merge(countries_data, on='iso3', how='left')

deaths['deaths_per_million'] = deaths['deaths'] / deaths['population_2019'] * 1000000

# --------------------------------------------
# Daily deaths and 7 day rolling average
# --------------------------------------------

# Column with daily deaths calculated from cumulative deaths column
deaths['daily'] = deaths.groupby('country')['deaths'].apply(lambda x: x.diff())

# Where daily deaths are below 0 due to revisions to data, the daily deaths are
# set to 0
deaths['daily'] = np.where(deaths['daily']<0, 0, deaths['daily'])

# 7 day rolling average of daily deaths
deaths['7_day_average'] = deaths.groupby('country')['daily'].apply(lambda x: x.rolling(window=7, min_periods=1).mean())

deaths['7_day_average_per_million'] = deaths['7_day_average'] / deaths['population_2019'] * 1000000

# Drops first date for each country as daily deaths can't be calculated (0 for
# almost all countries anyway)
deaths = deaths.dropna()

# Column with dates in format 'Jan 01, 2000'
deaths['date_string'] = deaths['date'].apply(lambda x: x.strftime('%b %d, %Y'))

deaths = deaths.sort_values(['country', 'date'])

# ----------
# Cases data
# ----------

cases = pd.read_csv(URL_cases)

# Each column from column 5 is date. These are melted into a single date column
cases = pd.melt(cases,
                id_vars=['Province/State','Country/Region'],
                value_vars=cases.columns[4:])

cases.columns = ['province_state', 'country', 'date', 'cases']

cases['date'] = pd.to_datetime(cases['date'], format='%m/%d/%y')

# Drop data for the two cruise liners
cases = cases[~cases['country'].isin(['Diamond Princess', 'MS Zaandam'])]

# Group deaths by country as some countries as split into regions / states
cases = cases.groupby(['country', 'date'], as_index=False)['cases'].sum()

# ------------------------------------------
# Population and continent data + flag emoji
# ------------------------------------------

# Use country converter to get iso3 codes. This is done in a seprate dataframe
# and then merged to avoid running the country converter regex on the same
# country for every date.
iso3 = pd.DataFrame(
    {
        'country': cases['country'].unique(),
        'iso3': coco.convert(list(cases['country'].unique()), to='ISO3')
    }
)
cases = cases.merge(iso3, on='country', how='left')

cases = cases.merge(countries_data, on='iso3', how='left')

cases['cases_per_million'] = cases['cases'] / cases['population_2019'] * 1000000

# --------------------------------------------
# Daily cases and 7 day rolling average
# --------------------------------------------

# Column with daily cases calculated from cumulative cases column
cases['daily'] = cases.groupby('country')['cases'].apply(lambda x: x.diff())

# Where daily cases are below 0 due to revisions to data, the daily cases are
# set to 0
cases['daily'] = np.where(cases['daily']<0, 0, cases['daily'])

# 7 day rolling average of daily cases
cases['7_day_average'] = cases.groupby('country')['daily'].apply(lambda x: x.rolling(window=7, min_periods=1).mean())

cases['7_day_average_per_million'] = cases['7_day_average'] / cases['population_2019'] * 1000000

# Drops first date for each country as daily cases can't be calculated (0 for
# almost all countries anyway)
cases = cases.dropna()

# Column with dates in format 'Jan 01, 2000'
cases['date_string'] = cases['date'].apply(lambda x: x.strftime('%b %d, %Y'))

cases = cases.sort_values(['country', 'date'])

# ------------------------
# Colours for graph traces
# ------------------------

colors = [
    'rgba(0,17,255,0.6)',
    'rgba(210,0,0,0.5)',
    'rgba(0,150,30,0.5)',
    'rgba(110,0,255,0.5)',
    'rgba(0,200,255,0.5)'
] * 10

# =============================================================================
# Graphs
# =============================================================================

# ------------------------------
# Graph - daily deaths EU OECD
# Filename: daily_deaths_EU_OECD
# ------------------------------

df_EU = deaths[deaths['EU_EEA'] == True]
df_OECD = deaths[deaths['OECD'] == True]

# Using the list of colours created above, create a list the same length as the
# number of countries in the EU and OECD and set the color for Sweden as black.
countries_EU = list(df_EU['country'].unique())
colors_EU = colors[:len(countries_EU)]
colors_EU[countries_EU.index('Sweden')] = 'black'

countries_OECD = list(df_OECD['country'].unique())
colors_OECD = colors[:len(countries_OECD)]
colors_OECD[countries_OECD.index('Sweden')] = 'black'

# Create a list the same length as the number of countries in the EU and OECD
# with a linewidth of 2.5. Set the linewidth for Sweden as 3.5.
line_width_EU = [2.5]*len(countries_EU)
line_width_EU[countries_EU.index('Sweden')] = 3.5

line_width_OECD = [2.5]*len(countries_OECD)
line_width_OECD[countries_OECD.index('Sweden')] = 3.5

# Set visibility to show one plot with deaths for all countries and another
# with deaths per 1 million for all countries.
vis_1 = [True] * len(countries_EU) + [False] * len(countries_EU) + [False] * len(countries_OECD) * 2
vis_2 = [False] * len(countries_EU) + [True] * len(countries_EU) + [False] * len(countries_OECD) * 2
vis_3 = [False] * len(countries_EU) * 2 + [True] * len(countries_OECD) + [False] * len(countries_OECD)
vis_4 = [False] * len(countries_EU) * 2 + [False] * len(countries_OECD) + [True] * len(countries_OECD)

fig = go.Figure()

# Deaths - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['7_day_average'][df_EU['country'] == country]),
            name=country,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Deaths per million - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['7_day_average_per_million'][df_EU['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Deaths - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['7_day_average'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Deaths per million - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['7_day_average_per_million'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

fig.update_layout(
    title="<b>Antal Avlidna per Dag - EU / EEA</b><br><sup>(7 dagar glidande medelvärde)",
    xaxis=dict(
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    yaxis=dict(
        title="Antal Avlidna per Dag",
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    paper_bgcolor='white',
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0, y=-0.2,
            text="Sources: John Hopkins University CSSE, World Bank",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(size=11,
                      color='dimgray')
        )
    ],
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                dict(label="EU",
                     method='update',
                     args=[{'visible': vis_1},
                           {'title': "<b>Antal Avlidna per Dag - EU / EEA</b><br><sup>(7 dagar glidande medelvärde)"}]),
                dict(label="EU / miljon",
                     method='update',
                     args=[{'visible': vis_2},
                           {'title': "<b>Antal Avlidna per Dag (per miljon) - EU / EEA</b><br><sup>(7 dagar glidande medelvärde)"}]),
                dict(label="OECD",
                     method='update',
                     args=[{'visible': vis_3},
                           {'title': "<b>Antal Avlidna per Dag - OECD</b><br><sup>(7 dagar glidande medelvärde)"}]),
                dict(label="OECD / miljon",
                     method='update',
                     args=[{'visible': vis_4},
                           {'title': "<b>Antal Avlidna per Dag (per miljon) - OECD</b><br><sup>(7 dagar glidande medelvärde)"}]),
            ])
        )
    ]
)

fig.write_html('graphs/comparisons/daily_deaths_EU_OECD.html')

# ------------------------------
# Graph - total deaths_EU_OECD
# Filename: total_deaths_EU_OECD
# ------------------------------

fig = go.Figure()

# Deaths - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['deaths'][df_EU['country'] == country]),
            name=country,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Deaths per million - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['deaths_per_million'][df_EU['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Deaths - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['deaths'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Deaths per million - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['deaths_per_million'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

fig.update_layout(
    title="<b>Totalt Antal Avlidna - EU / EEA</b>",
    xaxis=dict(
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    yaxis=dict(
        title="Totalt Antal Avlidna",
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    paper_bgcolor='white',
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0, y=-0.2,
            text="Sources: John Hopkins University CSSE, World Bank",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(size=11,
                      color='dimgray')
        )
    ],
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                dict(label="EU",
                     method='update',
                     args=[{'visible': vis_1},
                           {'title': "<b>Totalt Antal Avlidna - EU / EEA</b>"}]),
                dict(label="EU / miljon",
                     method='update',
                     args=[{'visible': vis_2},
                           {'title': "<b>Totalt Antal Avlidna (per miljon) - EU / EEA</b>"}]),
                dict(label="OECD",
                     method='update',
                     args=[{'visible': vis_3},
                           {'title': "<b>Totalt Antal Avlidna - OECD</b>"}]),
                dict(label="OECD / miljon",
                     method='update',
                     args=[{'visible': vis_4},
                           {'title': "<b>Totalt Antal Avlidna (per miljon) - OECD</b>"}]),
            ])
        )
    ]
)

fig.write_html('graphs/comparisons/total_deaths_EU_OECD.html')

# -----------------------------
# Graph - daily cases EU OECD
# Filename: daily_cases_EU_OECD
# -----------------------------

df_EU = cases[cases['EU_EEA'] == True]
df_OECD = cases[cases['OECD'] == True]

# Using the list of colours created above, create a list the same length as the
# number of countries in the EU and OECD and set the color for Sweden as black.
countries_EU = list(df_EU['country'].unique())
colors_EU = colors[:len(countries_EU)]
colors_EU[countries_EU.index('Sweden')] = 'black'

countries_OECD = list(df_OECD['country'].unique())
colors_OECD = colors[:len(countries_OECD)]
colors_OECD[countries_OECD.index('Sweden')] = 'black'

# Create a list the same length as the number of countries in the EU and OECD
# with a linewidth of 2.5. Set the linewidth for Sweden as 3.5.
line_width_EU = [2.5]*len(countries_EU)
line_width_EU[countries_EU.index('Sweden')] = 3.5

line_width_OECD = [2.5]*len(countries_OECD)
line_width_OECD[countries_OECD.index('Sweden')] = 3.5

# Set visibility to show one plot with deaths for all countries and another with
# deaths per 1 million for all countries.
vis_1 = [True] * len(countries_EU) + [False] * len(countries_EU) + [False] * len(countries_OECD) * 2
vis_2 = [False] * len(countries_EU) + [True] * len(countries_EU) + [False] * len(countries_OECD) * 2
vis_3 = [False] * len(countries_EU) * 2 + [True] * len(countries_OECD) + [False] * len(countries_OECD)
vis_4 = [False] * len(countries_EU) * 2 + [False] * len(countries_OECD) + [True] * len(countries_OECD)

fig = go.Figure()

# Cases - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['7_day_average'][df_EU['country'] == country]),
            name=country,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Cases per million - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['7_day_average_per_million'][df_EU['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Cases - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['7_day_average'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Cases per million - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['7_day_average_per_million'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>7 dagar medelvärde / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

fig.update_layout(
    title="<b>Bekräftade Fall per Dag - EU / EEA</b><br><sup>(7 dagar glidande medelvärde)",
    xaxis=dict(
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    yaxis=dict(
        title="Bekräftade Fall per Dag",
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    paper_bgcolor='white',
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0, y=-0.2,
            text="Sources: John Hopkins University CSSE, World Bank",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(size=11,
                      color='dimgray')
        )
    ],
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                dict(label="EU",
                     method='update',
                     args=[{'visible': vis_1},
                           {'title': "<b>Bekräftade Fall per Dag - EU / EEA</b><br><sup>(7 dagar glidande medelvärde)"}]),
                dict(label="EU / miljon",
                     method='update',
                     args=[{'visible': vis_2},
                           {'title': "<b>Bekräftade Fall per Dag (per miljon) - EU / EEA</b><br><sup>(7 dagar glidande medelvärde)"}]),
                dict(label="OECD",
                     method='update',
                     args=[{'visible': vis_3},
                           {'title': "<b>Bekräftade Fall per Dag - OECD</b><br><sup>(7 dagar glidande medelvärde)"}]),
                dict(label="OECD / miljon",
                     method='update',
                     args=[{'visible': vis_4},
                           {'title': "<b>Bekräftade Fall per Dag (per miljon) - OECD</b><br><sup>(7 dagar glidande medelvärde)"}]),
            ])
        )
    ]
)

fig.write_html('graphs/comparisons/daily_cases_EU_OECD.html')

# -----------------------------
# Graph - total cases_EU_OECD
# Filename: total_cases_EU_OECD
# -----------------------------

fig = go.Figure()

# Cases - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['cases'][df_EU['country'] == country]),
            name=country,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Cases per million - EU
for country, color, width in zip(countries_EU, colors_EU, line_width_EU) :
    fig.add_trace(
        go.Scatter(
            x=list(df_EU['date'][df_EU['country'] == country]),
            y=list(df_EU['cases_per_million'][df_EU['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_EU['country'][df_EU['country'] == country],
                df_EU['flag'][df_EU['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Cases - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['cases'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

# Cases per million - OECD
for country, color, width in zip(countries_OECD, colors_OECD, line_width_OECD) :
    fig.add_trace(
        go.Scatter(
            x=list(df_OECD['date'][df_OECD['country'] == country]),
            y=list(df_OECD['cases_per_million'][df_OECD['country'] == country]),
            name=country,
            visible=False,
            mode='lines',
            line=dict(
                color=color,
                width=width),
            customdata=np.stack((
                df_OECD['country'][df_OECD['country'] == country],
                df_OECD['flag'][df_OECD['country'] == country]),
                axis = -1),
            hovertemplate=
            '<b>Totalt / miljon:</b> %{y:.2f}' +
            '<br><b>Datum:</b> %{x}</br>' +
            '<extra>%{customdata[0]} %{customdata[1]}</extra>'
        )
    )

fig.update_layout(
    title="<b>Totalt Antal Bekräftade Fall - EU / EEA</b>",
    xaxis=dict(
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    yaxis=dict(
        title="Totalt Bekräftade Fall",
        showline=True,
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke'
    ),
    paper_bgcolor='white',
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0, y=-0.2,
            text="Sources: John Hopkins University CSSE, World Bank",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(size=11,
                      color='dimgray')
        )
    ],
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                dict(label="EU",
                     method='update',
                     args=[{'visible': vis_1},
                           {'title': "<b>Totalt Antal Bekräftade Fall - EU / EEA</b>"}]),
                dict(label="EU / miljon",
                     method='update',
                     args=[{'visible': vis_2},
                           {'title': "<b>Totalt Antal Bekräftade Fall (per miljon) - EU / EEA</b>"}]),
                dict(label="OECD",
                     method='update',
                     args=[{'visible': vis_3},
                           {'title': "<b>Totalt Antal Bekräftade Fall - OECD</b>"}]),
                dict(label="OECD / miljon",
                     method='update',
                     args=[{'visible': vis_4},
                           {'title': "<b>Totalt Antal Bekräftade Fall (per miljon) - OECD</b></b>"}]),
            ])
        )
    ]
)

fig.write_html('graphs/comparisons/total_cases_EU_OECD.html')

# -------------
# Excess deaths
# -------------

# Read data on excess deaths
excess = pd.read_csv(URL_excess)

# x100 to get percentage value
excess['excess_deaths_pct_change'] = excess['excess_deaths_pct_change'] * 100

# Some countries have regional data so this is dropped from the data frame
drop_regions = ['United States', 'Spain', 'Britain',
                'France', 'Italy', 'Chile']
for country in drop_regions:
    excess = excess.drop( excess[ (excess['country']==country) & \
                              (excess['region']!=country) ].index )

fig = go.Figure()

fig.add_shape(
    x0=1, x1=excess['week'].max(),
    y0=0, y1=0,
    line=dict(
        color='rgba(30, 30, 30, 0.4)',
        dash='dot'
    )
)

for country, col in zip(excess['country'].unique(), colors):
    fig.add_trace(
        go.Scatter(
            x=list(excess['week'][excess['country'] == country]),
            y=list(excess['excess_deaths_pct_change'][excess['country'] == country]),
            marker=dict(color=col),
            name=country,
            hovertemplate=
            'Week %{x}<br>'+
            'Excess: %{y:.2f}%'
        )
    )

fig.update_layout(
    title=dict(
        text="<b>Excess Deaths - % Over Expected Weekly Deaths</b>",
        x=0,
        xref='paper'),
    hovermode='closest',
    xaxis=dict(
        title="Week",
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke',
        gridwidth=1
    ),
    yaxis=dict(
        title="% Excess",
        linewidth=2,
        linecolor='black',
        gridcolor='whitesmoke',
        gridwidth=1
    ),
    paper_bgcolor='white',
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.2,
            text="Source: The Economist",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray')
            )
    ]
)

fig.write_html('graphs/comparisons/excess_deaths.html')
