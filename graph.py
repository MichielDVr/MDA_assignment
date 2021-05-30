#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import pickle
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import cloudpickle as cp
from urllib.request import urlopen


adj = pickle.load(open("adj","rb"))
df = cp.load(urlopen('https://s3groupgeorgia.s3.eu-central-1.amazonaws.com/data/df_All'))


def Adj_weight(df):
    '''compute adjacency matrix of investment companies'''
    dummies = pd.get_dummies(df['CUSIP']).astype(float)
    weights = dummies.T * np.asarray(df['(x$1000)']).astype(float)
    df_ = pd.concat([df[['CIK']], weights.T], axis=1)
    weights = df_.groupby(['CIK']).sum()
    v = np.dot(weights, weights.T)
    v = np.tril(v, -1)
    return v, weights







def centrality_attr(G):
    '''Calculate centrality metric and assign to nodes'''
    bb = list(nx.betweenness_centrality(G).values())
    cc = list(nx.closeness_centrality(G).values())
    dc = list(nx.degree_centrality(G).values())
    eg = list(nx.eigenvector_centrality(G).values())
    mean = 0.25*(bb/np.sum(bb)+cc/np.sum(cc)+dc/np.sum(dc)+eg/np.sum(eg))
    centrality = {j: {'betweenness': bb[j], 'closeness': cc[j], 'degree': dc[j], 'eigenvector':eg[j], 'mean':mean[j]} for j,i in enumerate(G.nodes)}
    return nx.set_node_attributes(G, centrality)


#print([i for i in G.nodes])
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

def connectivity(G):
    diameter = 'Diameter: %s'%nx.diameter(G)
    edge_connectivity = 'Edge connectivity: %s' %nx.edge_connectivity(G)
    node_connectivity = 'Node connectivity: %s' %nx.node_connectivity(G)
    return diameter, edge_connectivity, node_connectivity

def network_fit(adj,df):
    '''Fit a network from an adjacency matrix and relabel nodes by company names'''
    np.random.seed(3)
    # define network in networkx
    G = nx.from_numpy_matrix(adj)

    labels = list(set(df['Entity name']))
    labels =[i.title() for i in labels]


    labels = {j: labels[i] for i,j in enumerate(G.nodes)}
    centrality_attr(G)

    G=nx.relabel_nodes(G,labels)

    # calculate centrality metrics and assign to node attributes
    return G


# TODO: instead of CIK numbers company names
def plot_network(adj,df, centrality_metric):
    ''' plot network from adjacency matrix of a quarter and weight according to centrality metric'''
    # positions of nodes according to spring algorithm
    G= network_fit(adj,df)
    pos = nx.spring_layout(G, dim=2)
    # we need to seperate the X,Y coordinates for Plotly
    x_nodes = [pos[i][0] for i in G.nodes]  # x-coordinates of nodes
    y_nodes = [pos[i][1] for i in G.nodes]  # y-coordinates

    # hover info for node
    node_info = ['Company: ' + str(j) + '<br>' + str(centrality_metric) + ' centrality: ' + str(
        np.round(G.nodes[j][centrality_metric], 4)) +'<br>' + 'Market value: '+ str(int(np.sum(adj,axis=1)[i]/(10**10))) + ' *e^10' for i,j in enumerate(G.nodes)]
    # edge_info=['MV of shared sec.:' + str(i) for i in adj]
    # traces for edges: different weights -> different widths of lines (I scale them to 0-1 so that abs differences are not to big)
    edge_list = G.edges
    total_weight = []
    edges_list = [dict(type='scatter',
                       x=[pos[edge[0]][0], pos[edge[1]][0]],
                       y=[pos[edge[0]][1], pos[edge[1]][1]],
                       mode='lines', hoverinfo='skip',
                       line=dict(width=(list(G[edge[0]][edge[1]].values())[0]) / (
                                   10**18) + 0.05, color='blue')) for edge in
                  edge_list]

    # trace3_list = []
    # a=[]
    # middle_node_trace = go.Scatter(
    #     x=[],
    #     y=[],
    #     text=[],
    #     mode='markers',
    #     hoverinfo='text',
    #     marker=go.Marker(
    #         opacity=0
    #     )
    # )
    # for edge in G.edges(data=True):
    #     trace3=go.Scatter(
    #         x=[],
    #         y=[],
    #         mode='lines',
    #         line=dict(color='rgb(210,210,210)', width=edge[2]['weight']),
    #         hoverinfo='none'
    #     )
    #     x0, y0 = pos[edge[0]]
    #     x1, y1 = pos[edge[1]]
    #     trace3['x'] += (x0, x1, None)
    #     trace3['y'] += (y0, y1, None)
    #     trace3_list += trace3

    #     middle_node_trace['x']+=(x0+x1)/2
    #     middle_node_trace['y']+=(y0+y1)/2
    #     a.append(edge[2]['weight'])
    # middle_node_trace['text'] =a

    # edges_list.append(trace3_list)
    # txt='Most central companies:<br>1. %s <br> 2. %s <br> 3. %s' %(d[0],d[1],d[2])

    # trace for nodes, different node sizes -> choose centrality alg
    # node sizes are multiplied by a number so that abs differences are bigger
    #total_weight_nodes = [G.nodes[i][centrality_metric] for i in G.nodes]
    #print(total_weight_nodes)
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
    layout = go.Layout(title="Network for shared positions of 20 large investment companies",
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


