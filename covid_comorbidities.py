# ======================================================================
# Script to save maps summarising comorbidities data as html files. This
# will be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go

class Comorbidities:
    """Class containing methods to save two graphs as html files:
        - number of people who have died with certain comorbidities
        - the number of comorbidites people have had
    """
    def __init__(self, template, plot_config):
        self.template = template
        self.plot_config = plot_config

    def prepare_data(self):
        """Read data from socialstyrelsen on deaths by age group and
        comorbidities.
        """
        ss_url = ("https://www.socialstyrelsen.se/globalassets/1-globalt/"
                  "covid-19-statistik/avlidna-i-covid-19/"
                  "statistik-covid19-avlidna.xlsx")

        socialstyrelsen = pd.read_excel(
            ss_url,
            sheet_name="Övergripande statistik",
            skiprows=6,
            usecols=[0,1,3,5])

        # Select rows with data on comorbidities
        comorbidities = socialstyrelsen.iloc[[19,20,21,22], :]
        comorbidities.columns = ['Sjukdomsgrupper', 'Totalt', 'Män', 'Kvinnor']

        # Select rows with data on number of comorbidities per patient
        number_comorbidities = socialstyrelsen.iloc[[20,21,22], :]
        number_comorbidities.columns = ['Sjukdomsgrupper', 'Totalt', 'Män',
                                        'Kvinnor']

        self.comorbidities = comorbidities
        self.number_comorbidities = number_comorbidities

    def graph_comorbidities(self):
        """Plot graph showing the number of people with each comorbidity
        and save as an html file.

        File name: comorbidities.html
        """
        df = self.comorbidities

        fig = go.Figure()

        # Män
        fig.add_trace(
            go.Bar(
                y=list(df['Sjukdomsgrupper']),
                x=list(df['Män']),
                orientation='h',
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
                '<b>%{y}</b><br>'+
                '%{x}'
            )
        )

        # Kvinnor
        fig.add_trace(
            go.Bar(
                y=list(df['Sjukdomsgrupper']),
                x=list(df['Kvinnor']),
                orientation='h',
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
                '<b>%{y}</b><br>'+
                '%{x}'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Antal Avlidna i COVID-19 Uppdelat på Sjukdomsgrupper"
                   "</b><br><sub>Källa: Socialstyrelsen"),
            xaxis=dict(
                title="Antal Avlidna",
                separatethousands=True,
                gridwidth=0
            ),
            yaxis=dict(
                autorange='reversed',
                tickmode='array',
                tickvals=df['Sjukdomsgrupper'],
                ticktext=['Hjärt- och<br>kärlsjukdom', 'Högt<br>blodtryck',
                          'Diabetes', 'Lungsjukdom',
                          'Ingen av<br>sjukdomsgrupperna']
            ),
            height=600,
            margin=dict(t=80, l=150)
        )

        fig.write_html('graphs/deaths/comorbidities.html',
                       config=self.plot_config)

    def graph_number_of_comorbidities(self):
        """Plot graph showing the number comorbidities each person had and
        save as an html file.

        File name: number_of_comorbidities.html
        """
        df = self.number_comorbidities

        fig = go.Figure()

        # Män
        fig.add_trace(
            go.Bar(
                y=list(df['Sjukdomsgrupper']),
                x=list(df['Män']),
                orientation='h',
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
                '<b>%{y}</b><br>'+
                '%{x}'
            )
        )

        # Kvinnor
        fig.add_trace(
            go.Bar(
                y=list(df['Sjukdomsgrupper']),
                x=list(df['Kvinnor']),
                orientation='h',
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
                '<b>%{y}</b><br>'+
                '%{x}'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Antal av Sjukdomsgrupper</b><br><sub>Källa: "
                   "Socialstyrelsen"),
            xaxis=dict(
                title="Antal Avlidna",
                separatethousands=True,
                gridwidth=0
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=df['Sjukdomsgrupper'],
                ticktext=['Ingen av<br>sjukdomsgrupperna',
                          'En av <br>sjukdomsgrupperna',
                          '2 eller flera<br>av sjukdomsgrupperna']
            ),
            height=600,
            margin=dict(t=80, l=150)
        )

        fig.write_html('graphs/deaths/number_of_comorbidities.html',
                       config=self.plot_config)


def main(template, plot_config):
    """Initiate Comorbidities class and run methods to plot graphs."""
    comorbid = Comorbidities(template, plot_config)
    comorbid.prepare_data()
    comorbid.graph_comorbidities()
    comorbid.graph_number_of_comorbidities()
