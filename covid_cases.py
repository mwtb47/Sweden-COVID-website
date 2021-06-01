# ======================================================================
# Script to save graphs summarising the cases data as html files. This
# will be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class CasesData:
    """Class containing methods to prepare data on:
        - daily cases in Sweden
        - daily cases per county
    """
    def __init__(self, fhm_data, counties_pop):
        self.fhm_data = fhm_data
        self.counties_pop = counties_pop

    def prepare_cases_data(self):
        """Prepare cases data to be used in graphs."""
        daily_cases = self.fhm_data['Antal per dag region']

        daily_cases['Statistikdatum'] = pd.to_datetime(
            daily_cases['Statistikdatum'],
            format='%Y-%m-%d')

        # Melt columns for each county into a single column
        daily_cases = daily_cases.melt(
            id_vars='Statistikdatum',
            var_name='county',
            value_name='cases')

        daily_cases = daily_cases[~daily_cases['Statistikdatum'].isnull()]

        # Group data frame by county and create new column with 7 day
        # rolling average.
        group = daily_cases.groupby('county')['cases']
        daily_cases['cases_7_day'] = group.apply(
            lambda x: x.rolling(window=7).mean())

        # Replace region names with desired names
        daily_cases = daily_cases.replace(
            {
                'Jämtland_Härjedalen': "Jämtland",
                'Västra_Götaland': "Västra Götaland",
                "Sörmland": "Södermanland"
            }
        )

        # Merge population data and add total population
        daily_cases = daily_cases.merge(
            self.counties_pop,
            on='county',
            how='left')

        # Total population
        total_pop = self.counties_pop['population_2019'].sum()
        daily_cases.loc[daily_cases['county'] == 'Totalt_antal_fall',
                        'population_2019'] = total_pop

        # Create columns with cases and 7 day rolling averages per 10,000
        # inhabitants.
        daily_cases['cases_per_10000'] = (
            daily_cases['cases'] / daily_cases['population_2019'] * 10000)
        daily_cases['cases_7_day_per_10000'] = (
            daily_cases['cases_7_day'] /
            daily_cases['population_2019'] * 10000)

        # Thousand comma separator to be used in graph labels
        daily_cases['cases_str'] = [
            "{:,}".format(int(x)) for x in daily_cases['cases']]
        daily_cases['cases_7_day_str'] = [
            "{:,}".format(round(x, 2)) for x in daily_cases['cases_7_day']]
        daily_cases['cases_7_day_per_10000_str'] = [
            "{:,}".format(round(x, 2))
            for x in daily_cases['cases_7_day_per_10000']]

        return daily_cases


class PlotCases:
    """Class containing methods to use the prepared data to save two
    graphs and one table as html files:
        - daily cases in Sweden
        - subplot of daily cases per county
        - single plot of daily cases per county
    """
    def __init__(self, daily_cases, template, plot_config):
        self.daily_cases = daily_cases
        self.template = template
        self.plot_config = plot_config

    def graph_daily_cases_all(self):
        """Plot graph showing daily cases for all of Sweden and save as
        an html file.

        File name: daily_cases_all.html
        """
        df = self.daily_cases[
            (self.daily_cases['Statistikdatum'] >= '2020-02-10')
            & (self.daily_cases['county'] == 'Totalt_antal_fall')
        ]

        fig = go.Figure()

        # Daily cases - 7 day rolling average
        fig.add_trace(
            go.Scatter(
                x=list(df['Statistikdatum']),
                y=list(df['cases_7_day']),
                showlegend=False,
                customdata=np.stack((
                    df['cases_7_day_str'],
                    df['cases_str']
                ), axis=-1),
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
                '<b>Medelvärde</b>: %{customdata[0]}<br>'+
                '<b>Daglig</b>: %{customdata[1]}'
            )
        )

        # Daily cases - bar chart of daily cases as they are reported
        fig.add_trace(
            go.Bar(
                x=list(df['Statistikdatum']),
                y=list(df['cases']),
                marker=dict(color='rgba(200, 220, 255, 0.5)'),
                showlegend=False,
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Bekräftade Fall per Dag</b>"
                   "<br><sub>7 dagar glidande medelvärde"
                   "<br>Källa: Folkhälsomyndigheten"),
            yaxis_title="Antal Fall",
            height=600,
            margin=dict(t=100, b=30)
        )

        fig.write_html('graphs/cases/daily_cases_all.html',
                       config=self.plot_config)


    def graph_daily_cases_per_county(self):
        """Plot subplots showing daily cases per county and save as an
        html file.

        File name: daily_cases_per_county.html
        """
        df = self.daily_cases[self.daily_cases['Statistikdatum'] >= '2020-02-10']

        regions = list(self.daily_cases['county'].unique())
        regions.remove('Totalt_antal_fall')

        fig = make_subplots(7, 3, subplot_titles=(regions), shared_xaxes=True)

        # Cases
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['Statistikdatum'][df['county'] == region]),
                    y=list(df['cases_7_day'][df['county'] == region]),
                    showlegend=False,
                    text=df['cases_7_day_str'],
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
                    '%{text}'
                ),
                row=value//3, col=value%3+1
            )

        # Cases per 10,000
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['Statistikdatum'][df['county'] == region]),
                    y=list(df['cases_7_day_per_10000'][df['county'] == region]),
                    visible=False,
                    showlegend=False,
                    text=df['cases_7_day_per_10000_str'],
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
                    '%{text}'
                ),
                row=value//3, col=value%3+1
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
            title=dict(
                text=("<b>Bekräftade Fall per Dag per Län</b>"
                      "<br><sub>7 dagar glidande medelvärde"
                      "<br>Källa: Folkhälsomyndigheten"),
                x=0,
                xref='paper',
                y=0.96,
                yref='container',
                yanchor='top'
            ),
            margin=dict(t=120, b=60),
            height=800,
            plot_bgcolor='white',
            updatemenus=[
                dict(
                    direction='down',
                    x=1,
                    xanchor='right',
                    y=1.07,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="Antal Fall",
                             method='update',
                             args=[{'visible': [True]*21 + [False]*21},
                                   {'title': ("<b>Bekräftade Fall per Dag per "
                                              "Län</b><br><sub>7 dagar "
                                              "glidande medelvärde<br>Källa: "
                                              "Folkhälsomyndigheten")}]),
                        dict(label="Antal Fall per 10 000",
                             method='update',
                             args=[{'visible': [False]*21 + [True]*21},
                                   {'title': ("<b>Bekräftade Fall per Dag per "
                                              "Län (per 10 000)</b><br><sub>7 "
                                              "dagar glidande medelvärde<br>"
                                              "Källa: Folkhälsomyndigheten")}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/cases/daily_cases_per_county.html',
                       config=self.plot_config)


    def graph_daily_cases_per_county_single(self):
        """Plot graph showing daily cases for each county and save as an
        html file.

        File name: daily_cases_per_county_single.html
        """
        df = self.daily_cases[self.daily_cases['Statistikdatum'] >= '2020-02-10']

        regions = list(self.daily_cases['county'].unique())
        regions.remove('Totalt_antal_fall')

        fig = go.Figure()

        # Cases
        for region in regions:
            fig.add_trace(
                go.Scatter(
                    x=list(df['Statistikdatum'][df['county'] == region]),
                    y=list(df['cases_7_day'][df['county'] == region]),
                    name=region,
                    text=df['cases_7_day_str'],
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='gray',
                        font=dict(
                            color='black'
                        )
                    ),
                    hovertemplate=
                    '<b>%{x}</b><br>'+
                    '%{text}'
                )
            )

        # Cases per 10,000
        for region in regions:
            fig.add_trace(
                go.Scatter(
                    x=list(df['Statistikdatum'][df['county'] == region]),
                    y=list(df['cases_7_day_per_10000'][df['county'] == region]),
                    name=region,
                    visible=False,
                    text=df['cases_7_day_per_10000_str'],
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='gray',
                        font=dict(
                            color='black'
                        )
                    ),
                    hovertemplate=
                    '<b>%{x}</b><br>'+
                    '%{text}'
                )
            )

        fig.update_layout(
            template=self.template,
            title=("<b>Bekräftade Fall per Dag per Län</b>"
                   "<br><sub>7 dagar glidande medelvärde"
                   "<br>Källa: Folkhälsomyndigheten"),
            yaxis_separatethousands=True,
            height=600,
            margin=dict(t=90, b=30),
            updatemenus=[
                dict(
                    direction='down',
                    x=1,
                    xanchor='right',
                    y=1.01,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="Antal Fall",
                             method='update',
                             args=[{'visible': [True]*21 + [False]*21},
                                   {'title': ("<b>Bekräftade Fall per Dag per "
                                              "Län</b><br><sub>7 dagar "
                                              "glidande medelvärde<br>Källa: "
                                              "Folkhälsomyndigheten")}]),
                        dict(label="Antal Fall per 10 000",
                             method='update',
                             args=[{'visible': [False]*21 + [True]*21},
                                   {'title': ("<b>Bekräftade Fall per Dag per "
                                              "Län (per 10 000)</b><br><sub>7 "
                                              "dagar glidande medelvärde<br>"
                                              "Källa: Folkhälsomyndigheten")}]),
                            ]
                    )
            )]
        )

        fig.write_html('graphs/cases/daily_cases_per_county_single.html',
                       config=self.plot_config)


def main(template, plot_config, fhm_data, counties_pop):
    """Initiate CasesData class and run methods to prepare cases data.
    Then initiate PlotCases class and run methods to plot graphs.
    """
    cases = CasesData(fhm_data, counties_pop)
    daily_cases = cases.prepare_cases_data()

    cases = PlotCases(daily_cases, template, plot_config)
    cases.graph_daily_cases_all()
    cases.graph_daily_cases_per_county()
    cases.graph_daily_cases_per_county_single()
