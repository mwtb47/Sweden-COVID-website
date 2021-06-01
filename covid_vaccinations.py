# ======================================================================
# Script to save graphs summarising the vaccination data as html files.
# This will be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go

class VaccinationsData:
    """Class containing methods to prepare data on:
        - percentage of population vaccinated
        - percentage of each age group vaccinated
        - cumulative total vaccinations and total per week
    """
    def __init__(self, counties_pop):
        self.counties_pop = counties_pop

    def download_data(self):
        """Download the excel file containing vaccination data."""
        url = ("https://fohm.maps.arcgis.com/sharing/rest/content/items/"
               "fc749115877443d29c2a49ea9eca77e9/data")

        self.vaccine_data = pd.read_excel(url, sheet_name=None)

    def prepare_vaccine_data(self):
        """Prepare the data for the percentage of population vaccinated
        graph.
        """
        vaccine = self.vaccine_data['Vaccinerade kön']
        vaccine = vaccine[['Kön', 'Antal vaccinerade', 'Andel vaccinerade',
                           'Vaccinationsstatus']]

        # Sweden total population
        sweden_pop = self.counties_pop['population_2019'].sum()

        self.dose_2_percent = vaccine[
            (vaccine['Kön'] == 'Totalt')
            & (vaccine['Vaccinationsstatus'] == 'Färdigvaccinerade')
        ]['Antal vaccinerade'].values[0] / sweden_pop * 100

        self.dose_1_percent = vaccine[
            (vaccine['Kön'] == 'Totalt')
            & (vaccine['Vaccinationsstatus'] == 'Minst 1 dos')
        ]['Antal vaccinerade'].values[0] / sweden_pop * 100

    def prepare_vaccine_age_group_data(self):
        """Prepare the data for the percentage of each age group
        vaccinated graph.
        """
        vaccine_by_age = self.vaccine_data['Vaccinerade ålder']
        vaccine_by_age = vaccine_by_age[
            ['Region', 'Åldersgrupp', 'Antal vaccinerade', 'Andel vaccinerade',
             'Vaccinationsstatus']]
        vaccine_by_age.columns = ['region', 'åldersgrupp', 'antal_vac',
                                  'andel_vac', 'status']

        vaccine_by_age = vaccine_by_age[
            (vaccine_by_age['region'] == '| Sverige |')
            & (vaccine_by_age['åldersgrupp'] != 'Totalt') ]

        vaccine_by_age = vaccine_by_age.replace('90 eller äldre', '90+')

        vaccine_by_age['andel_vac'] = vaccine_by_age['andel_vac'] * 100

        self.vaccine_by_age = vaccine_by_age

    def prepare_vaccine_total_data(self):
        """Prepare the data for the cumulative and weekly total
        vaccinations.
        """
        vaccine_total = self.vaccine_data['Vaccinerade tidsserie']
        vaccine_total = vaccine_total[
            ['Vecka', 'År', 'Region', 'Antal vaccinerade', 'Andel vaccinerade',
             'Vaccinationsstatus']]
        vaccine_total.columns = ['vecka', 'år', 'region', 'antal_vac',
                                 'andel_vac', 'status']

        vaccine_total = vaccine_total.replace('| Sverige |', 'Sverige')
        vaccine_total = vaccine_total[vaccine_total['region'] == 'Sverige']

        vaccine_total['weekly'] = vaccine_total.groupby(
            'status')['antal_vac'].diff()
        vaccine_total.iloc[:2, 6] = vaccine_total.iloc[:2, 3]
        vaccine_total['weekly'] = vaccine_total['weekly'].astype(int)

        vaccine_total['antal_str'] = ["{:,}".format(x)
                                      for x in vaccine_total['antal_vac']]
        vaccine_total['weekly_str'] = ["{:,}".format(x)
                                       for x in vaccine_total['weekly']]

        self.vaccine_total = vaccine_total

    def return_data(self):
        """Return dictionary of Data Frames."""
        self.download_data()
        self.prepare_vaccine_data()
        self.prepare_vaccine_age_group_data()
        self.prepare_vaccine_total_data()

        return {
            'dose_1_percent': self.dose_1_percent,
            'dose_2_percent': self.dose_2_percent,
            'vaccine_by_age': self.vaccine_by_age,
            'vaccine_total': self.vaccine_total,
        }


class PlotVaccinations:
    """Class containing methods to use the prepared data to save two
    graphs and one table as html files:
        - percentage of population vaccinated
        - percentage of each age group vaccinated
        - cumulative total vaccinations and total per week
    """
    def __init__(self, data, template, plot_config):
        self.dose_1_percent = data['dose_1_percent']
        self.dose_2_percent = data['dose_2_percent']
        self.vaccine_by_age = data['vaccine_by_age']
        self.vaccine_total = data['vaccine_total']
        self.template = template
        self.plot_config = plot_config

    def graph_percent_vaccinated(self):
        """Plot graph showing percentage of the population vaccinated
        and save as an html file.

        File name: percent_vaccinated.html
        """
        x = [self.dose_2_percent, self.dose_1_percent]
        y = [100 - self.dose_2_percent, 100 - self.dose_1_percent]

        fig = go.Figure()

        # Percentage of people who have received either 1 or 2 doses
        fig.add_trace(
            go.Bar(
                name="Vaccinarade",
                y=['Färdigvaccinerade', 'Minst 1 dos'],
                x=x,
                marker=dict(color='rgb(40, 40, 140)'),
                orientation='h',
                text=['Färdigvaccinerade', 'Minst 1 dos'],
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
                '%{x:.3f}%'
            )
        )

        # Percentage of people who have not received either 1 or 2 doses
        fig.add_trace(
            go.Bar(
                name="Ej Vaccinerade",
                y=['Färdigvaccinerade', 'Minst 1 dos'],
                x=y,
                marker=dict(color='rgba(140, 140, 140, 0.8)'),
                orientation='h',
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            title=dict(
                text=("<b>Andel av Befolkning Vaccinerade</b>"
                      "<br><sub>Källa: Folkhälsomyndigheten, "
                      "Befolkningsstatistik från SCB"),
                x=0,
                xref='paper',
                y=0.9,
                yref='container',
                yanchor='top'
            ),
            barmode='stack',
            legend_traceorder='normal',
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
            height=200,
            margin=dict(t=80, b=0),
            plot_bgcolor='white'
        )

        fig.write_html('graphs/vaccine/percentage_vaccinated.html',
                       config=self.plot_config)

    def graph_percent_vaccinated_age(self):
        """Plot graph showing percentage of each age group vaccinated
        and save as an html file.

        File name: percent_vaccinated_age.html
        """
        x = [self.dose_2_percent, self.dose_1_percent]
        y = [100 - self.dose_2_percent, 100 - self.dose_1_percent]

        df = self.vaccine_by_age

        fig = go.Figure()

        # Percentage of people who have received either 1 or 2 doses
        fig.add_trace(
            go.Bar(
                x=list(df[
                    df['status'] == 'Minst 1 dos']['åldersgrupp']),
                y=list(df[
                    df['status'] == 'Minst 1 dos']['andel_vac']),
                marker=dict(color='rgb(40, 40, 140)'),
                name="Minst 1 dos",
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='rgb(40, 40, 140)',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x}</b><br>'+
                '%{y:.2f}%'
            )
        )

        # Percentage of people who have received either 1 or 2 doses
        fig.add_trace(
            go.Bar(
                x=list(df[
                    df['status'] == 'Färdigvaccinerade']['åldersgrupp']),
                y=list(df[
                    df['status'] == 'Färdigvaccinerade']['andel_vac']),
                marker=dict(color='skyblue'),
                name="Färdigvaccinerade",
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
                '%{y:.2f}%'
            )
        )

        fig.update_layout(
            title=dict(
                text=("<b>Andel av Befolkning Vaccinerade per Åldersgrupp</b>"
                      "<br><sub>Källa: Folkhälsomyndigheten"),
                x=0,
                xref='paper',
                y=0.9,
                yref='container',
                yanchor='top'
            ),
            barmode='group',
            xaxis=dict(
                title="Åldersgrupp",
                linewidth=2,
                linecolor='black',
            ),
            yaxis=dict(
                title="%",
                linewidth=2,
                linecolor='black',
                gridwidth=1,
                gridcolor='rgb(220, 220, 220)'
            ),
            height=600,
            margin=dict(t=100, l=50),
            plot_bgcolor='white'
        )

        fig.write_html('graphs/vaccine/percentage_vaccinated_age.html',
                       config=self.plot_config)

    def graph_total_vaccinated(self):
        """Plot graph showing time series of the cumulative total number
        of people vaccinated and the weekly number of people vaccinated
        and save as an html file.

        File name: total_vaccinated.html
        """
        df = self.vaccine_total

        fig = go.Figure()

        # Minst 1 dos
        fig.add_trace(
            go.Scatter(
                x=[list(df[df['status'] == 'Minst 1 dos']['år']),
                   list(df[df['status'] == 'Minst 1 dos']['vecka'])],
                y=list(df[df['status'] == 'Minst 1 dos']['antal_vac']),
                marker=dict(color='rgb(40, 40, 140)'),
                name="Minst 1 dos",
                customdata=np.stack((
                    df[df['status'] == 'Minst 1 dos']['vecka'],
                    df[df['status'] == 'Minst 1 dos']['år'],
                    df[df['status'] == 'Minst 1 dos']['antal_str']
                ), axis=-1),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='rgb(40, 40, 140)',
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

        # 2 doser
        fig.add_trace(
            go.Scatter(
                x=[list(df[df['status'] == 'Färdigvaccinerade']['år']),
                   list(df[df['status'] == 'Färdigvaccinerade']['vecka'])],
                y=list(df[df['status'] == 'Färdigvaccinerade']['antal_vac']),
                marker=dict(color='skyblue'),
                name="Färdigvaccinerade",
                customdata=np.stack((
                    df[df['status'] == 'Färdigvaccinerade']['vecka'],
                    df[df['status'] == 'Färdigvaccinerade']['år'],
                    df[df['status'] == 'Färdigvaccinerade']['antal_str']
                ), axis=-1),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='skyblue',
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

        # Minst 1 dos weekly
        fig.add_trace(
            go.Scatter(
                x=[list(df[df['status'] == 'Minst 1 dos']['år']),
                   list(df[df['status'] == 'Minst 1 dos']['vecka'])],
                y=list(df[df['status'] == 'Minst 1 dos']['weekly']),
                marker=dict(color='rgb(40, 40, 140)'),
                name="Minst 1 dos",
                visible=False,
                customdata=np.stack((
                    df[df['status'] == 'Minst 1 dos']['vecka'],
                    df[df['status'] == 'Minst 1 dos']['år'],
                    df[df['status'] == 'Minst 1 dos']['weekly_str']
                ), axis=-1),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='rgb(40, 40, 140)',
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

        # 2 doser weekly
        fig.add_trace(
            go.Scatter(
                x=[list(df[df['status'] == 'Färdigvaccinerade']['år']),
                   list(df[df['status'] == 'Färdigvaccinerade']['vecka'])],
                y=list(df[df['status'] == 'Färdigvaccinerade']['weekly']),
                marker=dict(color='skyblue'),
                name="Färdigvaccinerade",
                visible=False,
                customdata=np.stack((
                    df[df['status'] == 'Färdigvaccinerade']['vecka'],
                    df[df['status'] == 'Färdigvaccinerade']['år'],
                    df[df['status'] == 'Färdigvaccinerade']['weekly_str']
                ), axis=-1),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='skyblue',
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
            title=("<b>Antal av Befolkning Vaccinerade - Totalt</b>"
                   "<br><sub>Källa: Folkhälsomyndigheten"),
            xaxis_title="Vecka",
            height=600,
            margin=dict(t=80),
            updatemenus=[dict(
                direction='down',
                x=1,
                xanchor='right',
                y=1.01,
                yanchor='bottom',
                buttons=list([
                    dict(label="Totalt",
                         method='update',
                         args=[{'visible': [True, True, False, False]},
                                 {'title': ("<b>Antal av Befolkning Vaccinerade"
                                            " - Totalt</b>""<br><sub>"
                                            "Källa: Folkhälsomyndigheten")}]),
                    dict(label="Per Vecka",
                         method='update',
                         args=[{'visible': [False, False, True, True]},
                                 {'title': ("<b>Antal av Befolkning Vaccinerade"
                                            " - per Vecka</b>""<br><sub>"
                                            "Källa: Folkhälsomyndigheten")}]),
                ])
            )]
        )

        fig.write_html('graphs/vaccine/total_vaccinated.html',
                       config=self.plot_config)


def main(template, plot_config, counties_pop):
    """Initiate VaccinationsData class and run methods to prepare cases
    data. Then initiate PlotVaccinations class and run methods to plot
    graphs.
    """
    vaccinations = VaccinationsData(counties_pop)
    data = vaccinations.return_data()

    vaccinations = PlotVaccinations(data, template, plot_config)
    vaccinations.graph_percent_vaccinated()
    vaccinations.graph_percent_vaccinated_age()
    vaccinations.graph_total_vaccinated()
