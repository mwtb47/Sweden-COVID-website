# =============================================================================
# Creates plots summarising data on cases, deaths and hospitalisations using
# data from Folkhälsomyndiheten, Socialstyrelsen and Statistiska centralbyrån.
#
# Contact: mwt.barnes@outlook.com
# =============================================================================

from bs4 import BeautifulSoup
import config
from datetime import date
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import urllib

# =============================================================================
# Cases
# =============================================================================

# -----------------------------------
# Read data from Folkhälsomyndigheten
# -----------------------------------

folkhälsomyndigheten_url = "https://www.arcgis.com/sharing/rest/content/items/b5e7488e117749c19881cce45db13f7e/data"

urllib.request.urlretrieve(folkhälsomyndigheten_url, "data/Folkhälsomyndigheten.xlsx")

daily_cases = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                            sheet_name='Antal per dag region')

daily_cases['Statistikdatum'] = pd.to_datetime(daily_cases['Statistikdatum'],
                                               format='%Y-%m-%d')

# Melt columns for each county into a single column
daily_cases = daily_cases.melt(id_vars='Statistikdatum',
                               var_name='county',
                               value_name='cases')

# Group data frame by county and create new column with 7 day rolling average
daily_cases['7_day_rolling'] = daily_cases.groupby('county')['cases'].apply(lambda x: x.rolling(window=7).mean())

# Replace region names with desired names
daily_cases = daily_cases.replace(
    {
        'Jämtland_Härjedalen': 'Jämtland',
        'Västra_Götaland': 'Västra Götaland',
        'Sörmland': 'Södermanland'
    }
)

# County populations
counties_pop = pd.read_csv('data/sweden_counties.csv',
                           dtype={
                               'county_code':str,
                               'county':str,
                               'population_2019':int
                            })

# Total population
total_pop = counties_pop['population_2019'].sum()

# Merge population data and add total population
daily_cases = daily_cases.merge(counties_pop,
                                on='county',
                                how='left')

daily_cases.loc[daily_cases['county'] == 'Totalt_antal_fall',
                'population_2019'] = total_pop

# Create columns with cases and 7 day rolling averages per 10,000 inhabitants
daily_cases['cases_per_10000'] = daily_cases['cases'] / daily_cases['population_2019'] * 10000
daily_cases['7_day_per_10000'] = daily_cases['7_day_rolling'] / daily_cases['population_2019'] * 10000

# -------------------------
# Graph - daily cases
# Filename: daily_cases_all
# -------------------------

df = daily_cases[daily_cases['Statistikdatum'] >= '2020-02-10']

fig = go.Figure()

# Daily cases - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(df['Statistikdatum'][df['county'] == 'Totalt_antal_fall']),
        y=list(df['7_day_rolling'][df['county'] == 'Totalt_antal_fall']),
        showlegend=False,
        text=list(df['cases'][df['county'] == 'Totalt_antal_fall']),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='blue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '<b>Medelvärde</b>: %{y:.1f}<br>'+
        '<b>Daglig</b>: %{text}'
    )
)

# Daily cases - bar chart of daily cases as they are reported
fig.add_trace(
    go.Bar(
        x=list(df['Statistikdatum'][df['county'] == 'Totalt_antal_fall']),
        y=list(df['cases'][df['county'] == 'Totalt_antal_fall']),
        marker=dict(color='rgba(200, 220, 255, 0.5)'),
        showlegend=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    title="<b>Bekräftade Fall per Dag</b><br><sup>7 dagar glidande medelvärde",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        title="Antal Fall",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0, y=-0.15,
            text="Källa: Folkhälsomyndigheten",
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
    ]
)

fig.write_html('graphs/cases/daily_cases_all.html')

# --------------------------------
# Graph - daily cases per county
# Filename: daily_cases_per_county
# --------------------------------

regions = list(daily_cases['county'].unique())
regions.remove('Totalt_antal_fall')

rows = [1,1,1,2,2,2,3,3,3,4,4,4,5,5,5,6,6,6,7,7,7]
cols = [1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3]

fig = make_subplots(7, 3, subplot_titles=(regions), shared_xaxes=True)

# Cases
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['Statistikdatum'][df['county'] == region]),
            y=list(df['7_day_rolling'][df['county'] == region]),
            showlegend=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>%{x}</b><br>'+
            '%{y:.1f}'
        ),
        row, col
    )

# Cases per 10,000
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['Statistikdatum'][df['county'] == region]),
            y=list(df['7_day_per_10000'][df['county'] == region]),
            visible=False,
            showlegend=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>%{x}</b><br>'+
            '%{y:.1f}'
        ),
        row, col
    )

fig.update_xaxes(
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)

fig.update_yaxes(
    matches='y',
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)

fig.update_layout(
    title="<b>Bekräftade Fall per Län</b><br><sup>7 dagar glidande medelvärde",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=800,
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                    dict(label="Antal Fall",
                         method='update',
                         args=[{'visible': [True]*21 + [False]*21},
                                 {'title': "<b>Bekräftade Fall per Län</b><br><sup>7 dagar glidande medelvärde"}]),
                    dict(label="Antal Fall per 10,000",
                         method='update',
                         args=[{'visible': [False]*21 + [True]*21},
                                 {'title': "<b>Bekräftade Fall per Län (per 10,000)</b><br><sup>7 dagar glidande medelvärde"}]),
                        ]
            )
    )]
)

fig.add_annotation(
    dict(
        x=0, y=-0.08,
        text="Källa: Folkhälsomyndigheten",
        showarrow=False,
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='auto',
        xshift=0,
        yshift=0,
        font=dict(
            size=11,
            color='dimgray'
        )
    )
)

fig.write_html('graphs/cases/daily_cases_per_county.html')

# ---------------------------------------------
# Graph - daily cases per county (single graph)
# Filename: daily_cases_per_county_single
# ---------------------------------------------

fig = go.Figure()

# Cases
for region in regions:
    fig.add_trace(
        go.Scatter(
            x=list(df['Statistikdatum'][df['county'] == region]),
            y=list(df['7_day_rolling'][df['county'] == region]),
            name=region,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>%{x}</b><br>'+
            '%{y:.1f}'
        )
    )

# Cases per 10,000
for region in regions:
    fig.add_trace(
        go.Scatter(
            x=list(df['Statistikdatum'][df['county'] == region]),
            y=list(df['7_day_per_10000'][df['county'] == region]),
            name=region,
            visible=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>%{x}</b><br>'+
            '%{y:.1f}'
        )
    )

fig.update_layout(
    title="<b>Bekräftade Fall per Län</b><br><sup>7 dagar glidande medelvärde",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    height=600,
    annotations=[
        dict(
            x=0, y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
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
                dict(label="Antal Fall",
                     method='update',
                     args=[{'visible': [True]*21 + [False]*21},
                           {'title': "<b>Bekräftade Fall per Län</b><br><sup>7 dagar glidande medelvärde"}]),
                dict(label="Antal Fall per 10,000",
                     method='update',
                     args=[{'visible': [False]*21 + [True]*21},
                           {'title': "<b>Bekräftade Fall per Län (per 10,000)</b><br><sup>7 dagar glidande medelvärde"}]),
                    ]
            )
    )]
)

fig.write_html('graphs/cases/daily_cases_per_county_single.html')

# ---------------------------------------------------
# Graph - percentage of population with positive test
# Filename: percentage_cases
# ---------------------------------------------------

# Data on population by age group
population_ages = pd.read_excel('data/age_pyramid.xlsx',
                                sheet_name='Data',
                                skiprows=6,
                                usecols=list(range(8,13)))

population_ages = population_ages.dropna()

# As the data was set up for a population pyramid split between males and
# females, the population sizes for males are negative. This makes all
# population numbers positive.
population_ages[['födda i Sverige.4', 'utrikes födda.4']] = \
    population_ages[['födda i Sverige.3', 'utrikes födda.3']].abs()

# Populations are broken down by domestic and foreign born, these are summed to
# get the population totals.
population_ages['Men'] = population_ages['födda i Sverige.3'] + population_ages['utrikes födda.3']
population_ages['Women'] = population_ages['födda i Sverige.4'] + population_ages['utrikes födda.4']
population_ages['All'] = population_ages['Men'] + population_ages['Women']

population_ages = population_ages[['Ålder.1', 'Men', 'Women', 'All']]

# The ages need to be grouped as they are in the COVID-19 data. The age groups
# are 0-9, 10-19 etc. so the ages can be divided by 10, with the quotient
# forming the first age in the range and the quotient plus 9 forming the upper
# limit of the range.
def group_ages(e):
    quotient = e // 10
    string = str(quotient * 10) + '-' + str(quotient * 10 + 9)
    if string == '90-99' or string == '100-109':
        string = '90+'
    return string

# '100+' is replaced with 100 so the group_ages function can handle it
population_ages = population_ages.replace('100+', 100)
population_ages['group'] = population_ages['Ålder.1'].apply(group_ages)

population_grouped_ages = population_ages.groupby('group')[
    ['Men', 'Women', 'All']].sum().reset_index()

# Data on cases and deaths by age group
åldersgrupp = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                            sheet_name='Totalt antal per åldersgrupp')

# Drop data with unknown groups
åldersgrupp = åldersgrupp[åldersgrupp['Åldersgrupp'] != 'Uppgift saknas']

åldersgrupp['Åldersgrupp'] = [
    '0-9', '10-19', '20-29', '30-39', '40-49',
    '50-59', '60-69', '70-79', '80-89', '90+'
]

åldersgrupp['case_fatality_rate'] = åldersgrupp['Totalt_antal_avlidna'] / åldersgrupp['Totalt_antal_fall']

åldersgrupp['case_fatality_rate_rounded'] = round(åldersgrupp['case_fatality_rate'], 4)

åldersgrupp = åldersgrupp.merge(population_grouped_ages[['group', 'All']],
                                left_on='Åldersgrupp',
                                right_on='group',
                                how='left')

# Percentage of people in each age group who have tested positive
åldersgrupp['case_%'] = åldersgrupp['Totalt_antal_fall'] / åldersgrupp['All'] * 100

# Percentage of population which has tested positive
total_percentage = sum(åldersgrupp['Totalt_antal_fall']) / sum(åldersgrupp['All']) * 100

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=['All'] + list(åldersgrupp['Åldersgrupp']),
        y=[total_percentage] + list(åldersgrupp['case_%']),
        marker=dict(color=['darkblue']+['skyblue']*10),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor=['darkblue']+['skyblue']*10,
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '%{y:.3f}%'
    )
)

fig.update_layout(
    title="<b>Andelen av Befolkningen som har Testat Positivt i COVID-19</b>",
    xaxis=dict(
        title="Åldersgrupp",
        linewidth=2,
        linecolor='black'
    ),
    yaxis=dict(
        title="%",
        gridcolor='rgb(240, 240, 240)',
        gridwidth=2,
        linewidth=2,
        linecolor='black'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0, y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]

)

fig.write_html('graphs/cases/percentage_cases.html')

# -------------------------
# Graph - number of tests
# Filename: number_of_tests
# -------------------------

# The following fetches the html for the webpage containing the most up-to-date
# test numbers and extracts the table containing this information.
url = "https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/statistik-och-analyser/antalet-testade-for-covid-19/"
page = requests.get(url).text
soup = BeautifulSoup(page, 'lxml')
tables = soup.findAll('table')
table_tests = tables[0]

vecka=[]
number_individuals=[]
number_tests=[]
number_antibody=[]

# Iterate through the html table, extracting the week, number of individual
# tests, number of total tests and number of antibody tests.
for row in table_tests.findAll('tr'):
    vecka.append(row.find('th').find(text=True))
    cells = row.findAll('td')
    if len(cells) > 0:
        number_individuals.append(int(cells[0].find(text=True).replace(" ", "")))
        number_tests.append(int(cells[1].find(text=True).replace(" ", "")))
        number_antibody.append(int(cells[3].find(text=True).replace(" ", "")))

vecka = vecka[1:]

df_temp = pd.DataFrame({
    'year': 2021,
    'vecka':vecka,
    'number_individual_tests':number_individuals,
    'number_tests': number_tests,
    'number_antibody': number_antibody
})

# Convert 'Vecka 10', 'Vecak 11' etc. into integer values 10, 11 etc.
df_temp['vecka'] = df_temp['vecka'].apply(lambda x: int(x.split(" ")[1]))

# Webpage displays most recent 5 weeks therefore there are still weeks from the
# end of 2020 whjch need to be dropped. 
current_week = int(date.today().strftime("%U"))
df_temp = df_temp[df_temp['vecka'] <= current_week]

# Append weekly test data from earlier in the year
weekly_tests = pd.read_csv('data/weekly_tests.csv')
weekly_tests = weekly_tests.append(df_temp).drop_duplicates()
weekly_tests = weekly_tests.sort_values(['year', 'vecka'])

# Write data to csv as webpage only displays data for the most recent 5 weeks.
weekly_tests.to_csv('data/weekly_tests.csv', index=False)

# Create string formats of the numbers which are thousand comma separated
# making them easier to read
weekly_tests['str_ind'] = weekly_tests['number_individual_tests'].apply(lambda x: "{:,}".format(x))
weekly_tests['str_tests'] = weekly_tests['number_tests'].apply(lambda x: "{:,}".format(x))
weekly_tests['str_antibody'] = weekly_tests['number_antibody'].apply(lambda x: "{:,}".format(x))

fig = go.Figure()

# Number of individual tests
fig.add_trace(
    go.Scatter(
        x=[[2020]*46 + [2021]*(len(weekly_tests.index)-46), list(weekly_tests['vecka'])],
        y=list(weekly_tests['number_individual_tests']),
        name="Individer",
        text=weekly_tests['str_ind'],
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='blue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{text}'
    )
)

# Number of tests performed
fig.add_trace(
    go.Scatter(
        x=[[2020]*46 + [2021]*(len(weekly_tests.index)-46), list(weekly_tests['vecka'])],
        y=list(weekly_tests['number_tests']),
        name="Totalt",
        text=weekly_tests['str_tests'],
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='red',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{text}'
    )
)

# Number of antibody tests
fig.add_trace(
    go.Scatter(
        x=[[2020]*28 + [2021]*(len(weekly_tests.index)-46), list(weekly_tests['vecka'][18:])],
        y=list(weekly_tests['number_antibody'][18:]),
        name="Totalt",
        visible=False,
        text=weekly_tests['str_antibody'],
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='blue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{text}'
    )
)

fig.update_layout(
    title="<b>Antal per Vecka - Nukleinsyrapåvisning</b>",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        title="Vecka",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        title="Antal Tester",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ],
    updatemenus=[dict(
        direction='down',
        x=1,
        xanchor='right',
        y=1.1,
        yanchor='top',
        buttons=list([
            dict(label="Nukleinsyrapåvisning",
                 method='update',
                 args=[{'visible': [True, True, False]},
                       {'title': "<b>Antal per Vecka - Nukleinsyrapåvisning</b>"}]),
            dict(label="Antikroppspåvisning",
                 method='update',
                 args=[{'visible': [False, False, True]},
                       {'title': "<b>Antal per Vecka - Antikroppspåvisning</b>"}]),
        ])
    )]
)

fig.write_html('graphs/cases/number_of_tests.html')

# ---------------------------
# Antibody tests
# Filename: positive_antibody
# ---------------------------

# Extract the relevent table from the html
table_antibody = tables[2]

län = []
number_antibody = []
positive_antibody = []

# Iterate through the html table, extracting the län, number of antibody tests
# and the number of positive antibody tests.
for row in table_antibody.findAll('tr'):
    län.append(row.find('th').find(text=True))
    cells = row.findAll('td')
    if len(cells) > 0:
        number_antibody.append(int(cells[0].find(text=True).replace(" ", "")))
        positive_antibody.append(int(cells[1].find(text=True).replace(" ", "")))

# Drop 'Region' from the list of counties
län = län[1:]

df = pd.DataFrame(
    {
        "län": län,
        "number_tests": number_antibody,
        "number_positive": positive_antibody
    }
)

df = df.replace("Jämtland/ Härjedalen", "Jämtland")

# Percentage of tests with positive results
df['percent'] = round(df['number_positive'] / df['number_tests'] * 100, 4)
df = df.sort_values('percent')

# Not sure why this is needed, but graph would not plot without it.
df['län'] = df['län'].apply(lambda x: x[:20])

# Set the color as skyblue for all the counties, with the marker for the whole
# country being darkblue.
df['color'] = np.where(df['län']=='Riket', 'darkblue', 'skyblue')

# Extract the most recent week number to use in the graph title
text = tables[2].find('caption').find(text=True)
week_str = 'Vecka ' + text.split('vecka ')[1][:2]

fig = go.Figure()

# Percent positive antibody
fig.add_trace(
    go.Bar(
        y=list(df['län']),
        x=list(df['percent']),
        marker=dict(color=df['color']),
        orientation='h',
        text=df['number_tests'],
        hoverlabel=dict(
            bgcolor='white',
            bordercolor=df['color'],
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{y}</b><br>'+
        '<b>% Positiv</b>: %{x:.2f}<br>'+
        '<b>Antal Tester</b>: %{text}'

    )
)

fig.update_layout(
    title="<b>Andel Positiva Antikropps Tester - " + week_str + "</b>",
    xaxis=dict(
        title="% Positiv",
        linewidth=2,
        linecolor='black',
        gridcolor='rgb(240, 240, 240)',
        gridwidth=2
    ),
    yaxis=dict(
        linewidth=2,
        linecolor='black'
    ),
    plot_bgcolor='white',
    height=700,
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/cases/positive_antibody.html')

# =============================================================================
# Vaccinations
# =============================================================================

# The following fetches the html for the webpage with the most up-to-date
# vaccination numbers and extracts the table containing this information.
vaccine_url = "https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/vaccination-mot-covid-19/statistik-over-vaccinerade-mot-covid-19/"
page = requests.get(vaccine_url).text
soup = BeautifulSoup(page, 'lxml')
table = soup.findAll('table')[0]

# Extract week numbers from the table
vecka = []
for row in table.findAll('th'):
    if row.get('scope')=='row':
        vecka.append(row.find(text=True))

# Extract weekly totals for vaccines delivered to Sweden and vaccinations given
# to people.
levererat = []
förbrukat = []
for row in table.findAll('tr'):
    cells = row.findAll('td')
    if len(cells)==3:
        levererat.append(int(cells[0].find(text=True).replace(" ", "")))
        förbrukat.append(int(cells[1].find(text=True).replace(" ", "")))

df = pd.DataFrame({'vecka': vecka, 'levererat':levererat, 'förbrukat':förbrukat})
df = df[df['vecka']!='Totalt']

# Weeks come in the form '1, 2021' so these are split into seperate columns and
# then sorted.
df['year'] = df['vecka'].apply(lambda x: int(x.split(', v. ')[1]))
df['vecka'] = df['vecka'].apply(lambda x: int(x.split(',')[0]))
df = df.sort_values(['year', 'vecka'])

# Cumulative totals of vaccines delivered and vaccinations given
df[['levererat_total', 'förbrukat_total']] = df[['levererat', 'förbrukat']].cumsum()

# Convert weeks to strings and label the first weeks in the data from each year.
df['vecka'] = df['vecka'].astype(str)
df.loc[df['vecka']=='52', 'vecka'] = '52 (2020)'
df.loc[df['vecka']=='1', 'vecka'] = '1 (2021)'

# ----------------------------------------------
# Graph - total and weekly vaccinations
# Filename: vaccinations
# ----------------------------------------------

fig = go.Figure()

# Total vaccinations received
fig.add_trace(
    go.Scatter(
        x=list(df['vecka']),
        y=list(df['levererat_total']),
        name="Levererat",
        marker=dict(color='darkblue'),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='darkblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{y}'
    )
)

# Total vaccinations given
fig.add_trace(
    go.Scatter(
        x=list(df['vecka']),
        y=list(df['förbrukat_total']),
        name="Förbrukat",
        marker=dict(color='skyblue'),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{y}'
    )
)

# Weekly vaccinations received
fig.add_trace(
    go.Bar(
        x=list(df['vecka']),
        y=list(df['levererat']),
        visible=False,
        name="Levererat",
        marker=dict(color='darkblue'),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='darkblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{y}'
    )
)

# Weekly vaccinations given
fig.add_trace(
    go.Bar(
        x=list(df['vecka']),
        y=list(df['förbrukat']),
        visible=False,
        marker=dict(color='skyblue'),
        name="Förbrukat",
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x}</b><br>'+
        '%{y}'
    )
)


fig.update_layout(
    title="<b>Totalt Levererade och Förbrukade Doser</b>",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        type='category',
        title="Vecka",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        title="Antal Doser",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ],
    updatemenus=[dict(
        direction='down',
        x=1,
        xanchor='right',
        y=1.1,
        yanchor='top',
        buttons=list([
            dict(label="Totalt",
                 method='update',
                 args=[{'visible': [True, True, False, False]},
                       {'title': "<b>Totalt Levererade och Förbrukade Doser</b>"}]),
            dict(label="Per Vecka",
                 method='update',
                 args=[{'visible': [False, False, True, True]},
                       {'title': "<b>Levererade och Förbrukade Doser per Vecka</b>"}]),
        ])
    )]
)

fig.write_html('graphs/vaccine/vaccinations.html')

# ----------------------------------------------
# Graph - % population vaccinated
# Filename: percentage_vaccine
# ----------------------------------------------

# Sweden total population
sweden_pop = population_ages['All'].sum()

# Percentage of population vaccinated
percent_vaccinated = df['levererat_total'].max() / sweden_pop * 100

fig = go.Figure()

# Vaccinated
fig.add_trace(
    go.Bar(
        name="Vaccinerade",
        y=list(" "),
        x=[percent_vaccinated],
        marker=dict(color='darkblue'),
        orientation='h',
        text=['Vaccinerade'],
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='gray',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{text}</b><br>'+
        '%{x:.2f}%'
    )
)

# Not vaccinated
fig.add_trace(
    go.Bar(
        name="Ej Vaccinerade",
        y=list(" "),
        x=[100-percent_vaccinated],
        marker=dict(color='rgba(80, 80, 80, 0.8)'),
        orientation='h',
        text=['Ej Vaccinerade'],
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='gray',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{text}</b><br>'+
        '%{x:.2f}%'
    )
)


fig.update_layout(
    title="<b>Andelen av Befolkningen som Vaccinerat</b>",
    barmode='stack',
    legend_traceorder='normal',
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(220, 220, 220)'
    ),
    yaxis=dict(
        linewidth=2,
        linecolor='black',
    ),
    height=130,
    margin=dict(t=30, b=0),
    plot_bgcolor='white'
)

fig.write_html('graphs/vaccine/percent_vaccine.html')

# =============================================================================
# Stockholm
# =============================================================================

# ----------------------------------------------
# Graph - daily cases per area of Stockholms Län
# Filename: cases_stockholm_county
# ----------------------------------------------

# COVID-19 data for each kommun
kommun = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                       sheet_name='Veckodata Kommun_stadsdel')

# Data on the populations of each kommun
kommun_pop = pd.read_csv('data/sweden_kommun.csv',
                         dtype={
                             'kommun_code': str,
                             'kommun': str,
                             'population_2019': int,
                             'county_code': str,
                             'county': str
                         })

# Get a list of the kommuns that make up Stockholm County and create a new data
# frame with only Stockholm kommuns.
stockholm_kommuns = list(kommun_pop[kommun_pop['county_code'] == '01']['kommun'])
stockholm_län = kommun[kommun['KnNamn'].isin(stockholm_kommuns)].copy()

# Some figures are reported as strings '<15'. These are replaced with 0s.
stockholm_län = stockholm_län.replace('<15', 0)

stockholm_län['nya_fall_vecka'] = stockholm_län['nya_fall_vecka'].astype(int)

# Areas in Stockholm are in the format 'Stockholm Nacka' and are changed to just
# include the area name, i.e. 'Nacka'
stockholm_län['Kommun_stadsdel'] = np.where(
    stockholm_län['Kommun_stadsdel'].str.contains('Stockholm'),
    'Stockholm',
    stockholm_län['Kommun_stadsdel'])

stockholm_län = stockholm_län.groupby(['Kommun_stadsdel', 'veckonummer'],
                                      as_index=False)['nya_fall_vecka'].sum()

stockholm_län = stockholm_län.merge(kommun_pop[['kommun', 'population_2019']],
                                    left_on='Kommun_stadsdel',
                                    right_on='kommun',
                                    how='left')

stockholm_län['fall_per_10000'] = stockholm_län['nya_fall_vecka'] / stockholm_län['population_2019'] * 10000

df = stockholm_län

fig = make_subplots(6, 5,
                    subplot_titles=(stockholm_kommuns),
                    shared_xaxes=True)

rows = [1,1,1,1,1,2,2,2,2,2,3,3,3,3,3,4,4,4,4,4,5,5,5,5,5,6]
cols = [1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1]

# New cases per week
for region, row, col in zip(stockholm_kommuns, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Kommun_stadsdel'] == region]),
            y=list(df['nya_fall_vecka'][df['Kommun_stadsdel'] == region]),
            showlegend=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>Vecka %{x}</b><br>'+
            'Cases: %{y}'
        ), row, col
    )

# New cases per week per 10,000
for region, row, col in zip(stockholm_kommuns, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Kommun_stadsdel'] == region]),
            y=list(df['fall_per_10000'][df['Kommun_stadsdel'] == region]),
            visible=False,
            showlegend=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y:.2f}'
        ), row, col
    )

fig.update_xaxes(
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)
fig.update_yaxes(
    matches='y',
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)

fig.update_layout(
    title="<b>Bekräftade Fall inom Stockholms Län per Vecka</b>",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=800,
    updatemenus=[dict(
        direction='down',
        x=1,
        xanchor='right',
        y=1.1,
        yanchor='top',
        buttons=list([
            dict(label="Antal Fall",
                 method='update',
                 args=[{'visible': [True]*26 + [False]*26},
                         {'title': "<b>Bekräftade Fall inom Stockholms Län per Vecka</b>"}]),
            dict(label="Antal Fall per 10,000",
                 method='update',
                 args=[{'visible': [False]*26 + [True]*26},
                         {'title': "<b>Bekräftade Fall inom Stockholms Län per Vecka (per 10,000)</b>"}]),
        ])
    )]
)

fig.add_annotation(
    dict(
        x=0,
        y=-0.15,
        text="Källa: Folkhälsomyndigheten",
        showarrow=False,
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='auto',
        xshift=0,
        yshift=0,
        font=dict(
            size=11,
            color='dimgray'
        )
    )
)

fig.write_html('graphs/stockholm/cases_stockholm_county.html')

# -------------------------------------------------------------
# Graph - daily cases per area of Stockholms Län (single graph)
# Filename: cases_stockholm_county_single
# -------------------------------------------------------------

fig = go.Figure()

# New cases per week
for region in stockholm_kommuns:
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Kommun_stadsdel'] == region]),
            y=list(df['nya_fall_vecka'][df['Kommun_stadsdel'] == region]),
            name=region,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        )
    )

# New cases per week per 10,000
for region in stockholm_kommuns:
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Kommun_stadsdel'] == region]),
            y=list(df['fall_per_10000'][df['Kommun_stadsdel'] == region]),
            name=region,
            visible=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y:.2f}'
        )
    )

fig.update_layout(
    title="<b>Bekräftade Fall inom Stockholms Län</b>",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        title="Vecka",
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    height=700,
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
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
                dict(label="Antal Fall",
                     method='update',
                     args=[{'visible': [True]*26 + [False]*26},
                             {'title': "<b>Bekräftade Fall inom Stockholms Län</b>"}]),
                dict(label="Antal Fall per 10,000",
                     method='update',
                     args=[{'visible': [False]*26 + [True]*26},
                             {'title': "<b>Bekräftade Fall inom Stockholms Län (per 10,000)</b>"}]),
            ])
        )
    ]
)

fig.write_html('graphs/stockholm/cases_stockholm_county_single.html')

# -------------------------------------------------
# Graph - weekly cases per area of Stockholm Kommun
# Filename: cases_stockholm_kommun
# -------------------------------------------------

# Select all areas in Stockhom Kommun
stockholm_kommun = kommun[kommun['KnNamn'] == 'Stockholm']

# Some figures are reported as strings '<15'. These are replaced with 0s.
stockholm_kommun = stockholm_kommun.replace(['<15', np.nan], 0)

# Convert columns with COVID-19 cases and deaths to integers
stockholm_kommun.iloc[:, 6:] = stockholm_kommun.iloc[:, 6:].astype(int)

# Population data for each area of Stockholm Kommun
stockholm_kommun_befolkning = pd.read_csv('data/stockholms_kommun.csv')

stockholm_kommun = stockholm_kommun.merge(stockholm_kommun_befolkning,
                                          left_on="Stadsdel",
                                          right_on="stadsdelsområde",
                                          how="left")

stockholm_kommun['nya_fall_vecka_10000'] = stockholm_kommun['nya_fall_vecka'] / stockholm_kommun['befolkning_2019'] * 10000

df = stockholm_kommun
regions = list(df['Stadsdel'].unique())

fig = make_subplots(5, 3, subplot_titles=(regions), shared_xaxes=True)

rows = [1,1,1,2,2,2,3,3,3,4,4,4,5,5]
cols = [1,2,3,1,2,3,1,2,3,1,2,3,1,2]

# New cases per week
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Stadsdel'] == region]),
            y=list(df['nya_fall_vecka'][df['Stadsdel'] == region]),
            showlegend=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        ), row, col
    )

# New cases per week per 10,000
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Stadsdel'] == region]),
            y=list(df['nya_fall_vecka_10000'][df['Stadsdel'] == region]),
            visible=False,
            showlegend=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        ), row, col
    )

fig.update_xaxes(
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)
fig.update_yaxes(
    matches='y',
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)


fig.update_layout(
    title="<b>Bekräftade Fall inom Stockholms Kommun per Vecka</b>",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=700,
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.13,
            yanchor='top',
            buttons=list([
                dict(label="Antal Fall",
                     method='update',
                     args=[{'visible': [True]*14 + [False]*14},
                             {'title': "<b>Bekräftade Fall inom Stockholms Kommun per Vecka</b>"}]),
                dict(label="Antal Fall per 10,000",
                     method='update',
                     args=[{'visible': [False]*14 + [True]*14},
                             {'title': "<b>Bekräftade Fall inom Stockholms Kommun per Vecka (per 10,000)</b>"}]),
            ])
        )
    ]
)

fig.add_annotation(
    dict(
        x=0,
        y=-0.15,
        text="Källa: Folkhälsomyndigheten",
        showarrow=False,
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='auto',
        xshift=0,
        yshift=0,
        font=dict(
            size=11,
            color='dimgray'
        )
    )

)

fig.write_html('graphs/stockholm/cases_stockholm_kommun.html')

# ---------------------------------------------------------------
# Graph - daily cases per area of Stockholm Kommun (single graph)
# Filename: cases_stockholm_kommun_single
# ---------------------------------------------------------------

fig = go.Figure()

# New cases per week
for region in regions:
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Stadsdel'] == region]),
            y=list(df['nya_fall_vecka'][df['Stadsdel'] == region]),
            name=region,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        )
    )

# New cases per week per 10,000
for region in regions:
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Stadsdel'] == region]),
            y=list(df['nya_fall_vecka_10000'][df['Stadsdel'] == region]),
            name=region,
            visible=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        )
    )

fig.update_layout(
    title="<b>Bekräftade Fall inom Stockholms Kommun</b>",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        title="Vecka",
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    height=700,
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
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
                dict(label="Antal Fall",
                     method='update',
                     args=[{'visible': [True]*14 + [False]*14},
                             {'title': "<b>Bekräftade Fall inom Stockholms Kommun per Vecka</b>"}]),
                dict(label="Antal Fall per 10,000",
                     method='update',
                     args=[{'visible': [False]*14 + [True]*14},
                             {'title': "<b>Bekräftade Fall inom Stockholms Kommun per Vecka (per 10,000)</b>"}]),
            ])
        )
    ]
)

fig.write_html('graphs/stockholm/cases_stockholm_kommun_single.html')

# =============================================================================
# Intensive ward
# =============================================================================

# ----------------------------
# Graph - daily intensive ward
# Filename: intensive_ward_all
# ----------------------------

# Data on intensive ward patients
hospital = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                         sheet_name='Antal intensivvårdade per dag')

hospital['Datum_vårdstart'] = pd.to_datetime(hospital['Datum_vårdstart'],
                                             format='%Y-%m-%d')

# 7 day rolling average
hospital['7_day_rolling'] = hospital['Antal_intensivvårdade'].rolling(window=7).mean()

hospital = hospital.dropna()

fig = go.Figure()

# 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(hospital['Datum_vårdstart']),
        y=list(hospital['7_day_rolling']),
        showlegend=False,
        text=list(hospital['Antal_intensivvårdade']),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='blue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '<b>Medelvärde</b>: %{y:.1f}<br>'+
        '<b>Daglig</b>: %{text}'
    )
)

# Bar chart with daily values as reported
fig.add_trace(
    go.Bar(
        x=list(hospital['Datum_vårdstart']),
        y=list(hospital['Antal_intensivvårdade']),
        marker=dict(color='rgba(200, 220, 255, 0.5)'),
        showlegend=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    title="<b>Antal Intensivvårdade per Dag</b><br><sup>7 dagar glidande medelvärde",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    xaxis=dict(
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        title="Antal Intensivvårdade",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
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
    ]
)

fig.write_html('graphs/intensiv/intensive_ward_all.html')

# ---------------------------------------
# Graph - daily intensive ward per region
# Filename: intensive_ward_per_county
# ---------------------------------------

# Read regional data
regions = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                        sheet_name='Veckodata Region')

# Replace county names with desired names
regions = regions.replace(
    {
        'Jämtland Härjedalen': 'Jämtland',
        'Sörmland': 'Södermanland'
    })

regions = regions.merge(counties_pop[['county', 'population_2019']],
                        left_on='Region',
                        right_on='county',
                        how='left')

regions['Intensivvård_per_10000'] = regions['Antal_intensivvårdade_vecka'] / regions['population_2019'] * 10000

df = regions
regions_list = list(df['Region'].unique())

fig = make_subplots(5, 5, subplot_titles=(regions_list), shared_xaxes=True)

rows = [1,1,1,1,1,2,2,2,2,2,3,3,3,3,3,4,4,4,4,4,5]
cols = [1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1,2,3,4,5,1]

for region, row, col in zip(regions_list, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Region'] == region]),
            y=list(df['Antal_intensivvårdade_vecka'][df['Region'] == region]),
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}',
            showlegend=False
        ), row, col
    )

for region, row, col in zip(regions_list, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Region'] == region]),
            y=list(df['Intensivvård_per_10000'][df['Region'] == region]),
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<extra></extra>'+
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}',
            showlegend=False,
            visible=False
        ), row, col
    )


fig.update_xaxes(
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)
fig.update_yaxes(
    matches='y',
    linewidth=1,
    linecolor='black',
    gridwidth=1,
    gridcolor='rgb(240, 240, 240)'
)

fig.update_layout(
    title="<b>Antal Intensivvådade per Län</b>",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=800,
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                dict(label="Antal Intensivvådade",
                    method='update',
                    args=[{'visible': [True]*21 + [False]*21},
                          {'title': "<b>Antal Intensivvådade per Län</b>"}]),
                dict(label="Antal per 10,000",
                    method='update',
                    args=[{'visible': [False]*21 + [True]*21},
                          {'title': "<b>Antal Intensivvådade per Län (per 10,000)</b>"}]),
            ])
        )
    ]
)

# Add source annotation
fig.add_annotation(
    x=0,
    y=-0.15,
    text="Källa: Folkhälsomyndigheten",
    showarrow=False,
    xref='paper',
    yref='paper',
    xanchor='left',
    yanchor='auto',
    xshift=0,
    yshift=0,
    font=dict(
        size=11,
        color='dimgray'
    )
)

fig.write_html('graphs/intensiv/intensive_ward_per_county.html')

# ------------------------------------------------------
# Graph - daily intensive ward per region (single graph)
# Filename: intensive_ward_per_county_single
# ------------------------------------------------------

fig = go.Figure()

for region in regions_list:
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Region'] == region]),
            y=list(df['Antal_intensivvårdade_vecka'][df['Region'] == region]),
            name=region,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        )
    )

for region in regions_list:
    fig.add_trace(
        go.Scatter(
            x=list(df['veckonummer'][df['Region'] == region]),
            y=list(df['Intensivvård_per_10000'][df['Region'] == region]),
            name=region,
            visible=False,
            hoverlabel=dict(
                bgcolor='white',
                bordercolor='gray',
                font=dict(
                    color='black'
                )
            ),
            hovertemplate=
            '<b>Vecka %{x}</b><br>'+
            '<b>Cases</b>: %{y}'
        )
    )


fig.update_layout(
    title="<b>Antal Intensivvådade per Län</b>",
    xaxis=dict(
        title="Vecka",
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        linewidth=1,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=700,
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
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
                dict(label="Antal Intensivvådade",
                    method='update',
                    args=[{'visible': [True]*21 + [False]*21},
                          {'title': "<b>Antal Intensivvådade per Län</b>"}]),
                dict(label="Antal per 10,000",
                    method='update',
                    args=[{'visible': [False]*21 + [True]*21},
                          {'title': "<b>Antal Intensivvådade per Län (per 10,000)</b>"}]),
            ])
        )
    ]
)

fig.write_html('graphs/intensiv/intensive_ward_per_county_single.html')

# =============================================================================
# Deaths
# =============================================================================

# --------------------
# Graph - daily deaths
# Filename: deaths_all
# --------------------

# Data on daily deaths
daily_deaths = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                             sheet_name='Antal avlidna per dag')

# Drop row which shows deaths where the date is unknown
daily_deaths = daily_deaths[daily_deaths['Datum_avliden'] != 'Uppgift saknas']

daily_deaths['Datum_avliden'] = pd.to_datetime(daily_deaths['Datum_avliden'],
                                               format='%Y-%m-%d')

# 7 day rolling average
daily_deaths['total_7_day'] = daily_deaths['Antal_avlidna'].rolling(window=7).mean()

fig = go.Figure()

df = daily_deaths[daily_deaths['Datum_avliden']>='2020-03-17']

# 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(df['Datum_avliden']),
        y=list(df['total_7_day']),
        text=list(df['Antal_avlidna']),
        showlegend=False,
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='blue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '<b>Medelvärde</b>: %{y:.1f}<br>'+
        '<b>Daglig</b>: %{text}'
    )
)

# Bar chart with daily deaths as reported
fig.add_trace(
    go.Bar(
        x=list(df['Datum_avliden']),
        y=list(df['Antal_avlidna']),
        marker=dict(color='rgba(200, 220, 255, 0.5)'),
        showlegend=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    title="<b>Antal Avlidna i COVID-19</b><br><sup>7 dagar glidande medelvärde",
    xaxis=dict(
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        title="Antal Avlidna",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/deaths/deaths_all.html')

# ----------------------------------------
# Graph - weekly deaths vs. 5 year average
# Filename: deaths_weekly
# ----------------------------------------

# Statistiska centralbyrån data on weekly deaths from 2015 to 2019
all_deaths_url = "https://www.scb.se/en/finding-statistics/statistics-by-subject-area/population/population-composition/population-statistics/pong/tables-and-graphs/preliminary-statistics-on-deaths/"

sweden_weekly = pd.read_excel(all_deaths_url,
                              sheet_name = 'Tabell 1',
                              skiprows = 6,
                              usecols = [0,1,2,3,4,5,6]
                             )

# Remove 29th February to give same number of days in each year. Also drop the
# row that contained deaths with an unknown date.
sweden_weekly = sweden_weekly[
    ~sweden_weekly['DagMånad'].isin(['29 februari', 'Okänd dödsdag '])
]

years = {
    '2015': 'weekly_2015', '2016': 'weekly_2016', '2017': 'weekly_2017',
    '2018': 'weekly_2018', '2019': 'weekly_2019', '2020': 'weekly_2020'
}

# Create new columns for each year with the 7 day rolling sum, i.e. the weekly
# total. Then select every 7th day of the year to get week 1, week 2 etc.
# totals.
for year in years:
    sweden_weekly[years[year]] = sweden_weekly[year].rolling(window=7).sum()

sweden_weekly = sweden_weekly.iloc[range(6, 365, 7), :].reset_index(drop=True)

# Create new columns with 5-year average, maximum and minimum
sweden_weekly['5_year_average'] = sweden_weekly[
    ['weekly_2015', 'weekly_2016', 'weekly_2017',
     'weekly_2018', 'weekly_2019']].mean(axis=1)

sweden_weekly['5_year_min'] = sweden_weekly[
    ['weekly_2015', 'weekly_2016', 'weekly_2017',
     'weekly_2018', 'weekly_2019']].min(axis=1)

sweden_weekly['5_year_max'] = sweden_weekly[
    ['weekly_2015', 'weekly_2016', 'weekly_2017',
     'weekly_2018', 'weekly_2019']].max(axis=1)

# As deaths are added to the weekly totals as they are registered, weekly
# totals are often incomplete until 3 weeks later. Therefore data is selected
# up to the week 3 weeks before the most recent.
sweden_weekly = sweden_weekly.iloc[:sweden_weekly['weekly_2020'].idxmin() - 3 ,:]

df = sweden_weekly

fig = go.Figure()

# The 5 year min and max are ploted, with the area between them shaded. As it
# has to be a continuous line, the minimum data is reversed to plot back to
# the origin.
fig.add_trace(
    go.Scatter(
        x=list(range(1, len(df['DagMånad']) + 1)) + list(range(1, len(df['DagMånad']) + 1))[::-1],
        y=list(df['5_year_max']) + list(df['5_year_min'][::-1]),
        name="5 year min/max",
        line=dict(color='rgba(200, 200, 200, 0.5)'),
        fill='toself',
        fillcolor='rgba(200, 200, 200, 0.5)',
        hoverinfo='skip'
        )
    )

# 5-year average
fig.add_trace(
    go.Scatter(
        x=list(range(1, len(df['DagMånad']) + 1)),
        y=list(df['5_year_average']),
        name="5 year avg.",
        line=dict(dash='dash'),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='red',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x} - 2015-2019</b><br>'+
        '%{y:.1f}'
    )
)

# 2020 deaths
fig.add_trace(
    go.Scatter(
        x=list(range(1, len(df['DagMånad']) + 1)),
        y=list(df['weekly_2020']),
        line=dict(color='blue'),
        name="2020",
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='blue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>Vecka %{x} - 2020</b><br>'+
        '%{y:.1f}'
    )
)

fig.update_layout(
    title="<b>Antal Avlidna per Vecka (2020) vs. Medelvärde över 5 år (2015-2019)",
    hovermode='x',
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        title="Vecka",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    yaxis=dict(
        title="Antal Avlidna",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    legend=dict(traceorder='reversed'),
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Statistiska Centralbyrån",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/deaths/deaths_weekly.html')

# ----------------------------
# Graph - case fatality rate
# Filename: case_fatality_rate
# ----------------------------

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=list(åldersgrupp['Åldersgrupp']),
        y=list(åldersgrupp['case_fatality_rate']),
        marker=dict(
            color='skyblue'
        ),
        text=list(åldersgrupp['case_fatality_rate_rounded']),
        textposition="auto",
        textfont=dict(
            family='arial'
        ),
        texttemplate='%{text:.4f}',
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '%{y:.4f}'
    )
)
fig.update_layout(
    title="<b>Case Fatality Rate by Age Group</b>",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    xaxis=dict(
        title="Åldersgrupp",
        linewidth=2,
        linecolor='black'
    ),
    yaxis=dict(
        title="Case Fatality Rate",
        gridcolor='rgb(240, 240, 240)',
        gridwidth=2,
        linewidth=2,
        linecolor='black'
    ),
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/deaths/case_fatality_rate.html')

# ---------------------------
# Graph - deaths by age group
# Filename: deaths_age_group
# ---------------------------

åldersgrupp['deaths_%'] = åldersgrupp['Totalt_antal_avlidna'] / åldersgrupp['All'] * 100

fig = go.Figure()

# Total per age group
fig.add_trace(
    go.Bar(
        x=list(åldersgrupp['Åldersgrupp']),
        y=list(åldersgrupp['Totalt_antal_avlidna']),
        marker=dict(
            color='skyblue'
        ),
        text=list(åldersgrupp['Totalt_antal_avlidna']),
        textposition="auto",
        textfont=dict(
            family='arial'
        ),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '%{y}'
    )
)

# % of age group
fig.add_trace(
    go.Bar(
        x=list(åldersgrupp['Åldersgrupp']),
        y=list(åldersgrupp['deaths_%']),
        marker=dict(
            color='skyblue'
        ),
        visible=False,
        text=list(round(åldersgrupp['deaths_%'], 3)),
        textposition="auto",
        textfont=dict(
            family='arial'
        ),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<extra></extra>'+
        '<b>%{x}</b><br>'+
        '%{y:.3f}%'
    )
)

fig.update_layout(
    title="<b>Antal Avlidna per Åldersgrupp</b>",
    xaxis=dict(
        title="Åldersgrupp",
        linewidth=2,
        linecolor='black'
    ),
    yaxis=dict(
        title="Antal Avlidna",
        gridcolor='rgb(240, 240, 240)',
        gridwidth=2,
        linewidth=2,
        linecolor='black'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Folkhälsomyndigheten",
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
                dict(label="Antal Avlidna",
                     method='update',
                     args=[{'visible': [True, False]},
                           {'title': "<b>Antal Avlidna per Åldersgrupp</b>",
                            'yaxis': {'title': 'Antal Avlidna',
                                      'gridcolor': 'rgb(240, 240, 240)',
                                      'gridwidth': 2,
                                      'linewidth': 2,
                                      'linecolor': 'black'}}]),
                dict(label="Andel Avlidna",
                     method='update',
                     args=[{'visible': [False, True]},
                           {'title': "<b>Andelen av Befolkningen som har Dött i COVID-19 - per Åldersgrupp</b>",
                            'yaxis': {'title': '% per Åldersgrupp',
                                      'gridcolor': 'rgb(240, 240, 240)',
                                      'gridwidth': 2,
                                      'linewidth': 2,
                                      'linecolor': 'black'}}]),
                    ]
            )
    )]
)

fig.write_html('graphs/deaths/deaths_age_group.html')

# -----------------------
# Graph - comorbidities
# Filename: comorbidities
# -----------------------

URL_socialstyrelsen = "https://www.socialstyrelsen.se/globalassets/1-globalt/covid-19-statistik/statistik-over-antal-avlidna-i-covid-19/statistik-covid19-avlidna.xlsx"

# Read data from socialstyrelsen on deaths by age group and comorbidities
socialstyrelsen = pd.read_excel(URL_socialstyrelsen,
                                sheet_name="Övergripande statistik",
                                skiprows=6,
                                usecols=[0,1,3,5])

# Select rows with data on comorbidities
comorbidities = socialstyrelsen.iloc[[15,16,17,18,20], :]

comorbidities.columns = ['Sjukdomsgrupper', 'Totalt', 'Män', 'Kvinnor']

fig = go.Figure()

df = comorbidities

# Män
fig.add_trace(
    go.Bar(
        x=list(df['Sjukdomsgrupper']),
        y=list(df['Män']),
        marker=dict(
            color='skyblue'
        ),
        name="Män",
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<b>%{x}</b><br>'+
        '%{y}'
    )
)

# Kvinnor
fig.add_trace(
    go.Bar(
        x=list(df['Sjukdomsgrupper']),
        y=list(df['Kvinnor']),
        marker=dict(
            color='darkblue'
        ),
        name="Kvinnor",
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='darkblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<b>%{x}</b><br>'+
        '%{y}'
    )
)

fig.update_layout(
    title="<b>Antal Avlidna i COVID-19 Uppdelat på Sjukdomsgrupper</b>",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        linewidth=2,
        linecolor='black'
    ),
    yaxis=dict(
        title="Antal Avlidna",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Socialstyrelsen",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/deaths/comorbidities.html')

# ---------------------------------
# Graph - number of comorbidities
# Filename: number_of_comorbidities
# ---------------------------------

# Select rows with data on number of comorbidities per patient
number_comorbidities = socialstyrelsen.iloc[[20,21,22], :]
number_comorbidities.columns = ['Sjukdomsgrupper', 'Totalt', 'Män', 'Kvinnor']

fig = go.Figure()

df = number_comorbidities

# Män
fig.add_trace(
    go.Bar(
        x=list(df['Sjukdomsgrupper']),
        y=list(df['Män']),
        name="Män",
        marker=dict(
            color='skyblue'
        ),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='skyblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<b>%{x}</b><br>'+
        '%{y}'
    )
)

# Kvinnor
fig.add_trace(
    go.Bar(
        x=list(df['Sjukdomsgrupper']),
        y=list(df['Kvinnor']),
        name="Kvinnor",
        marker=dict(
            color='darkblue'
        ),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='darkblue',
            font=dict(
                color='black'
            )
        ),
        hovertemplate=
        '<b>%{x}</b><br>'+
        '%{y}'
    )
)

fig.update_layout(
    title="<b>Antal av Sjukdomsgrupper</b>",
    font=dict(
        family='Arial'
    ),
    xaxis=dict(
        linewidth=2,
        linecolor='black'
    ),
    yaxis=dict(
        title="Antal Avlidna",
        linewidth=2,
        linecolor='black',
        gridwidth=1,
        gridcolor='rgb(240, 240, 240)'
    ),
    plot_bgcolor='white',
    annotations=[
        dict(
            x=0,
            y=-0.15,
            text="Källa: Socialstyrelsen",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/deaths/number_of_comorbidities.html')

# =============================================================================
# Maps
# =============================================================================

# ---------------------------
# Map - total cases in Sweden
# Filename: Sweden_map_cases
# ---------------------------

mapbox_access_token = config.mapbox_key

# Read data on Swedish counties
county_data = pd.read_excel("data/Folkhälsomyndigheten.xlsx",
                            sheet_name='Totalt antal per region')

# Replace region names desired names
county_data = county_data.replace(
    {
        'Jämtland Härjedalen': 'Jämtland',
        'Sörmland': 'Södermanland'
    }
)

# geojson data for Swedish county boundaries
with open('data/geojson/sweden-counties.geojson') as file:
    counties = json.load(file)

# Create plot of total number of deaths per county
fig = go.Figure(
    go.Choroplethmapbox(
        geojson=counties,
        featureidkey='properties.name',
        locations=county_data['Region'],
        z=county_data['Totalt_antal_fall'],
        colorscale=[
            [0, 'rgb(255, 240, 240)'],
            [0.2, 'rgb(180, 110, 110)'],
            [0.7, 'rgb(140, 70, 70)'],
            [1, 'rgb(120, 50, 50)']
        ],
        showscale=False,
        text=county_data['Region'],
        hovertemplate =
        '<extra></extra>' +
        '<b>%{text}</b><br>' +
        '%{z}'
    )
)

fig.update_layout(
    title="<b>Bekräftade Fall</b>",
    hovermode ='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=63,
            lon=17
        ),
        pitch=0,
        zoom=3.5
    ),
    height=700,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4
    ),
    annotations=[
        dict(
            x=0,
            y=-0.05,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('maps/Sweden_map_cases.html')

# --------------------------------
# Map - total cases per 10,000
# Filename: Sweden_map_cases_10000
# --------------------------------

# Merge county populations
county_data = county_data.merge(counties_pop[['county', 'population_2019']],
                                left_on='Region',
                                right_on='county',
                                how='left')

county_data['cases_per_10000'] = round(county_data['Totalt_antal_fall'] / county_data['population_2019'] * 1000, 3)

# Create plot of total number of deaths per 1000 per county
fig = go.Figure(
    go.Choroplethmapbox(
        geojson=counties,
        featureidkey='properties.name',
        locations=county_data['Region'],
        z=county_data['cases_per_10000'],
        colorscale=[
            [0, 'rgb(255, 240, 240)'],
            [0.2, 'rgb(180, 110, 110)'],
            [0.7, 'rgb(140, 70, 70)'],
            [1, 'rgb(120, 50, 50)']
        ],
        showscale=False,
        text=county_data['Region'],
        hovertemplate =
        '<extra></extra>' +
        '<b>%{text}</b><br>' +
        '%{z}'
    )
)

fig.update_layout(
    title="<b>Bekräftade Fall per 10,000</b>",
    hovermode ='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=63,
            lon=17
        ),
        pitch=0,
        zoom=3.5
    ),
    #width=500,
    height=700,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4
    ),
    annotations=[
        dict(
            x=0,
            y=-0.05,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('maps/Sweden_maps_cases_10000.html')

# ----------------------------
# Map - total deaths in Sweden
# Filename: Sweden_map_deaths
# ----------------------------

# Create plot of total number of deaths per county
fig = go.Figure(
    go.Choroplethmapbox(
        geojson=counties,
        featureidkey='properties.name',
        locations=county_data['Region'],
        z=county_data['Totalt_antal_avlidna'],
        colorscale=[
            [0, 'rgb(255, 240, 240)'],
            [0.2, 'rgb(180, 110, 110)'],
            [0.7, 'rgb(140, 70, 70)'],
            [1, 'rgb(120, 50, 50)']
        ],
        showscale=False,
        text=county_data['Region'],
        hovertemplate =
        '<extra></extra>' +
        '<b>%{text}</b><br>' +
        '%{z}'
    )
)

fig.update_layout(
    title="<b>Antal Avlidna</b>",
    hovermode ='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=63,
            lon=17
        ),
        pitch=0,
        zoom=3.5
    ),
    height=700,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4
    ),
    annotations=[
        dict(
            x=0,
            y=-0.05,
            text="Källa: Folkhälsomyndigheten",
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
    ]
)

fig.write_html('maps/Sweden_map_deaths.html')

# ---------------------------------
# Map - total deaths per 10,000
# Filename: Sweden_map_deaths_10000
# ---------------------------------

county_data['deaths_per_10000'] = round(county_data['Totalt_antal_avlidna'] / county_data['population_2019'] * 1000, 3)

# Create plot of total number of deaths per 10,000 per county
fig = go.Figure(
    go.Choroplethmapbox(
        geojson=counties,
        featureidkey='properties.name',
        locations=county_data['Region'],
        z=county_data['deaths_per_10000'],
        colorscale=[
            [0, 'rgb(255, 240, 240)'],
            [0.2, 'rgb(180, 110, 110)'],
            [0.7, 'rgb(140, 70, 70)'],
            [1, 'rgb(120, 50, 50)']
        ],
        showscale=False,
        text=county_data['Region'],
        hovertemplate =
        '<extra></extra>' +
        '<b>%{text}</b><br>' +
        '%{z}'
    )
)

fig.update_layout(
    title="<b>Antal Avlidna per 10,000</b>",
    hovermode ='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=63,
            lon=17
        ),
        pitch=0,
        zoom= 3.5
    ),
    height=700,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4
    ),
    annotations=[
        dict(
            x=0,
            y=-0.05,
            text="Källa: Folkhälsomyndigheten",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('maps/Sweden_maps_deaths_10000.html')
