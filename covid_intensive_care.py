# ======================================================================
# Script to save graphs summarising intensive care data as html files.
# This will be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class IntensiveCareData:
    """Class containing methods to prepare data on:
        - intensive care patients in Sweden
        - intensive care patients per county
    """
    def __init__(self, fhm_data, counties_pop):
        self.fhm_data = fhm_data
        self.counties_pop = counties_pop

    def prepare_data(self):
        """Prepare data on patients receiving intensive care for ploting
        on graphs.
        """
        # Data on intensive ward patients
        hospital = self.fhm_data['Antal intensivvårdade per dag']

        hospital['Datum_vårdstart'] = pd.to_datetime(
            hospital['Datum_vårdstart'],
            format='%Y-%m-%d')

        # 7 day rolling average
        hospital['7_day_rolling'] = hospital['Antal_intensivvårdade'].rolling(
            window=7).mean()

        self.hospital = hospital.dropna()

    def prepare_counties_data(self):
        """Prepare county level data on patients receiving intensive care
        for plotting on graphs.
        """
        # Read regional data
        regions = self.fhm_data['Veckodata Region']

        # Replace county names with desired names
        regions = regions.replace(
            {
                'Jämtland Härjedalen': 'Jämtland',
                'Sörmland': 'Södermanland'
            }
        )

        regions = regions.merge(
            self.counties_pop[['county', 'population_2019']],
            left_on='Region',
            right_on='county',
            how='left')

        regions['Intensivvård_per_10000'] = (
            regions['Antal_intensivvårdade_vecka']
            / regions['population_2019'] * 10000)

        self.regions = regions

    def return_data(self):
        """Run methods to prepare data and return dictionary of Data
        Frames.
        """
        self.prepare_data()
        self.prepare_counties_data()

        return {
            'hospital': self.hospital,
            'regions': self.regions,
        }


class PlotIntensiveCare:
    """Class containing methods to use the prepared data to save two
    graphs and one table as html files:
        - intensive care patients in Sweden
        - subplot of intensive care patients per county
        - single plot of intensive care patients per county
    """
    def __init__(self, data, template, plot_config):
        self.hospital = data['hospital']
        self.regions = data['regions']
        self.template = template
        self.plot_config = plot_config

    def graph_intensive_ward_all(self):
        """Plot graph showing bar chart of daily intensive ward patients
        and line chart of 7 day rolling average and save as an html file.

        File name: intensive_ward_all.html
        """
        df = self.hospital

        fig = go.Figure()

        # 7 day rolling average
        fig.add_trace(
            go.Scatter(
                x=list(df['Datum_vårdstart']),
                y=list(df['7_day_rolling']),
                showlegend=False,
                text=list(df['Antal_intensivvårdade']),
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

        # Bar chart with daily values as reported
        fig.add_trace(
            go.Bar(
                x=list(df['Datum_vårdstart']),
                y=list(df['Antal_intensivvårdade']),
                marker=dict(color='rgba(200, 220, 255, 0.5)'),
                showlegend=False,
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Antal Intensivvårdade per Dag</b>"
                   "<br><sub>7 dagar glidande medelvärde<br>"
                   "Källa: Folkhälsomyndigheten"),
            yaxis_title="Antal Intensivvårdade",
            height=600,
            margin=dict(t=90, b=30)
        )

        fig.write_html('graphs/intensiv/intensive_ward_all.html',
                       config=self.plot_config)

    def graph_intensive_ward_per_county(self):
        """Plot subplots showing the number of patients receiving
        intensive care per county and save as an html file.

        File name: intensive_ward_per_county.html
        """
        df = self.regions
        regions_list = list(df['Region'].unique())

        fig = make_subplots(3, 7,
                            subplot_titles=(regions_list),
                            shared_xaxes=True)

        # Intensive ward per week
        for value, region in enumerate(regions_list, start=7):
            fig.add_trace(
                go.Scatter(
                    x=[list(df['år'][df['Region'] == region]),
                       list(df['veckonummer'][df['Region'] == region])],
                    y=list(df['Antal_intensivvårdade_vecka'][df['Region'] == region]),
                    customdata=np.stack((
                        df['Region'][df['Region'] == region],
                        df['veckonummer'][df['Region'] == region],
                        df['år'][df['Region'] == region],
                    ), axis=-1),
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='gray',
                        font=dict(
                            color='black'
                        )
                    ),
                    hovertemplate=
                    '<extra>%{customdata[0]}</extra>'+
                    '<b>Vecka %{customdata[1]} - %{customdata[2]}</b><br>'+
                    '<b>Antal Intensivvårdade</b>: %{y}',
                    showlegend=False
                ), value//7, value%7+1
            )

        # Intensive ward per week per 10,000
        for value, region in enumerate(regions_list, start=7):
            fig.add_trace(
                go.Scatter(
                    x=[list(df['år'][df['Region'] == region]),
                       list(df['veckonummer'][df['Region'] == region])],
                    y=list(df['Intensivvård_per_10000'][df['Region'] == region]),
                    customdata=np.stack((
                        df['Region'][df['Region'] == region],
                        df['veckonummer'][df['Region'] == region],
                        df['år'][df['Region'] == region],
                    ), axis=-1),
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='gray',
                        font=dict(
                            color='black'
                        )
                    ),
                    hovertemplate=
                    '<extra>%{customdata[0]}</extra>'+
                    '<b>Vecka %{customdata[1]} - %{customdata[2]}</b><br>'+
                    '<b>Antal Intensivvårdade</b>: %{y:.3f}',
                    showlegend=False,
                    visible=False
                ), value//7, value%7+1
            )


        fig.update_xaxes(
            showdividers=False,
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
                text=("<b>Antal Intensivvådade per Dag per Län</b><br>"
                      "<sub>Källa: Folkhälsomyndigheten"),
                x=0,
                xref='paper',
                y=0.96,
                yref='container',
                yanchor='top'
            ),
            plot_bgcolor='white',
            height=800,
            margin=dict(b=80),
            updatemenus=[
                dict(
                    direction='down',
                    x=1,
                    xanchor='right',
                    y=1.05,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="Antal Intensivvådade",
                            method='update',
                            args=[{'visible': [True]*21 + [False]*21},
                                  {'title': ("<b>Antal Intensivvådade per Dag "
                                             "per Län</b><br><sub>Källa: "
                                             "Folkhälsomyndigheten")}]),
                        dict(label="Antal per 10 000",
                            method='update',
                            args=[{'visible': [False]*21 + [True]*21},
                                  {'title': ("<b>Antal Intensivvådade per Dag "
                                             "per Län (per 10 000)</b><br>"
                                             "<sub>Källa: "
                                             "Folkhälsomyndigheten")}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/intensiv/intensive_ward_per_county.html',
                       config=self.plot_config)


    def graph_intensive_ward_per_county_single(self):
        """Plot graph showing the number of patients receiving intensive
        care per county and save as an html file.

        File name: intensive_ward_per_county_single.html
        """
        df = self.regions
        regions_list = list(df['Region'].unique())

        fig = go.Figure()

        # Intensive ward per week
        for region in regions_list:
            fig.add_trace(
                go.Scatter(
                    x=[list(df['år'][df['Region'] == region]),
                       list(df['veckonummer'][df['Region'] == region])],
                    y=list(df['Antal_intensivvårdade_vecka'][df['Region'] == region]),
                    name=region,
                    customdata=np.stack((
                        df['veckonummer'][df['Region'] == region],
                        df['år'][df['Region'] == region],
                    ), axis=-1),
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='gray',
                        font=dict(
                            color='black'
                        )
                    ),
                    hovertemplate=
                    '<b>Vecka %{customdata[0]} - %{customdata[1]}</b><br>'+
                    '<b>Antal Intensivvårdade</b>: %{y}'
                )
            )

        # Intensive ward per week per 10,000
        for region in regions_list:
            fig.add_trace(
                go.Scatter(
                    x=[list(df['år'][df['Region'] == region]),
                       list(df['veckonummer'][df['Region'] == region])],
                    y=list(df['Intensivvård_per_10000'][df['Region'] == region]),
                    name=region,
                    visible=False,
                    customdata=np.stack((
                        df['veckonummer'][df['Region'] == region],
                        df['år'][df['Region'] == region],
                    ), axis=-1),
                    hoverlabel=dict(
                        bgcolor='white',
                        bordercolor='gray',
                        font=dict(
                            color='black'
                        )
                    ),
                    hovertemplate=
                    '<b>Vecka %{customdata[0]} - %{customdata[1]}</b><br>'+
                    '<b>Antal Intensivvårdade</b>: %{y:.3f}'
                )
            )

        fig.update_layout(
            template=self.template,
            title=("<b>Antal Intensivvådade per Dag per Län</b><br>"
                   "<sub>Källa: Folkhälsomyndigheten"),
            xaxis_title="Vecka",
            height=700,
            margin=dict(t=80),
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
                                  {'title': ("<b>Antal Intensivvådade per Dag "
                                             "per Län</b><br><sub>Källa: "
                                             "Folkhälsomyndigheten")}]),
                        dict(label="Antal per 10 000",
                            method='update',
                            args=[{'visible': [False]*21 + [True]*21},
                                  {'title': ("<b>Antal Intensivvådade per Dag "
                                             "per Län (per  10 000)</b><br>"
                                             "<sub>Källa: "
                                             "Folkhälsomyndigheten")}]),
                    ])
                )
            ]
        )

        fig.write_html(
            'graphs/intensiv/intensive_ward_per_county_single.html',
            config=self.plot_config)


def main(template, plot_config, fhm_data, counties_pop):
    """Initiate IntensiveCareData class and run methods to prepare cases
    data. Then initiate PlotIntensiveCare class and run methods to plot
    graphs.
    """
    intensive = IntensiveCareData(fhm_data, counties_pop)
    data = intensive.return_data()

    intensive = PlotIntensiveCare(data, template, plot_config)
    intensive.graph_intensive_ward_all()
    intensive.graph_intensive_ward_per_county()
    intensive.graph_intensive_ward_per_county_single()
