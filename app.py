import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from graph import *
from dash.dependencies import Input, Output
import numpy as np

# dict with quarters as values used for slider
quarters=dict(zip(range(0,9),adj.keys()))
quarters={int(k):v for k,v in quarters.items()}

# list for centrality measures used for dropdown
ls_centrality=['degree','betweenness','closeness', 'eigenvector', 'mean']

BS = "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
app = dash.Dash(__name__, external_stylesheets=[BS])
app.title ='Uncovering the network'
server = app.server

control_centrality = dbc.Card([
        dbc.FormGroup(
            [
                dbc.Label("Node definition:"),
                dcc.Dropdown(
                    id="centrality",
                    options=[
                        {"label": i, "value": i} for i in ls_centrality
                    ],
                    value="degree"),
                ]
            ),
        ]
    )
control_quarter=dbc.Card([
        dbc.Label("Quarter:"),
        dcc.Slider(id="quarter",

                    min=0,
                    max=9,
                    step=None,
                    marks=quarters,
                    value=0,)
            ],
        )


app.layout = dbc.Container(
    [
        html.H1("Uncovering the network"),
        html.H4("Group Georgia"),
        html.Hr(),
        #html.H5("Weighted network for 13F-HR filings from the first quarter pf 2019 to the first quarter of 2021.",
                #" To goal is the examine the effect of COVID-19 on the netwrok"),
        html.H5("Select graph"),
        dbc.Row([
            dbc.Col(control_centrality,md=3) ,
            dbc.Col(control_quarter, md=6)], ),
        dbc.Row([
            dbc.Col(dcc.Graph(id="cluster-graph"), md=6),
            dbc.Col(
                [dbc.ListGroup([
                    dbc.ListGroupItemHeading("Total value of securities"),
                    dbc.ListGroupItem(id="totalValue"),
                ]), html.Hr(),
                dbc.ListGroup([
                    dbc.ListGroupItemHeading("Connectivity of graph"),
                    dbc.ListGroupItem(id="numberEdges"),
                    dbc.ListGroupItem(id="diameter"),
                    dbc.ListGroupItem(id="edge_connectivity"),
                    dbc.ListGroupItem(id="node_connectivity"),
                ]), html.Hr(),
                dbc.ListGroup([
                        dbc.ListGroupItemHeading("Most central companies"),
                        dbc.ListGroupItem(id="1_Rank-centrality"),
                        dbc.ListGroupItem(id="2_Rank-centrality"),
                        dbc.ListGroupItem(id="3_Rank-centrality"),
                        ]),
                    html.Hr(),
                    dbc.ListGroup([
                    dbc.ListGroupItemHeading("Most de-central company"),
                    dbc.ListGroupItem(id="Smallest-centrality"),
                        ]),
                ], md=3),
            ], align='right',
        ),
        dbc.Row(
            [
html.Button('Table', id='table-but', n_clicks=0),
                    html.Div(id='centrality table'),
            ], align='center'
        ),
    ]   ,
fluid=True)

@app.callback([
    Output("cluster-graph", "figure"),
    Output("numberEdges", "children"),
    Output("totalValue", "children"),
    Output("1_Rank-centrality", "children"),
    Output("2_Rank-centrality", "children"),
    Output("3_Rank-centrality", "children"),
    Output("Smallest-centrality", "children"),
    Output("diameter", "children"),
    Output("edge_connectivity", "children"),
    Output("node_connectivity", "children"),

],
    [
        Input("quarter", "value"),
        Input("centrality", "value"),
],
)

def update_figure(quarter_key,centrality_metric):
    #select quarter
    quarter = list(quarters.values())[quarter_key]
    #select adjacency matrix and dataframe of fillings for that quarter
    df_quarter = df[quarter]
    adj_quarter = adj[quarter]
    #functions to obtain callback output variables
    G=network_fit(adj_quarter,df_quarter)
    # ranking of nodes based on centrality/ connectivity
    rank_centrality_ = rank_centrality(G,centrality_metric)
    lowest_rank_centrality_ = lowest_rank_centrality(G,centrality_metric)
    connectivity_ = connectivity(G)
    numberEdges = 'Number of edges: ' + str(len(G.edges))
    totalValue = str(int(np.sum(adj_quarter) / (10 ** 13))) + 'e+13$ '
    #make network
    figure = plot_network(adj_quarter,df_quarter, centrality_metric)
    return figure, numberEdges, totalValue, rank_centrality_[0], rank_centrality_[1], rank_centrality_[2], lowest_rank_centrality_, connectivity_[0], connectivity_[1], connectivity_[2]


@app.callback(
    Output("centrality table", "children"),
    [
        Input("quarter", "value"),
        Input("centrality", "value"),
        Input('table-but', 'n_clicks'),
],
)
def table(quarter_key, centrality_metric, n_clicks):
    #select quarter
    quarter = list(quarters.values())[quarter_key]
    #select adjacency matrix and dataframe of fillings for that quarter
    df_quarter = df[quarter]
    adj_quarter = adj[quarter]
    G=network_fit(adj_quarter,df_quarter)
    # show table when button is clicked
    if n_clicks % 2:
        centable = get_cenTable(G, centrality_metric)

        return dbc.Table.from_dataframe(centable,striped=True, bordered=True, hover=True)

app.config['suppress_callback_exceptions'] = True

if __name__ == '__main__':
    app.run_server(debug=True)