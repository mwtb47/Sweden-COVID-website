# ======================================================================
# Script to save graphs summarising the test data as html files. This
# will be imported as a module into main.py.
# ======================================================================

from datetime import date
from unicodedata import normalize

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from requests import get


class TestsData:
    """Class containing methods to prepare data on:
        - percentage of each age group who have tested positive
        - number of covid-19 tests and antibody tests per week
        - antibody test positivity rate for latest week by county
    """
    def __init__(self, fhm_data):
        self.fhm_data = fhm_data
        self.user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                           "Version/14.1 Safari/605.1.15")

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

        # The ages need to be grouped as they are in the COVID-19 data.
        # The age groups are 0-9, 10-19 etc. so the ages can be divided
        # by 10, with the quotient forming the first age in the range
        # and the quotient plus 9 forming the upper limit of the range.
        def group_ages(x):
            quotient = x // 10
            string = str(quotient * 10) + '-' + str(quotient * 10 + 9)
            if string == '90-99' or string == '100-109':
                string = '90+'
            return string

        # '100+' is replaced with 100 so the group_ages function can handle it
        population_ages = population_ages.replace('100+', 100)
        population_ages['group'] = population_ages['Ålder.1'].apply(group_ages)

        population_grouped_ages = population_ages.groupby('group')[
            ['Men', 'Women', 'All']].sum().reset_index()

        self.population_grouped_ages = population_grouped_ages

    def prepare_cases_per_age_group(self):
        """Prepare the data on the number of cases, cases % and case
        fatality rate by age group for plotting on graphs.
        """
        # Data on cases and deaths by age group
        åldersgrupp = self.fhm_data['Totalt antal per åldersgrupp']

        # Drop data with unknown groups
        åldersgrupp = åldersgrupp[
            åldersgrupp['Åldersgrupp'] != 'Uppgift saknas'].dropna(how='all')

        # Rename the age groups
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

        # Percentage in each age group who have tested positive
        åldersgrupp['case_%'] = (åldersgrupp['Totalt_antal_fall']
                                 / åldersgrupp['All'] * 100)

        # Percentage of population which has tested positive
        self.total_percentage = (sum(åldersgrupp['Totalt_antal_fall'])
                            / sum(åldersgrupp['All']) * 100)

        self.åldersgrupp = åldersgrupp

    def prepare_number_of_tests(self):
        """Download and prepare data on the number of covid-19 and
        antibody tests performed in Sweden.
        """
        tests_url = ("https://www.folkhalsomyndigheten.se/"
                     "smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/"
                     "statistik-och-analyser/antalet-testade-for-covid-19/")

        page = get(tests_url, headers={'User-Agent': self.user_agent}).text
        soup = BeautifulSoup(page, 'lxml')
        self.tables = soup.findAll('table')
        table_tests = self.tables[0]

        vecka=[]
        number_individuals=[]
        number_tests=[]
        number_antibody=[]

        # Iterate through the html table, extracting the week, number
        # of individual tests, number of total tests and number of
        # antibody tests.
        for row in table_tests.findAll('tr'):
            vecka.append(row.find('th').find(text=True))
            cells = row.findAll('td')
            if len(cells) > 0:
                number_individuals.append(
                    int(cells[0].find(text=True).replace(" ", "")))
                number_tests.append(
                    int(cells[1].find(text=True).replace(" ", "")))
                number_antibody.append(
                    int(cells[3].find(text=True).replace(" ", "")))

        df_temp = pd.DataFrame(
            {
                'year': 2021,
                'vecka':vecka[1:],
                'number_individual_tests':number_individuals,
                'number_tests': number_tests,
                'number_antibody': number_antibody,
            }
        )

        # Convert 'Vecka 10', 'Vecak 11' etc. into integer values 10,
        # 11 etc.
        df_temp['vecka'] = df_temp['vecka'].apply(
            lambda x: int(x.split(" ")[1]))

        # Webpage displays most recent 5 weeks therefore there are still
        # weeks from the end of 2020 whjch need to be dropped.
        current_week = int(date.today().strftime("%U"))
        df_temp = df_temp[df_temp['vecka'] <= current_week]

        # Append weekly test data from earlier in the year
        weekly_tests = pd.read_csv('data/weekly_tests.csv')
        weekly_tests = weekly_tests.append(df_temp).drop_duplicates()
        weekly_tests = weekly_tests.sort_values(['year', 'vecka'])

        # Write data to csv as webpage only displays data for the most
        # recent 5 weeks.
        weekly_tests.to_csv('data/weekly_tests.csv', index=False)

        # Create string formats of the numbers which are thousand comma
        # separated making them easier to read.
        cols = ['number_individual_tests', 'number_tests', 'number_antibody']
        for c in cols:
            weekly_tests[c + '_str'] = [f'{x:,}'.replace('.0', '')
                                        for x in weekly_tests[c]]

        # Plotly multicategory axes want to plot values found in both
        # categories first. As 2020 starts in week 8, it therefore plots
        # from week 8 in 2021 first, with weeks 1-7 at the end. A dummy
        # week number is set up for 2020 shifting all weeks by 7 to start
        # at week 1.
        weekly_tests['plot_vecka'] = weekly_tests['vecka'].copy()
        weekly_tests.iloc[:46, -1] = weekly_tests['plot_vecka'][:46] - 7

        self.weekly_tests = weekly_tests

    def prepare_antibody_tests(self):
        """Prepare data on antibody tests."""
        # Extract the table containing antibody test data from the html.
        table_antibodies = self.tables[2]

        län = []
        number_antibodies = []
        positive_antibodies = []

        # Iterate through the html table, extracting the län, number of
        # antibody tests and the number of positive antibody tests.
        for row in table_antibodies.findAll('tr'):
            län.append(row.find('th').find(text=True))
            cells = row.findAll('td')
            if len(cells) > 0:
                number_antibodies.append(
                    int(normalize(
                        'NFKD', cells[0].find(text=True)).replace(" ", "")))
                positive_antibodies.append(
                    int(normalize(
                        'NFKD', cells[1].find(text=True)).replace(" ", "")))

        antibodies = pd.DataFrame(
            {
                "län": län[1:],
                "number_tests": number_antibodies,
                "number_positive": positive_antibodies,
            }
        )
        antibodies = antibodies.replace("Jämtland/ Härjedalen", "Jämtland")

        # Percentage of tests with positive results
        antibodies['percent'] = round(antibodies['number_positive']
                                      / antibodies['number_tests'] * 100, 4)
        antibodies = antibodies.sort_values('percent')

        # Not sure why this is needed, but graph would not plot without it.
        antibodies['län'] = [i[:20] for i in antibodies['län']]

        # Set the color as skyblue for all the counties, with the marker
        # for the whole country being darkblue.
        antibodies['color'] = np.where(
            antibodies['län'] == 'Riket', 'darkblue', 'skyblue')

        # Extract the most recent week number to use in the graph title.
        text = self.tables[2].find('caption').find(text=True)
        self.week_str = 'Vecka ' + text.split('vecka ')[1][:2]

        self.antibodies = antibodies

    def return_data(self):
        """Run methods to prepare data and return dictionary of Data
        Frames.
        """
        self.get_age_group_populations()
        self.prepare_cases_per_age_group()
        self.prepare_number_of_tests()
        self.prepare_antibody_tests()

        return {
            'åldersgrupp': self.åldersgrupp,
            'weekly_tests': self.weekly_tests,
            'antibodies': self.antibodies,
            'total_percentage': self.total_percentage,
            'week_str': self.week_str
        }


class PlotTests:
    """Class containing methods to use the prepared data to save two
    graphs and one table as html files:
        - percentage of each age group who have tested positive
        - number of covid-19 tests and antibody tests per week
        - antibody test positivity rate for latest week by county
    """
    def __init__(self, data, template, plot_config):
        self.åldersgrupp = data['åldersgrupp']
        self.weekly_tests = data['weekly_tests']
        self.antibodies = data['antibodies']
        self.total_percentage = data['total_percentage']
        self.week_str = data['week_str']
        self.template = template
        self.plot_config = plot_config

    def graph_percentage_cases(self):
        """Plot graph showing percentage of age group who have tested
        positive per week and save as an html file.

        File name: percentage_cases.html
        """
        df = self.åldersgrupp

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=['All'] + list(df['Åldersgrupp']),
                y=[self.total_percentage] + list(df['case_%']),
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
            template=self.template,
            title=("<b>Andelen av Befolkningen som har Testat Positivt i "
                   "COVID-19</b><br><sub>Källa: Folkhälsomyndigheten"),
            xaxis=dict(
                title="Åldersgrupp",
                gridwidth=0
            ),
            yaxis_title="%",
            height=600,
            margin=dict(t=80)

        )

        fig.write_html('graphs/cases/percentage_cases.html',
                       config=self.plot_config)

    def graph_number_of_tests(self):
        """Plot graph showing number of individuals tested and the number of
        tests performed per week and save as an html file.

        File name: number_of_tests.html
        """
        df = self.weekly_tests

        fig = go.Figure()

        # Number of individual tests
        fig.add_trace(
            go.Scatter(
                x=[[2020] * 46 + [2021] * (len(df.index) - 46),
                   list(df['plot_vecka'])],
                y=list(df['number_individual_tests']),
                name="Individer",
                customdata=np.stack(
                    (df['plot_vecka'],
                     [2020] * 46 + [2021] * (len(df.index) - 46),
                     df['number_individual_tests_str']
                    ), axis=-1
                ),
                text=df['number_individual_tests_str'],
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='steelblue',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>Vecka %{customdata[0]} - %{customdata[1]}</b><br>'+
                '%{customdata[2]}'
            )
        )

        # Number of tests performed
        fig.add_trace(
            go.Scatter(
                x=[[2020] * 46 + [2021] * (len(df.index) - 46),
                   list(df['plot_vecka'])],
                y=list(df['number_tests']),
                name="Totalt",
                customdata=np.stack(
                    (df['plot_vecka'],
                     [2020] * 46 + [2021] * (len(df.index) - 46),
                     df['number_tests_str']
                    ), axis=-1
                ),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='red',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>Vecka %{customdata[0]} - %{customdata[1]}</b><br>'+
                '%{customdata[2]}'
            )
        )

        # Number of antibody tests
        fig.add_trace(
            go.Scatter(
                x=[[2020] * 28 + [2021] * (len(df.index) - 46),
                   list(df['vecka'][18:])],
                y=list(df['number_antibody'][18:]),
                name="Totalt",
                visible=False,
                customdata=np.stack(
                    (df['plot_vecka'][18:],
                     [2020] * 28 + [2021] * (len(df.index) - 46),
                     df['number_antibody_str'][18:]
                    ), axis=-1
                ),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='steelblue',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>Vecka %{customdata[0]} - %{customdata[1]}</b><br>'+
                '%{customdata[2]}'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Antal per Vecka - Nukleinsyrapåvisning</b>"
                   "<br><sub>Källa: Folkhälsomyndigheten"),
            yaxis_title="Antal Tester",
            height=600,
            margin=dict(t=70),
            updatemenus=[dict(
                direction='down',
                x=1,
                xanchor='right',
                y=1.02,
                yanchor='bottom',
                buttons=list([
                    dict(label="Nukleinsyrapåvisning",
                         method='update',
                         args=[{'visible': [True, True, False]},
                               {'title': ("<b>Antal per Vecka - "
                                          "Nukleinsyrapåvisning</b>"
                                          "<br><sub>Källa: "
                                          "Folkhälsomyndigheten")}]),
                    dict(label="Antikroppspåvisning",
                         method='update',
                         args=[{'visible': [False, False, True]},
                               {'title': ("<b>Antal per Vecka - "
                                          "Antikroppspåvisning</b>"
                                          "<br><sub>Källa: "
                                          "Folkhälsomyndigheten")}]),
                ])
            )]
        )

        fig.write_html('graphs/cases/number_of_tests.html',
                       config=self.plot_config)





    def graph_positive_antibody(self):
        """Plot graph showing percentage of antibody test which are positive
        per county and save as an html file.

        File name: positive_antibody.html
        """
        df = self.antibodies

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
            template=self.template,
            title=("<b>Andel Positiva Antikropps Tester - " + self.week_str
                   + "</b><br><sub>Källa: Folkhälsomyndigheten"),
            xaxis_title="% Positiv",
            yaxis=dict(
                gridwidth=0
            ),
            plot_bgcolor='white',
            height=700,
            margin=dict(t=70, l=120)
        )

        fig.write_html('graphs/cases/positive_antibody.html',
                       config=self.plot_config)


def main(template, plot_config, fhm_data):
    """Initiate TestsData class and run methods to prepare cases data.
    Then initiate PlotTests class and run methods to plot graphs.
    """
    tests = TestsData(fhm_data)
    data = tests.return_data()

    tests = PlotTests(data, template, plot_config)
    tests.graph_percentage_cases()
    tests.graph_number_of_tests()
    tests.graph_positive_antibody()
