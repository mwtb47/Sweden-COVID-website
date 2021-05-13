# ======================================================================
# Script to save maps summarising case and deaths data as html files.
# This will be imported as a module into main.py.
# ======================================================================

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go


class Maps:
    """Class containing methods to save four maps as html files:
        - cases per county
        - cases per 10,000 people per county
        - deaths per county
        - deaths per 10,000 people per county
    """
    def __init__(self, plot_config, fhm_data, counties_pop,
                 mapbox_access_token):
        self.plot_config = plot_config
        self.fhm_data = fhm_data
        self.counties_pop = counties_pop
        self.mapbox_access_token = mapbox_access_token

    def get_data(self):
        """Read in data on cases and deaths by county and read geojson
        file with boundaries for Sweden's counties.
        """
        county_data = self.fhm_data['Totalt antal per region']

        # Replace region names desired names
        county_data = county_data.replace(
            {
                'Jämtland Härjedalen': 'Jämtland',
                'Sörmland': 'Södermanland'
            }
        )
        self.county_data = county_data

        # geojson data for Swedish county boundaries
        with open('data/geojson/sweden-counties.geojson') as file:
            self.counties_json = json.load(file)

    def map_Sweden_map_cases(self):
        """Create map showing number of cases per county in Sweden and
        save as an html file.

        File name: Sweden_map_cases.html
        """
        # Create plot of total number of deaths per county
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=self.counties_json,
                featureidkey='properties.name',
                locations=self.county_data['Region'],
                z=self.county_data['Totalt_antal_fall'],
                colorscale=[
                    [0, 'rgb(255, 240, 240)'],
                    [0.2, 'rgb(180, 110, 110)'],
                    [0.7, 'rgb(140, 70, 70)'],
                    [1, 'rgb(120, 50, 50)']
                ],
                showscale=False,
                text=self.county_data['Region'],
                hovertemplate =
                '<extra></extra>' +
                '<b>%{text}</b><br>' +
                '%{z}'
            )
        )

        fig.update_layout(
            title="<b>Bekräftade Fall</b><br><sub>Källa: Folkhälsomyndigheten",
            hovermode ='closest',
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
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
                l=50, r=50, b=50, t=90, pad=4
            )
        )

        fig.write_html('maps/Sweden_map_cases.html', config=self.plot_config)

    def map_Sweden_map_cases_10000(self):
        """Create map showing number of cases per 10,000 inhabitants
        per county in Sweden and save as an html file.

        File name: Sweden_map_cases_10000.html
        """
        # Merge county populations
        self.county_data = self.county_data.merge(
            self.counties_pop[['county', 'population_2019']],
            left_on='Region',
            right_on='county',
            how='left')

        self.county_data['cases_per_10000'] = (round(
            self.county_data['Totalt_antal_fall'] /
            self.county_data['population_2019'] * 1000, 3))

        # Create plot of total number of deaths per 1000 per county
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=self.counties_json,
                featureidkey='properties.name',
                locations=self.county_data['Region'],
                z=self.county_data['cases_per_10000'],
                colorscale=[
                    [0, 'rgb(255, 240, 240)'],
                    [0.2, 'rgb(180, 110, 110)'],
                    [0.7, 'rgb(140, 70, 70)'],
                    [1, 'rgb(120, 50, 50)']
                ],
                showscale=False,
                text=self.county_data['Region'],
                hovertemplate =
                '<extra></extra>' +
                '<b>%{text}</b><br>' +
                '%{z}'
            )
        )

        fig.update_layout(
            title=("<b>Bekräftade Fall per 10,000</b><br>"
                   "<sub>Källa: Folkhälsomyndigheten"),
            hovermode ='closest',
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
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
                l=50, r=50, b=50, t=90, pad=4
            )
        )

        fig.write_html('maps/Sweden_maps_cases_10000.html',
                       config=self.plot_config)


    def map_Sweden_map_deaths(self):
        """Create map showing number of deaths per county in Sweden and
        save as an html file.

        File name: Sweden_map_deaths.html
        """
        # Create plot of total number of deaths per county
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=self.counties_json,
                featureidkey='properties.name',
                locations=self.county_data['Region'],
                z=self.county_data['Totalt_antal_avlidna'],
                colorscale=[
                    [0, 'rgb(255, 240, 240)'],
                    [0.2, 'rgb(180, 110, 110)'],
                    [0.7, 'rgb(140, 70, 70)'],
                    [1, 'rgb(120, 50, 50)']
                ],
                showscale=False,
                text=self.county_data['Region'],
                hovertemplate =
                '<extra></extra>' +
                '<b>%{text}</b><br>' +
                '%{z}'
            )
        )

        fig.update_layout(
            title="<b>Antal Avlidna</b><br><sub>Källa: Folkhälsomyndigheten",
            hovermode ='closest',
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
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
                l=50, r=50, b=50, t=90, pad=4
            ),
        )

        fig.write_html('maps/Sweden_map_deaths.html', config=self.plot_config)

    def map_Sweden_map_deaths_10000(self):
        """Create map showing number of deaths per 10,000 inhabitants
        per county in Sweden and save as an html file.

        File name: Sweden_map_deaths_10000.html
        """
        self.county_data['deaths_per_10000'] = (
            round(self.county_data['Totalt_antal_avlidna']
                  / self.county_data['population_2019'] * 1000, 3))

        # Create plot of total number of deaths per 10,000 per county
        fig = go.Figure(
            go.Choroplethmapbox(
                geojson=self.counties_json,
                featureidkey='properties.name',
                locations=self.county_data['Region'],
                z=self.county_data['deaths_per_10000'],
                colorscale=[
                    [0, 'rgb(255, 240, 240)'],
                    [0.2, 'rgb(180, 110, 110)'],
                    [0.7, 'rgb(140, 70, 70)'],
                    [1, 'rgb(120, 50, 50)']
                ],
                showscale=False,
                text=self.county_data['Region'],
                hovertemplate =
                '<extra></extra>' +
                '<b>%{text}</b><br>' +
                '%{z}'
            )
        )

        fig.update_layout(
            title=("<b>Antal Avlidna per 10,000</b>"
                   "<br><sub>Källa: Folkhälsomyndigheten"),
            hovermode ='closest',
            mapbox=dict(
                accesstoken=self.mapbox_access_token,
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
                l=50, r=50, b=50, t=90, pad=4
            )
        )

        fig.write_html('maps/Sweden_maps_deaths_10000.html',
                       config=self.plot_config)


def main(plot_config, fhm_data, counties_pop, mapbox_access_token):
    """Initiate Maps class and run methods to plot maps."""
    maps = Maps(plot_config, fhm_data, counties_pop, mapbox_access_token)
    maps.get_data()
    maps.map_Sweden_map_cases()
    maps.map_Sweden_map_cases_10000()
    maps.map_Sweden_map_deaths()
    maps.map_Sweden_map_deaths_10000()
