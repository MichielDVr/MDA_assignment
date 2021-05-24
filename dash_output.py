import pickle

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from graph import *
from dash.dependencies import Input, Output
# dict with quarters as values
d=dict(zip(range(0,8),adj.keys()))
d={int(k):v for k,v in d.items()}

BS = "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
ls=['degree','betweenness','closeness']
app = dash.Dash(__name__, external_stylesheets=[BS])

controls = html.Div(
    [
    dbc.Card([
        html.H6("Select graph", className="card-title"),
        dbc.FormGroup(
            [
                dbc.Label("Node definition: centrality metric"),
                dcc.Dropdown(
                    id="centrality",
                    options=[
                        {"label": i, "value": i} for i in ls
                    ],
                    value="degree"),
                ]
            ),
        ]
    ),
        dbc.Label("Select quarter"),
        dcc.Slider(id="quarter",

                    min=0,
                    max=9,
                    step=None,
                    marks=d,
                    value=0,
                    )
    ],
    )

card_content = dbc.CardBody(
    [
                        html.H6("Most central companies", className="card-title"),
                        html.P(id="Rank centrality")
                        #html.P("2. %s : %s " % (rank_centrality('degree')[1][0], rank_centrality('degree')[1][1])),
                        #html.P("3. %s : %s " % (rank_centrality('degree')[2][0], rank_centrality('degree')[2][1]))
    ]
)

app.layout = dbc.Container(
    [
        html.H1("Uncovering the network"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(dcc.Graph(id="cluster-graph"), md=8),
                dbc.Col(dbc.CardBody( [
                        html.H6("Most central companies", className="card-title"),
                        html.P(id="1_Rank-centrality"),
                        html.P(id="2_Rank-centrality"),
                        html.P(id="3_Rank-centrality"),

                        #html.P("2. %s : %s " % (rank_centrality('degree')[1][0], rank_centrality('degree')[1][1])),
                        #html.P("3. %s : %s " % (rank_centrality('degree')[2][0], rank_centrality('degree')[2][1]))
])),
            ],
        align='center',
    )
    ],
 fluid=True)

@app.callback([
    Output("cluster-graph", "figure"),
    Output("1_Rank-centrality", "children"),
    Output("2_Rank-centrality", "children"),
    Output("3_Rank-centrality", "children")

],
    [
        Input("quarter", "value"),
        Input("centrality", "value"),
    ],
)





def update_figure(quarter,centrality_metric):
    quarter_ = list(d.values())[quarter]
    print(quarter_)
    adj_ = adj[quarter_]
    G=network_fit(adj_)
    rank_centrality_ = rank_centrality(G,centrality_metric)
    figure = plot_network(adj_, centrality_metric)
    return figure, rank_centrality_[0], rank_centrality_[1], rank_centrality_[2]



app.config['suppress_callback_exceptions'] = True

if __name__ == '__main__':
    app.run_server(debug=True)