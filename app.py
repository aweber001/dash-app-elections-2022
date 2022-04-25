from tokenize import group
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


# Data
data = {
    "1er tour": {
        "France entière": {
            "id": "Libellé du niveau",
            "stats": "resultats-t1-france-entiere.csv",
            "candidats": "resultats-t1-france-entiere.csv",
            "geo": "departements_france.geojson",
        },
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
    },
    "2nd tour": {
        "France entière": {
            "id": "Libellé du niveau",
            "stats": "resultats-t2-france-entiere.csv",
            "candidats": "resultats-t2-france-entiere.csv",
            "geo": "departements_france.geojson",
        },
        "Département": {
            "id": "Libellé du département",
            "stats": "resultats-par-dpt-t2-france-entiere.csv",
            "candidats": "resultats-par-dpt-t2-candidats.csv",
            "geo": "departements_france.geojson",
        },
        "Région": {
            "id": "Libellé de la région",
            "stats": "resultats-par-reg-t2-france-entiere.csv",
            "candidats": "resultats-par-reg-t2-candidats.csv",
            "geo": "regions_france.geojson",
        },
    },
}

# List of candidates
list_candidates = {
    "1er tour": [
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
    "2nd tour": ["MAJORITE", "Macron", "Le Pen"],
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
def create_choropleth_stats(stats, geography, pourcentage, tour):
    df_stats = read_file(data[tour][geography]["stats"])
    geojson = read_geojson(data[tour][geography]["geo"])

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
        locations=data[tour][geography]["id"],
        color=color_label,
        # range_color=(0, 100), # TODO: adapt color bar or not ?
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


def create_choropleth_cand(candidate, geography, pourcentage, tour):
    df_candidats = read_file(data[tour][geography]["candidats"])
    geojson = read_geojson(data[tour][geography]["geo"])

    if candidate == "MAJORITE":
        res_candidat = df_candidats.groupby(data[tour][geography]["id"]).apply(
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
        locations=data[tour][geography]["id"],
        color=color_label,
        color_continuous_scale="RdBu_r",
        # range_color=(0, 100),
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


def create_bar_stats(stats, geography, pourcentage, tour):
    df_stats = read_file(data[tour][geography]["stats"])

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
        y=data[tour][geography]["id"],
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


def create_bar_cand(candidate, geography, pourcentage, tour):

    df_candidats = read_file(data[tour][geography]["candidats"])

    if candidate == "MAJORITE":
        res_candidat = df_candidats.groupby(data[tour][geography]["id"]).apply(
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
            y=data[tour][geography]["id"],
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


def create_results_cand(geography, pourcentage, tour):

    df = read_file(data[tour][geography]["candidats"])

    if pourcentage == "Oui":
        color_label = "% Voix/Exp"
    elif pourcentage == "Non":
        color_label = "Voix"

    fig = px.bar(
        df.sort_values(by=color_label),
        orientation="h",
        y="Nom",
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


def create_results_stats(geography, pourcentage, tour):

    serie = read_file(data[tour][geography]["stats"]).iloc[0]

    if pourcentage == "Oui":
        values = ["% Vot/Ins", "% Abs/Ins", "% Blancs/Vot", "% Nuls/Vot"]
    elif pourcentage == "Non":
        values = ["Votants", "Abstentions", "Blancs", "Nuls"]

    df = pd.DataFrame(serie[values])
    fig = px.bar(
        df,
        x=0,
        y=df.index,
        color=df.index,
        orientation="h",
    )

    fig.update_coloraxes(showscale=False)
    xlabel = "Voix"
    if pourcentage == "Oui":
        xlabel += " (%) "
    fig.update_xaxes(title_text=xlabel)

    return fig


@app.callback(
    Output("left-graphs", "children"),
    Output("right-graphs", "children"),
    Input("geography", "value"),
    Input("tour", "value"),
    Input("stats", "value"),
    Input("candidate", "value"),
    Input("pourcentage", "value"),
)
def display_candidates_results(geography, tour, stats, candidate, pourcentage):
    if geography == "France entière":
        res_cand = create_results_cand(geography, pourcentage, tour)
        res_stats = create_results_stats(geography, pourcentage, tour)

        children_left = [dcc.Graph(figure=res_cand)]
        children_right = [dcc.Graph(figure=res_stats)]

    else:
        chloro_cand = create_choropleth_cand(candidate, geography, pourcentage, tour)
        bar_cand = create_bar_cand(candidate, geography, pourcentage, tour)
        children_left = [dcc.Graph(figure=chloro_cand), dcc.Graph(figure=bar_cand)]

        chloro_stats = create_choropleth_stats(stats, geography, pourcentage, tour)
        bar_stats = create_bar_stats(stats, geography, pourcentage, tour)
        children_right = [dcc.Graph(figure=chloro_stats), dcc.Graph(figure=bar_stats)]

    return children_left, children_right


@app.callback(Output("candidate", "options"), Input("tour", "value"))
def set_candidates_options(selected_tour):
    return [{"label": i, "value": i} for i in list_candidates[selected_tour]]


# Layout
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
                    className="three columns div-user-controls",
                    children=[
                        # HEADER
                        html.H5(
                            children="Paramètres",
                        ),
                        # SETTINGS
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.P("Résultats du :"),
                                dcc.Dropdown(
                                    id="tour",
                                    options=["1er tour", "2nd tour"],
                                    value="1er tour",
                                    # inline=True,
                                ),
                            ],
                        ),
                        html.Br(),
                        # Geography
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.P("Précision géographique :"),
                                dcc.Dropdown(
                                    id="geography",
                                    options=["France entière", "Région", "Département"],
                                    value="France entière",
                                    # inline=True,
                                ),
                            ],
                        ),
                        html.Br(),
                        # Pourcentage
                        html.Div(
                            className="div-for-dropdown",
                            children=[
                                html.P("En pourcentage :"),
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
                    className="nine columns div-for-charts bg-grey",
                    children=[
                        # LEFT PANEL - CANDIDATES
                        html.Div(
                            id="left-panel",
                            children=[
                                html.H5("Résultats par candidat"),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="candidate",
                                            value="MAJORITE",
                                            # inline=True
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id="left-graphs",
                                    children=[
                                        # dcc.Graph(id="graph-cand"),
                                        # dcc.Graph(id="bar-cand"),
                                    ],
                                ),
                            ],
                            style={"width": "48%", "display": "inline-block"},
                        ),
                        # RIGHT PANEL - STATISTIQUES
                        html.Div(
                            id="right-panel",
                            children=[
                                html.H5("Statistiques de vote"),
                                html.Div(
                                    className="div-for-dropdown",
                                    children=[
                                        dcc.Dropdown(
                                            id="stats",
                                            options=[
                                                # "Inscrits",
                                                "Votants",
                                                "Abstentions",
                                                "Blancs",
                                                "Nuls",
                                                # "Exprimés",
                                            ],
                                            value="Abstentions",
                                            # inline=True
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id="right-graphs",
                                    children=[
                                        # dcc.Graph(id="graph-stats"),
                                        # dcc.Graph(id="bar-stats"),
                                    ],
                                ),
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
