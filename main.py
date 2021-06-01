# ======================================================================
# Creates plots summarising data on cases, deaths, hospitalisations and
# vaccinations using data from Folkhälsomyndigheten, Socialstyrelsen and
# Statistiska centralbyrån.
# ======================================================================

import pandas as pd
import plotly.graph_objects as go

import config
import covid_cases
import covid_comorbidities
import covid_deaths
import covid_intensive_care
import covid_maps
import covid_tests
import covid_vaccinations


mapbox_access_token = config.mapbox_key

# Graph template
template=dict(
    layout=go.Layout(
        title=dict(
            x=0,
            xref='paper',
            y=0.96,
            yref='container',
            yanchor='top'
        ),
        xaxis=dict(
            showline=True,
            linewidth=1.5,
            linecolor='black',
            gridwidth=1,
            gridcolor='whitesmoke'
        ),
        yaxis=dict(
            showline=True,
            linewidth=1.5,
            linecolor='black',
            gridwidth=1,
            gridcolor='whitesmoke'
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='closest'
    )
)

# Configuration of the mode bar buttons for the Plotly plots.
plot_config={
    'modeBarButtonsToRemove': [
        'toggleSpikelines', 'hoverClosestCartesian', 'hoverCompareCartesian',
        'lasso2d', 'toggleSpikelines', 'autoScale2d', 'zoom2d'
    ]
}

# Populations of Swedish counties
counties_population = pd.read_csv(
    'data/sweden_counties.csv',
    dtype={
        'county_code':str,
        'county':str,
        'population_2019':int
    })

# Folkhälsomyndigheten data
fhm_url = ("https://www.arcgis.com/sharing/rest/content/items/"
           "b5e7488e117749c19881cce45db13f7e/data")
fhm_data = pd.read_excel(fhm_url, sheet_name=None)

# Dictionary of modules where the value for each dictionary item is a
# list. The first item of the list is the name of the method's main
# function. The second is a list containing the arguments for the main
# function.
modules_dict = {
    'cases': [covid_cases.main,
              [template, plot_config, fhm_data, counties_population]],
    'comorbidities': [covid_comorbidities.main, [template, plot_config]],
    'deaths': [covid_deaths.main,
               [template, plot_config, fhm_data, counties_population]],
    'intensive_care': [covid_intensive_care.main,
                       [template, plot_config, fhm_data, counties_population]],
    'maps': [covid_maps.main,
             [plot_config, fhm_data, counties_population,
              mapbox_access_token]],
    'tests': [covid_tests.main, [template, plot_config, fhm_data]],
    'vaccinations': [covid_vaccinations.main,
                     [template, plot_config, counties_population]],
}


def main():
    """Ask which modules to run and then run them."""
    print("Choose from: [all, cases, comorbidities, deaths, intensive_care")
    print("              maps, tests, vaccinations]")
    modules = input("              ")

    if modules == 'all':
        for m in modules_dict:
            modules_dict[m][0](*modules_dict[m][1])
    else:
        for m in modules.split(', '):
            modules_dict[m][0](*modules_dict[m][1])


if __name__ == "__main__":
    main()
