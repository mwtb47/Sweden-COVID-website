# ======================================================================
# Script to save maps summarising deaths data as html files. This will
# be imported as a module into main.py.
# ======================================================================

from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go

class Deaths:
    """Class containing methods to save four graphs as html files:
        - daily deaths in Sweden
        - 5 year average vs. 2020/2021 weekly deaths
        - case fatality rate by age group
        - number of deaths by age group
    """
    def __init__(self, template, plot_config, fhm_data, counties_pop):
        self.template = template
        self.plot_config = plot_config
        self.fhm_data = fhm_data
        self.counties_pop = counties_pop

    def prepare_data(self):
        """Prepare data on covid deaths for graphs."""
        # Data on daily deaths
        daily_deaths = self.fhm_data['Antal avlidna per dag'].copy()

        # Drop row showing deaths where the date is unknown
        daily_deaths = daily_deaths[
            daily_deaths['Datum_avliden'] != 'Uppgift saknas']

        daily_deaths['Datum_avliden'] = pd.to_datetime(
            daily_deaths['Datum_avliden'],
            format='%Y-%m-%d')

        # 7 day rolling average
        daily_deaths['total_7_day'] = daily_deaths['Antal_avlidna'].rolling(
            window=7).mean()

        self.daily_deaths = daily_deaths

    def get_age_group_populations(self):
        """Data on population by age group."""
        population_ages = pd.read_excel(
            'data/age_pyramid.xlsx',
            sheet_name='Data',
            skiprows=6,
            usecols=list(range(8,13)))

        population_ages = population_ages.dropna()

        # As the data was set up for a population pyramid split between
        # males and females, the population sizes for males are
        # negative. This makes all population numbers positive.
        population_ages[
            ['födda i Sverige.4', 'utrikes födda.4']] = population_ages[
            ['födda i Sverige.3', 'utrikes födda.3']].abs()

        # Populations are broken down by domestic and foreign born,
        # these are summed to get the population totals.
        population_ages['Men'] = (population_ages['födda i Sverige.3']
                                  + population_ages['utrikes födda.3'])
        population_ages['Women'] = (population_ages['födda i Sverige.4']
                                    + population_ages['utrikes födda.4'])
        population_ages['All'] = (population_ages['Men']
                                  + population_ages['Women'])

        population_ages = population_ages[['Ålder.1', 'Men', 'Women', 'All']]

        def group_ages(x):
            """The ages need to be grouped as they are in the COVID-19
            data. The age groups are 0-9, 10-19 etc. so the ages can be
            divided by 10, with the quotient forming the first age in
            the range and the quotient plus 9 forming the upper limit of
            the range.
            """
            quotient = x // 10
            string = str(quotient * 10) + '-' + str(quotient * 10 + 9)
            if string == '90-99' or string == '100-109':
                string = '90+'
            return string

        # '100+' is replaced with 100 so the group_ages function can handle it
        population_ages = population_ages.replace('100+', 100)
        population_ages['group'] = population_ages['Ålder.1'].apply(group_ages)

        self.population_grouped_ages = population_ages.groupby('group')[
            ['Men', 'Women', 'All']].sum().reset_index()

    def prepare_deaths_per_age_group(self):
        """Prepare data on deaths per age group for plotting on graphs.
        """
        # Data on cases and deaths by age group
        åldersgrupp = self.fhm_data['Totalt antal per åldersgrupp']

        # Drop data with unknown groups
        åldersgrupp = åldersgrupp[(åldersgrupp['Åldersgrupp']
                                   != 'Uppgift saknas')].dropna(how='all')

        åldersgrupp['Åldersgrupp'] = [
            '0-9', '10-19', '20-29', '30-39', '40-49',
            '50-59', '60-69', '70-79', '80-89', '90+'
        ]

        åldersgrupp['case_fatality_rate'] = (
            åldersgrupp['Totalt_antal_avlidna']
            / åldersgrupp['Totalt_antal_fall'])

        åldersgrupp['case_fatality_rate_rounded'] = round(
            åldersgrupp['case_fatality_rate'], 4)

        åldersgrupp = åldersgrupp.merge(
            self.population_grouped_ages[['group', 'All']],
            left_on='Åldersgrupp',
            right_on='group',
            how='left')

        åldersgrupp['deaths_%'] = (åldersgrupp['Totalt_antal_avlidna']
                                   / åldersgrupp['All'] * 100)

        self.åldersgrupp = åldersgrupp

    def graph_deaths_all(self):
        """Plot graph showing daily covid-19 deaths and save as an html
         file.

        File name: deaths_all.html
        """
        df = self.daily_deaths
        df = df[df['Datum_avliden']>='2020-03-17']

        fig = go.Figure()

        # 7 day rolling average
        fig.add_trace(
            go.Scatter(
                x=list(df['Datum_avliden']),
                y=list(df['total_7_day']),
                text=list(df['Antal_avlidna']),
                showlegend=False,
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='steelblue',
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
            template=self.template,
            title=("<b>Antal Avlidna i COVID-19</b><br>"
                   "<sub>7 dagar glidande medelvärde<br>"
                   "Källa: Folkhälsomyndigheten"),
            yaxis_title="Antal Avlidna",
            height=600,
            margin=dict(t=90, b=30)
        )

        fig.write_html('graphs/deaths/deaths_all.html',
                       config=self.plot_config)

    def prepare_weekly_deaths_data(self):
        """Download and prepare data on the 2015-2019 five year average
        weekly deaths and the weekly deaths in 2020 and 2021.
        """
        def get_recent_monday():
            """The URL for weekly deaths contains the date that it was
            updated, therefore the date of the most recent Monday has to
            be found.
            """
            today = date.today()
            week_ago = today - timedelta(days=6)

            for day in pd.date_range(week_ago, today):
                if day.weekday() == 0:
                    return day.strftime('%Y-%m-%d')

        # Statistiska centralbyrån data on weekly deaths from 2015 to 2019
        all_deaths_url = ("https://www.scb.se/hitta-statistik/"
                          "statistik-efter-amne/befolkning/"
                          "befolkningens-sammansattning/befolkningsstatistik/"
                          "pong/tabell-och-diagram/"
                          "preliminar-statistik-over-doda-publicerad-"
                          + get_recent_monday() + "/")

        sweden_weekly = pd.read_excel(
            all_deaths_url,
            sheet_name = 'Tabell 1',
            skiprows = 6,
            usecols = [0,1,2,3,4,5,6,7]
        )

        # Remove 29th February to give same number of days in each year.
        # Also drop the row that contained deaths with an unknown date.
        sweden_weekly = sweden_weekly[~sweden_weekly['DagMånad'].isin(
            ['29 februari', 'Okänd dödsdag '])]

        sweden_average = sweden_weekly[['DagMånad', '2015', '2016',
                                        '2017', '2018', '2019']].copy()
        sweden_pandemic = sweden_weekly[['DagMånad', '2020', '2021']].copy()

        # Create new columns for each year with the 7 day rolling sum,
        # i.e. the weekly total. Then select every 7th day of the year
        # to get week 1, week 2 etc. totals.
        years_average = {
            '2015': 'weekly_2015', '2016': 'weekly_2016',
            '2017': 'weekly_2017', '2018': 'weekly_2018',
            '2019': 'weekly_2019'
        }
        for year in years_average:
            sweden_average[years_average[year]] = sweden_average[year].rolling(
                window=7).sum()

        sweden_pandemic['weekly_2020'] = sweden_pandemic['2020'].rolling(
            window=7).sum()
        sweden_pandemic['weekly_2021'] = sweden_pandemic['2021'].rolling(
            window=7).sum()

        # Take every 7th day to form 7-day periods
        sweden_average = sweden_average.iloc[range(6, 365, 7), :].reset_index(
            drop=True)
        sweden_pandemic = sweden_pandemic.iloc[range(6, 365, 7), :].reset_index(
            drop=True)

        # Create new columns with 5-year average, maximum and minimum
        sweden_average['5_year_average'] = sweden_average[
            ['weekly_2015', 'weekly_2016', 'weekly_2017',
             'weekly_2018', 'weekly_2019']].mean(axis=1)

        sweden_average['5_year_min'] = sweden_average[
            ['weekly_2015', 'weekly_2016', 'weekly_2017',
             'weekly_2018', 'weekly_2019']].min(axis=1)

        sweden_average['5_year_max'] = sweden_average[
            ['weekly_2015', 'weekly_2016', 'weekly_2017',
             'weekly_2018', 'weekly_2019']].max(axis=1)

        # Append the data frame to itself to create two years worth of
        # averages.
        sweden_average = sweden_average.append(sweden_average)
        sweden_average['pandemic'] = sweden_pandemic['weekly_2020'].append(
                    sweden_pandemic['weekly_2021'])
        sweden_average['år'] = [2020]*52 + [2021]*52

        # Drop the weeks which have not happened yet and then remove the
        # most recent 3 weeks to avoid showing incomplete data (it takes
        # a couple of weeks for all deaths to be published).
        sweden_average = sweden_average.iloc[
            :(sweden_average['pandemic'] == 0).argmax() - 3, :]

        self.sweden_average = sweden_average

    def graph_deaths_weekly(self):
        """Plot graph showing 5 year average vs. 2020/2021 weekly deaths
        and save as an html file.

        File name: deaths_weekly.html
        """
        df = self.sweden_average

        df['DM_str'] = [x.split(' ')[0] + ' ' + x.split(' ')[1][:3]
                        for x in df['DagMånad']]

        fig = go.Figure()

        # The 5 year min and max are ploted, with the area between them
        # shaded. As it has to be a continuous line, the minimum data is
        # reversed to plot back to the origin.
        fig.add_trace(
            go.Scatter(
                x=[list(df['år']) + list(df['år'][::-1]),
                   list(df['DM_str']) + list(df['DM_str'][::-1])],
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
                x=[list(df['år']), list(df['DM_str'])],
                y=list(df['5_year_average']),
                name="5 year avg.",
                line=dict(dash='dash'),
                text=df['DM_str'],
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='red',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{text} - 2015-2019</b><br>'+
                '%{y:.1f}'
            )
        )

        # Pandemic deaths
        fig.add_trace(
            go.Scatter(
                x=[list(df['år']), list(df['DM_str'])],
                y=list(df['pandemic']),
                line=dict(color='blue'),
                name="2020/2021",
                customdata=np.stack((
                    df['DM_str'],
                    df['år']
                ), axis=-1),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='blue',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{customdata[0]} - %{customdata[1]}</b><br>'+
                '%{y:.1f}'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Antal Avlidna per Vecka (2020-2021) vs.<br>"
                   "Medelvärde över 5 år (2015-2019)</b><br>"
                   "<sub>Källa: Statistiska Centralbyrån"),
            xaxis=dict(
                title="7 Days Ending",
                #showdividers=False,
                tickmode="auto",
                nticks=15,
                tickangle=45
            ),
            yaxis=dict(
                title="Antal Avlidna",
                separatethousands=True
            ),
            legend=dict(traceorder='reversed'),
            height=600,
            margin=dict(t=90, b=130)
        )

        fig.write_html('graphs/deaths/deaths_weekly.html',
                       config=self.plot_config)

    def graph_case_fatality_rate(self):
        """Plot graph showing case fatality rates by age group and save as
        an html file.

        File name: case_fatality_rate.html
        """
        df = self.åldersgrupp

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=list(df['Åldersgrupp']),
                y=list(df['case_fatality_rate']),
                marker=dict(
                    color='skyblue'
                ),
                text=list(df['case_fatality_rate_rounded']),
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
            template=self.template,
            title=("<b>Case Fatality Rate by Age Group</b>"
                   "<br><sub>Källa: Folkhälsomyndigheten"),
            height=600,
            margin=dict(t=80),
            xaxis=dict(
                title="Åldersgrupp",
                gridwidth=0
            ),
            yaxis_title="Case Fatality Rate"
        )

        fig.write_html('graphs/deaths/case_fatality_rate.html',
                       config=self.plot_config)

    def graph_deaths_age_group(self):
        """Plot graph showing the number of deaths per age group and save
        as an html file.

        File name: deaths_age_group.html
        """
        df = self.åldersgrupp

        fig = go.Figure()

        # Total per age group
        fig.add_trace(
            go.Bar(
                x=list(df['Åldersgrupp']),
                y=list(df['Totalt_antal_avlidna']),
                marker=dict(
                    color='skyblue'
                ),
                text=list(df['Totalt_antal_avlidna']),
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
                x=list(df['Åldersgrupp']),
                y=list(df['deaths_%']),
                marker=dict(
                    color='skyblue'
                ),
                visible=False,
                text=list(round(df['deaths_%'], 3)),
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
            template=self.template,
            title=("<b>Antal Avlidna per Åldersgrupp</b><br>"
                   "<sub>Källa: Folkhälsomyndigheten"),
            xaxis=dict(
                title="Åldersgrupp",
                gridwidth=0
            ),
            yaxis=dict(
                title="Antal Avlidna",
                separatethousands=True
            ),
            height=600,
            margin=dict(t=80),
            updatemenus=[
                dict(
                    direction='down',
                    x=1,
                    xanchor='right',
                    y=1.01,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="Antal Avlidna",
                             method='update',
                             args=[{'visible': [True, False]},
                                   {'title': ("<b>Antal Avlidna per "
                                              "Åldersgrupp</b><br><sub>Källa: "
                                              "Folkhälsomyndigheten"),
                                    'yaxis': {'title': 'Antal Avlidna',
                                              'gridcolor': 'rgb(240, 240, 240)',
                                              'gridwidth': 2,
                                              'linewidth': 2,
                                              'linecolor': 'black'}}]),
                        dict(label="Andel Avlidna",
                             method='update',
                             args=[{'visible': [False, True]},
                                   {'title': ("<b>Andelen av Befolkningen som "
                                              "har Dött i COVID-19 - per "
                                              "Åldersgrupp</b><br><sub>Källa: "
                                              "Folkhälsomyndigheten"),
                                    'yaxis': {'title': '% per Åldersgrupp',
                                              'gridcolor': 'rgb(240, 240, 240)',
                                              'gridwidth': 2,
                                              'linewidth': 2,
                                              'linecolor': 'black'}}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/deaths/deaths_age_group.html',
                       config=self.plot_config)


def main(template, plot_config, fhm_data, counties_pop):
    """Initiate Deaths class and run methods to plot graphs."""
    deaths = Deaths(template, plot_config, fhm_data, counties_pop)
    deaths.prepare_data()
    deaths.get_age_group_populations()
    deaths.prepare_deaths_per_age_group()
    deaths.prepare_weekly_deaths_data()
    deaths.graph_deaths_all()
    deaths.graph_deaths_weekly()
    deaths.graph_case_fatality_rate()
    deaths.graph_deaths_age_group()
