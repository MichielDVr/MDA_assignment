#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import cloudpickle as cp
from urllib.request import urlopen

#load pickle of dataframes with all filings and adjacency matrices (dict with keys=quarters)
df = cp.load(urlopen('https://s3groupgeorgia.s3.eu-central-1.amazonaws.com/data/df_All'))
adj = cp.load(urlopen('https://s3groupgeorgia.s3.eu-central-1.amazonaws.com/data/adj'))

#--------------------------------------------------------------------------------------------
# functions used in callback

def centrality_attr(G):
    '''Calculate centrality metric and assign to node attr'''
    bb = list(nx.betweenness_centrality(G).values())
    cc = list(nx.closeness_centrality(G).values())
    dc = list(nx.degree_centrality(G).values())
    eg = list(nx.eigenvector_centrality(G).values())
    mean = 0.25*(bb/np.sum(bb)+cc/np.sum(cc)+dc/np.sum(dc)+eg/np.sum(eg))
    centrality = {j: {'betweenness': bb[j], 'closeness': cc[j], 'degree': dc[j], 'eigenvector':eg[j], 'mean':mean[j]} for j,i in enumerate(G.nodes)}
    return nx.set_node_attributes(G, centrality)


def rank_centrality(G,centrality_metric):
    '''Returns a ranking of most central nodes + centrality value'''
    all_metrics = {i:G.nodes[i][centrality_metric] for i in G.nodes}
    rank=sorted(all_metrics.items(), key=lambda x: x[1], reverse=True)
    rank_text = ["1. %s : %.4f"%(rank[0][0],rank[1][1]),
    "2. %s : %.4f" %(rank[1][0],rank[1][1]), "3. %s : %.4f" %(rank[2][0], rank[2][1])]
    return rank_text

def lowest_rank_centrality(G, centrality_metric):
    '''Returns a ranking of least central nodes + centrality value'''
    all_metrics = {i:G.nodes[i][centrality_metric] for i in G.nodes}
    rank=sorted(all_metrics.items(), key=lambda x: x[1])
    rank_text = "1. %s : %.4f" %(rank[0][0],rank[0][1])
    return rank_text

def get_cenTable(G, centrality_metric):
    '''Dataframe for ranked nodes based on centrality metric'''
    all_metrics = {i:G.nodes[i][centrality_metric] for i in G.nodes}
    cenTable=pd.DataFrame(sorted(all_metrics.items(), key=lambda x: x[1],reverse=True),columns=['Company name',str(centrality_metric)])
    return cenTable


def connectivity(G):
    '''get connectivity of the graph'''
    diameter = 'Diameter: %s'%nx.diameter(G)
    edge_connectivity = 'Edge connectivity: %s' %nx.edge_connectivity(G)
    node_connectivity = 'Node connectivity: %s' %nx.node_connectivity(G)
    return diameter, edge_connectivity, node_connectivity

def network_fit(adj,df):
    '''Fit a network from an adjacency matrix and relabel nodes by company names'''
    np.random.seed(3)
    # define network in networkx
    G = nx.from_numpy_matrix(adj)
    # relabel nodes according to company names
    labels = list(set(df['Entity name']))
    labels =[i.title() for i in labels]
    labels = {j: labels[i] for i,j in enumerate(G.nodes)}
    # calculate centrality metrics and assign to node attributes
    centrality_attr(G)
    G=nx.relabel_nodes(G,labels)

    return G

def plot_network(adj,df, centrality_metric):
    ''' plot network from adjacency matrix of a quarter and weight according to centrality metric'''
    # positions of nodes according to spring algorithm
    G= network_fit(adj,df)
    pos = nx.spring_layout(G, dim=2)
    # seperate the X,Y coordinates for Plotly
    x_nodes = [pos[i][0] for i in G.nodes]  # x-coordinates of nodes
    y_nodes = [pos[i][1] for i in G.nodes]  # y-coordinates

    # hover info for node
    node_info = ['Company: ' + str(j) + '<br>' + str(centrality_metric) + ' centrality: ' + str(np.round(G.nodes[j][centrality_metric], 4)) +'<br>' + 'Total value investments: '+ str(int(np.sum(adj,axis=1)[i]/(10**8))) + ' +e^11 $' for i,j in enumerate(G.nodes)]

    # traces for edges: different weights -> different widths of lines (I scale them to 0-1 so that abs differences are not to big)
    edge_list = G.edges
    edges_list = [dict(type='scatter',
                       x=[pos[edge[0]][0], pos[edge[1]][0]],
                       y=[pos[edge[0]][1], pos[edge[1]][1]],
                       mode='lines', hoverinfo='skip',
                       line=dict(width=(list(G[edge[0]][edge[1]].values())[0]) / (
                                   10**18) + 0.05, color='blue')) for edge in
                  edge_list]


    trace_nodes = go.Scatter(x=x_nodes,
                             y=y_nodes,
                             mode='markers',
                             marker=dict(symbol='circle', size=[(G.nodes[i][centrality_metric]+1)* 10 for i in G.nodes],
                                         colorscale=['lightgreen', 'magenta']), line=dict(color='red', width=0.5),
                             text=node_info,
                             hoverinfo='text')

    axis = dict(showbackground=True,
                showline=False,
                zeroline=False,
                showgrid=False,
                showticklabels=False,
                title='')
    # layout for the plot

    # Include the traces, create a figure
    layout = go.Layout(title="Network with shared positions of investment companies",
                       width=650,
                       height=625,
                       showlegend=False,
                       xaxis=dict(autorange=True, showgrid=False, ticks='', showticklabels=False),
                       yaxis=dict(autorange=True, showgrid=False, ticks='', showticklabels=False),
                       margin=dict(t=100),
                       hovermode='x',
                       paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       )
    data = edges_list + [trace_nodes]
    return go.Figure(data=data, layout=layout)


