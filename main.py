from dash import Dash, html, dcc, Input, Output
from datetime import datetime, timedelta

import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# ================== Importing the Dataset ================== #
cases_death_df = pd.read_csv(
    'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/jhu/full_data.csv')
vaccinations_df = pd.read_csv(
    'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv')
locations_df = pd.read_csv(
    'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/jhu/locations.csv')

cases_deaths_vaccinations_df = cases_death_df.merge(vaccinations_df, how='outer', on=[
                                                    'location', 'date']).merge(locations_df, how='left', on='location')


cases_deaths_vaccinations_df['date'] = pd.to_datetime(
    cases_deaths_vaccinations_df['date'])

income_stream = ['High income', 'Upper middle income', 'Lower middle income']
regions = ['Europe', 'Asia', 'North America', 'South America', 'Africa']
organizations = ['World', 'European Union', 'Oceania']

country_filter = cases_deaths_vaccinations_df['Country/Region'] == cases_deaths_vaccinations_df['Country/Region']
countries_only_df = cases_deaths_vaccinations_df[country_filter]
countries_only_df['month'] = countries_only_df['date'].dt.month
countries_only_df['year'] = countries_only_df['date'].dt.year

app.layout = html.Div([
    html.Div(children=[
        html.H2('Global Status', style={
                'font-weight': 'bold', 'color': '#c19b7a'}),
        html.Div(children=[
            html.Div(children=[
                html.P('Column'),
                dcc.Dropdown(['total_cases', 'total_deaths', 'new_cases', 'new_deaths',
                            'people_vaccinated', 'people_fully_vaccinated'], value='total_cases', id='column-dropdown', clearable=False, style={'width': '500px'})
            ]),
            html.Div(style={'flex': '1'}),
            html.Div(children=[
                html.P('Timeframe'),
                dcc.Dropdown(['All Time', 'Past Year', 'Past Month', 'Past Week'], value='All Time', id='timeframe-dropdown', clearable=False, style={'width': '500px'})
            ]),
        ], style={'display': 'flex', 'align-items': 'space-between', 'text-align': 'left'}),
        html.Div(children=[
            dcc.Graph(id='top-10-bar', style={'flex': '1'}),
            dcc.Graph(id='choropleth-map', style={'flex': '1'}),
        ], style={'display': 'flex'})
    ], style={'text-align': 'center'}),
    html.Hr(),
    html.Div(children=[
        html.H2('Per Country', style={
                'font-weight': 'bold', 'color': '#c19b7a'}),
        html.Div(children=[
            html.Div(children=[
                html.P('Country'),
                dcc.Dropdown(countries_only_df['Country/Region'].unique(), value=countries_only_df['Country/Region'].unique()[
                    0], id='country-dropdown', clearable=False, style={'width': '500px'})
            ]),
            html.Div(style={'flex': '1'}),
            html.Div(children=[
                html.P('From/To'),
                dcc.DatePickerRange(countries_only_df['date'].min(),
                                    countries_only_df['date'].max(),
                                    min_date_allowed=countries_only_df['date'].min(),
                                    max_date_allowed=countries_only_df['date'].max(),
                                    id='from-to-dropdown'
                )
            ]),
        ], style={'display': 'flex', 'align-items': 'space-between', 'text-align': 'left'}),
        html.Div(children=[
            dcc.Graph(id='line-chart', style={'flex': '1'}),
            dcc.Graph(id='pie-chart', style={'flex': '1'}),
        ], style={'display': 'flex'})
    ], style={'text-align': 'center'}),
], style={'margin': '25px'})


@app.callback(
    Output(component_id='top-10-bar', component_property='figure'),
    Input(component_id='column-dropdown', component_property='value'),
    Input(component_id='timeframe-dropdown', component_property='value')
)
def update_bar_chart(column_value, timeframe_value):
    # ================== Top 10 Countries - Bar Chart ================== #
    if(timeframe_value == 'Past Year'):
        date_filter = datetime.now() - timedelta(days=365)
    elif(timeframe_value == 'Past Month'):
        date_filter = datetime.now() - timedelta(days=30)
    elif(timeframe_value == 'Past Week'):
        date_filter = datetime.now() - timedelta(days=7)
    else:
        date_filter = countries_only_df['date'].min()
        
    filtered_df = countries_only_df[countries_only_df['date'] >= date_filter].groupby('Country/Region').agg(
        {'total_cases': ['max', 'min'], 'total_deaths': ['max', 'min'],  'new_cases': 'mean', 'new_deaths': 'mean', 'people_vaccinated': ['max', 'min'], 'people_fully_vaccinated': ['max', 'min'], 'continent': 'max'}).reset_index()
    
    total_cases = (filtered_df['total_cases']['max'] - filtered_df['total_cases']['min'])
    del filtered_df['total_cases']
    filtered_df['total_cases'] = total_cases

    total_deaths = (filtered_df['total_deaths']['max'] - filtered_df['total_deaths']['min'])
    del filtered_df['total_deaths']
    filtered_df['total_deaths'] = total_deaths

    people_vaccinated = (filtered_df['people_vaccinated']['max'] - filtered_df['people_vaccinated']['min'])
    del filtered_df['people_vaccinated']
    filtered_df['people_vaccinated'] = people_vaccinated

    people_fully_vaccinated = (filtered_df['people_fully_vaccinated']['max'] - filtered_df['people_fully_vaccinated']['min'])
    del filtered_df['people_fully_vaccinated']
    filtered_df['people_fully_vaccinated'] = people_fully_vaccinated

    fig = px.bar(filtered_df.sort_values(column_value, ascending=False).head(
        10), x='Country/Region', y=column_value, color=column_value, color_continuous_scale='orrd')
    fig.update_layout(title='Top 10 Countries with Most COVID-19 %s' % (column_value.replace('_', ' ').title()),
                      title_x=0.5, title_font=dict(size=18, color='Darkred'))
    return fig


@app.callback(
    Output(component_id='choropleth-map', component_property='figure'),
    Input(component_id='column-dropdown', component_property='value'),
    Input(component_id='timeframe-dropdown', component_property='value')
)
def update_choropleth_map(column_value, timeframe_value):
    # ================== Choropleth Map ================== #
    if(timeframe_value == 'Past Year'):
        date_filter = datetime.now() - timedelta(days=365)
    elif(timeframe_value == 'Past Month'):
        date_filter = datetime.now() - timedelta(days=30)
    elif(timeframe_value == 'Past Week'):
        date_filter = datetime.now() - timedelta(days=7)
    else:
        date_filter = countries_only_df['date'].min()
        
    filtered_df = countries_only_df[countries_only_df['date'] >= date_filter].groupby('Country/Region').agg(
        {'total_cases': ['max', 'min'], 'total_deaths': ['max', 'min'],  'new_cases': 'mean', 'new_deaths': 'mean', 'people_vaccinated': ['max', 'min'], 'people_fully_vaccinated': ['max', 'min'], 'continent': 'max'}).reset_index()
    
    total_cases = (filtered_df['total_cases']['max'] - filtered_df['total_cases']['min'])
    del filtered_df['total_cases']
    filtered_df['total_cases'] = total_cases

    total_deaths = (filtered_df['total_deaths']['max'] - filtered_df['total_deaths']['min'])
    del filtered_df['total_deaths']
    filtered_df['total_deaths'] = total_deaths

    people_vaccinated = (filtered_df['people_vaccinated']['max'] - filtered_df['people_vaccinated']['min'])
    del filtered_df['people_vaccinated']
    filtered_df['people_vaccinated'] = people_vaccinated

    people_fully_vaccinated = (filtered_df['people_fully_vaccinated']['max'] - filtered_df['people_fully_vaccinated']['min'])
    del filtered_df['people_fully_vaccinated']
    filtered_df['people_fully_vaccinated'] = people_fully_vaccinated
    
    fig = px.choropleth(filtered_df,
                        locations='Country/Region',
                        locationmode='country names',
                        color=column_value,
                        hover_name='Country/Region',
                        color_continuous_scale='orrd')

    fig.update_layout(title='COVID-19 %s' % (column_value.replace('_', ' ').title()),
                      title_x=0.5,
                      title_font=dict(size=18, color='Darkred'),
                      geo=dict(showframe=False,
                               showcoastlines=False,
                               projection_type='equirectangular'))

    return fig

@app.callback(
    Output(component_id='line-chart', component_property='figure'),
    Input(component_id='country-dropdown', component_property='value'),
    Input(component_id='from-to-dropdown', component_property='start_date'),
    Input(component_id='from-to-dropdown', component_property='end_date')
)
def update_line_chart(country_value, start_date, end_date):
    # ================== Line Chart ================== #
    grouped_by_year_month_loc = countries_only_df[(countries_only_df['date'] >= start_date) & (countries_only_df['date'] <= end_date)].groupby(['year', 'month', 'location'])[
        ['new_cases', 'new_deaths', 'daily_vaccinations']].mean().reset_index()
    grouped_by_year_month_loc['month-year'] = grouped_by_year_month_loc.apply(
        lambda x: '%d-%d' % (x['month'], x['year']), axis=1)
    tidy = grouped_by_year_month_loc[grouped_by_year_month_loc['location'] == country_value].melt(
        id_vars=['month-year', 'location'])

    fig = px.line(tidy[(tidy['variable'] != 'year') & (tidy['variable'] != 'month')],
                  x='month-year',
                  y='value',
                  color='variable',
                  log_y=True,
                  markers=True,
                  color_discrete_map={
                      "new_cases": "#fc8d59", "new_deaths": "#da3825", "daily_vaccinations": "#7f0000"}
                  )
    
    fig.update_layout(title='Trend of New Cases, Deaths, and Vaccinations', title_x=0.5, title_font=dict(size=18, color='Darkred'))

    return fig


@app.callback(
    Output(component_id='pie-chart', component_property='figure'),
    Input(component_id='country-dropdown', component_property='value'),
    Input(component_id='from-to-dropdown', component_property='start_date'),
    Input(component_id='from-to-dropdown', component_property='end_date')
)
def update_pie_chart(country_value, start_date, end_date):
    # ================== Pie Chart ================== #
    grouped_by_country = countries_only_df[(countries_only_df['date'] >= start_date) & (countries_only_df['date'] <= end_date)].groupby('location')[
        ['people_vaccinated_per_hundred', 'people_fully_vaccinated_per_hundred', 'population']].max().reset_index()

    grouped_by_country['partially_vaccinated'] = (
        grouped_by_country['population'] / 100) * grouped_by_country['people_vaccinated_per_hundred']
    grouped_by_country['fully_vaccinated'] = (
        grouped_by_country['population'] / 100) * grouped_by_country['people_fully_vaccinated_per_hundred']
    grouped_by_country.head()

    labels = ['Fully Vaccinated', 'Partially Vaccinated', 'Unvaccinated']
    values = [
        float(grouped_by_country[grouped_by_country['location']
              == country_value]['partially_vaccinated']),
        float(grouped_by_country[grouped_by_country['location'] == country_value]['partially_vaccinated'] -
              grouped_by_country[grouped_by_country['location'] == country_value]['fully_vaccinated']),
        float(grouped_by_country[grouped_by_country['location'] == country_value]['population'] -
              grouped_by_country[grouped_by_country['location'] == country_value]['partially_vaccinated'])
    ]

    temp_df = pd.DataFrame({'labels': labels, 'values': values})

    fig = px.pie(
        temp_df,
        names='labels',
        values='values',
        color='labels',
        color_discrete_map={'Unvaccinated': '#7f0000',
                            'Partially Vaccinated': '#fc8d59', 'Fully Vaccinated': '#da3825'}
    )
    
    fig.update_layout(title='% of Population Vaccinated', title_x=0.5, title_font=dict(size=18, color='Darkred'))

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
