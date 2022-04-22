from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import json
import pathlib


# Dash App
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Path
BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("data").resolve()

# Functions
def dot_where_comma(x):
    if "%" in x.name:
        return pd.to_numeric(x.str.replace(",", "."))
    else:
        return x


def find_majority(x):
    return x.sort_values(by=["% Voix/Ins"], ascending=False).iloc[0]


def read_file(filepath):
    df = pd.read_csv(DATA_PATH.joinpath(filepath), sep=";").apply(
        lambda x: dot_where_comma(x)
    )
    if "Code du département" in df.columns:
        df = df[
            ~df["Code du département"].isin(
                ["ZA", "ZB", "ZC", "ZD", "ZM", "ZN", "ZP", "ZS", "ZW", "ZX"]
            )
        ]
    elif "Code de la région" in df.columns:
        df = df[~df["Code de la région"].isin([1, 2, 3, 4, 6])]

    return df


def read_geojson(filepath):
    with open(DATA_PATH.joinpath(filepath)) as file:
        return json.load(file)


# Data"
data = {
    "Département": {
        "id": "Libellé du département",
        "stats": "resultats-par-dpt-france-entiere.csv",
        "candidats": "resultats-par-dpt-candidats.csv",
        "geo": "departements_france.geojson",
    },
    "Région": {
        "id": "Libellé de la région",
        "stats": "resultats-par-reg-france-entiere.csv",
        "candidats": "resultats-par-reg-candidats.csv",
        "geo": "regions_france.geojson",
    },
}

color_map_candidats = {
    "JADOT": "#FFA15A",
    "LE PEN": "#9467BD",
    "MACRON": "rgb(33,102,172)",
    "MÉLENCHON": "rgb(178,24,43)",
    "PÉCRESSE": "#19D3F3",
    "ZEMMOUR": "#AB63FA",
}


# Callbacks
@app.callback(
    Output("graph-stats", "figure"),
    Input("stats", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_choropleth_stats(stats, geography, pourcentage):
    df_stats = read_file(data[geography]["stats"])
    geojson = read_geojson(data[geography]["geo"])

    if pourcentage == "Oui":
        if stats == "Inscrits":
            color_label = "Inscrits"
        elif stats == "Votants":
            color_label = "% Vot/Ins"
        elif stats == "Abstentions":
            color_label = "% Abs/Ins"
        elif stats == "Blancs":
            color_label = "% Blancs/Vot"
        elif stats == "Nuls":
            color_label = "% Nuls/Vot"
        elif stats == "Exprimés":
            color_label = "% Exp/Vot"
    elif pourcentage == "Non":
        color_label = stats

    fig = px.choropleth(
        df_stats,
        geojson=geojson,
        locations=data[geography]["id"],
        color=color_label,
        # range_color=(0, 100),
        color_continuous_scale="RdBu_r",  # Blues
        featureidkey="properties.nom",
        projection="mercator",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # fig.update_coloraxes(showscale=False)

    colorlabel = stats
    if pourcentage == "Oui":
        colorlabel += " (%) "
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=colorlabel,
        ),
    )

    return fig


@app.callback(
    Output("graph-cand", "figure"),
    Input("candidate", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_choropleth_cand(candidate, geography, pourcentage):
    df_candidats = read_file(data[geography]["candidats"])
    geojson = read_geojson(data[geography]["geo"])

    if candidate == "MAJORITE":
        res_candidat = df_candidats.groupby(data[geography]["id"]).apply(
            lambda x: find_majority(x)
        )
        color_label = "Nom"
    else:
        res_candidat = df_candidats[df_candidats["Nom"] == candidate.upper()]
        if pourcentage == "Oui":
            color_label = "% Voix/Exp"
        elif pourcentage == "Non":
            color_label = "Voix"

    fig = px.choropleth(
        res_candidat,
        geojson=geojson,
        locations=data[geography]["id"],
        color=color_label,
        color_continuous_scale="RdBu_r",
        color_discrete_map=color_map_candidats,
        featureidkey="properties.nom",
        projection="mercator",
        hover_data=["% Voix/Exp"],
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    colorlabel = "Voix"
    if pourcentage == "Oui":
        colorlabel += " (%) "
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=colorlabel,
        ),
    )

    return fig


@app.callback(
    Output("bar-stats", "figure"),
    Input("stats", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_bar_stats(stats, geography, pourcentage):
    df_stats = read_file(data[geography]["stats"])

    if pourcentage == "Oui":
        if stats == "Inscrits":
            color_label = "Inscrits"
        elif stats == "Votants":
            color_label = "% Vot/Ins"
        elif stats == "Abstentions":
            color_label = "% Abs/Ins"
        elif stats == "Blancs":
            color_label = "% Blancs/Vot"
        elif stats == "Nuls":
            color_label = "% Nuls/Vot"
        elif stats == "Exprimés":
            color_label = "% Exp/Vot"
    elif pourcentage == "Non":
        color_label = stats

    fig = px.bar(
        df_stats.sort_values(by=color_label),
        orientation="h",
        y=data[geography]["id"],
        x=color_label,
        color=color_label,
        color_continuous_scale="RdBu_r",
    )
    fig.update_coloraxes(showscale=False)
    xlabel = stats
    if pourcentage == "Oui":
        xlabel += " (%) "
    fig.update_xaxes(title_text=xlabel)

    return fig


@app.callback(
    Output("bar-cand", "figure"),
    Input("candidate", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_bar_cand(candidate, geography, pourcentage):

    df_candidats = read_file(data[geography]["candidats"])

    if candidate == "MAJORITE":
        res_candidat = df_candidats.groupby(data[geography]["id"]).apply(
            lambda x: find_majority(x)
        )
        color_label = "Nom"
        maj_count = (
            res_candidat["Nom"]
            .value_counts(ascending=True)
            .reset_index()
            .rename(columns={"index": "Nom", "Nom": "Count"})
        )
        fig = px.bar(
            maj_count,
            orientation="h",
            color=color_label,
            color_discrete_map=color_map_candidats,
        )
    else:
        res_candidat = df_candidats[df_candidats["Nom"] == candidate.upper()]
        if pourcentage == "Oui":
            color_label = "% Voix/Exp"
        elif pourcentage == "Non":
            color_label = "Voix"

        fig = px.bar(
            res_candidat.sort_values(by=color_label),
            orientation="h",
            y=data[geography]["id"],
            x=color_label,
            color=color_label,
            color_continuous_scale="RdBu_r",
        )

    fig.update_coloraxes(showscale=False)
    xlabel = "Voix"
    if pourcentage == "Oui":
        xlabel += " (%) "
    fig.update_xaxes(title_text=xlabel)

    return fig


# Layout
colors = {"background": "#d1d1e0", "text": "#7FDBFF"}
app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # BANNER
                html.Div(
                    id="banner",
                    className="banner",
                    children=[
                        html.H1("Election présidentielle des 10 et 24 avril 2022")
                    ],
                ),
                # LEFT PANEL
                html.Div(
                    id="left-column",
                    className="four columns div-user-controls",
                    children=[
                        # HEADER
                        # html.H1(
                        #     children="Election présidentielle des 10 et 24 avril 2022",
                        # ),
                        html.H5(
                            children="Paramètres",
                        ),
                        # SETTINGS
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.H6("Résultats"),
                                dcc.Dropdown(
                                    id="resultats",
                                    options=["1er tour", "2nd tour"],
                                    value="1er tour",
                                    # inline=True,
                                ),
                            ],
                        ),
                        # Geography
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.H6("Précision géographique"),
                                dcc.Dropdown(
                                    id="geography",
                                    options=["Région", "Département"],
                                    value="Région",
                                    # inline=True,
                                ),
                            ],
                        ),
                        # Pourcentage
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.H6("Exprimé en pourcentage"),
                                dcc.Dropdown(
                                    id="pourcentage",
                                    options=["Oui", "Non"],
                                    value="Oui",
                                    # inline=True,
                                ),
                            ],
                        ),
                    ],
                ),
                # RIGHT PANELS
                html.Div(
                    id="right-column",
                    className="eight columns div-for-charts bg-grey",
                    children=[
                        # LEFT PANEL - CANDIDATES
                        html.Div(
                            [
                                html.H5("Résultats par candidat"),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="candidate",
                                            options=[
                                                "MAJORITE",
                                                "Arthaud",
                                                "Dupont-Aignan",
                                                "Hidalgo",
                                                "Jadot",
                                                "Lassalle",
                                                "Le Pen",
                                                "Macron",
                                                "Mélenchon",
                                                "Poutou",
                                                "Pécresse",
                                                "Roussel",
                                                "Zemmour",
                                            ],
                                            value="Arthaud",
                                            # inline=True
                                        ),
                                    ],
                                ),
                                dcc.Graph(id="graph-cand"),
                                dcc.Graph(id="bar-cand"),
                            ],
                            style={"width": "48%", "display": "inline-block"},
                        ),
                        # RIGHT PANEL - STATISTIQUES
                        html.Div(
                            [
                                html.H5("Statistiques de vote"),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="stats",
                                            options=[
                                                #"Inscrits",
                                                "Votants",
                                                "Abstentions",
                                                "Blancs",
                                                "Nuls",
                                                #"Exprimés",
                                            ],
                                            value="Abstentions",
                                            # inline=True
                                        ),
                                    ],
                                ),
                                dcc.Graph(id="graph-stats"),
                                dcc.Graph(id="bar-stats"),
                            ],
                            style={
                                "width": "48%",
                                "float": "right",
                                "display": "inline-block",
                            },
                        ),
                    ],
                ),
            ],
        ),
        html.Br(),
        html.Footer(
            style={"verticalAlign": "bottom"},
            children=[
                html.H5("Sources"),
                html.P("Créé sous Python avec Dash Plotly : https://dash.plotly.com/"),
                html.P(
                    "Résultats définitifs du ministère de l'intérieur : https://www.data.gouv.fr/fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-du-1er-tour/"
                ),
                html.P(
                    "Données geojson pour les cartes de France : https://france-geojson.gregoiredavid.fr/"
                ),
                html.Br(),
                html.P("Créé par Axelle Weber"),
            ],
        ),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
