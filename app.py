from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import json
import pathlib


# Dash App
app = Dash(__name__)

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
    "LE PEN": "#EF553B",
    "MACRON": "#636EFA",
    "MÉLENCHON": "#00CC96",
    "PÉCRESSE": "#19D3F3",
    "ZEMMOUR": "#AB63FA",
}
color_continuous_scale = "Blues"


# Callbacks
@app.callback(
    Output("graph-stats", "figure"),
    Input("stats", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_choropleth_stats(stats, geography, pourcentage):
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

    fig = px.choropleth(
        df_stats,
        geojson=read_geojson(data[geography]["geo"]),
        locations=data[geography]["id"],
        color=color_label,
        color_continuous_scale="Purples",
        featureidkey="properties.nom",
        projection="mercator",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig


@app.callback(
    Output("graph-cand", "figure"),
    Input("candidate", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_choropleth_cand(candidate, geography, pourcentage):

    df_candidats = read_file(data[geography]["candidats"])

    if candidate == "Majorité":
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
        geojson=read_geojson(data[geography]["geo"]),
        locations=data[geography]["id"],
        color=color_label,
        color_continuous_scale="Blues",
        color_discrete_map=color_map_candidats,
        featureidkey="properties.nom",
        projection="mercator",
        hover_data=["% Voix/Exp"],
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

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
        color_continuous_scale="Purples",
    )

    return fig


@app.callback(
    Output("bar-cand", "figure"),
    Input("candidate", "value"),
    Input("geography", "value"),
    Input("pourcentage", "value"),
)
def display_bar_cand(candidate, geography, pourcentage):

    df_candidats = read_file(data[geography]["candidats"])

    if candidate == "Majorité":
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
            color_continuous_scale="Blues",
        )

    return fig


# Layout
app.layout = html.Div(
    [
        html.H4("Elections présidentielles 2022 - 1er tour"),
        html.P("Précision géographique :"),
        dcc.RadioItems(
            id="geography",
            options=["Région", "Département"],
            value="Région",
            inline=True,
        ),
        html.P("Exprimé en pourcentage :"),
        dcc.RadioItems(
            id="pourcentage", options=["Oui", "Non"], value="Oui", inline=True
        ),
        html.Div(
            [
                html.H5("Résultats par candidat"),
                html.P("Candidat :"),
                dcc.Dropdown(
                    id="candidate",
                    options=[
                        "Majorité",
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
                    value="Majorité",
                    # inline=True
                ),
                dcc.Graph(id="graph-cand"),
                dcc.Graph(id="bar-cand"),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
        html.Div(
            [
                html.H5("Statistiques de vote"),
                html.P("Chiffres :"),
                dcc.Dropdown(
                    id="stats",
                    options=[
                        "Inscrits",
                        "Votants",
                        "Abstentions",
                        "Blancs",
                        "Nuls",
                        "Exprimés",
                    ],
                    value="Votants",
                    # inline=True
                ),
                dcc.Graph(id="graph-stats"),
                dcc.Graph(id="bar-stats"),
            ],
            style={"width": "48%", "float": "right", "display": "inline-block"},
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)