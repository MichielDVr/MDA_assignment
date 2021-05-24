#!/usr/bin/env python
# coding: utf-8


import pandas as pd

import pickle
import numpy as np
import networkx as nx
import plotly.graph_objects as go



df0 = pickle.load(open('adj_19q1', "rb"))
df1 = pickle.load(open('adj_19q2', "rb"))
df2 = pickle.load(open('adj_19q3', "rb"))
df3 = pickle.load(open('adj_19q4', "rb"))
df4 = pickle.load(open('adj_20q1', "rb"))
df5 = pickle.load(open('adj_20q2', "rb"))
df6 = pickle.load(open('adj_20q3', "rb"))
df7 = pickle.load(open('adj_20q4', "rb"))
df8 = pickle.load(open('adj_21q1', "rb"))
ls = ['2019 Q1','2019 Q2','2019 Q3','2019 Q4','2020 Q1','2020 Q2','2020 Q3','2020 Q4','2021 Q1']
df = [df0,df1,df2,df3,df4,df5,df5,df6,df7,df8]

k=0
adj={}
for i in range(0,8):
    adj[str(ls[k])] = df[i]
    k+=1

with open("C:/Users/michi/Desktop/MDA/adj","wb") as f:
    pickle.dump(adj, f)
f.close()






#labels = list(set(df['Entity name'].str.lower()))




def Adj_weight(df):
    dummies = pd.get_dummies(df['CUSIP']).astype(float)
    weights = dummies.T * np.asarray(df['(x$1000)']).astype(float)
    df_ = pd.concat([df[['CIK']], weights.T], axis=1)
    weights = df_.groupby(['CIK']).sum()
    v = np.dot(weights, weights.T)
    v = np.tril(v, -1)
    return v, weights







def centrality_attr(G):
    bb = nx.betweenness_centrality(G)
    cc = nx.closeness_centrality(G)
    dc = nx.degree_centrality(G)
    centrality = {j: {'betweenness': bb[j], 'closeness': cc[j], 'degree': dc[j]} for i, j in enumerate(G.nodes)}
    nx.set_node_attributes(G, centrality)

def rank_centrality(G,centrality_metric):
    if centrality_metric == 'degree':
        rank=sorted(nx.degree_centrality(G).items(), key=lambda x: x[1], reverse=True)
    if centrality_metric == 'betweenness':
        rank=sorted(nx.degree_centrality(G).items(), key=lambda x: x[1], reverse=True)
    if centrality_metric == 'closeness':
        rank=sorted(nx.degree_centrality(G).items(), key=lambda x: x[1], reverse=True)
    rank_ = ["1. %s : %s " %(rank[0][0],rank[1][1]),
    "2. %s : %s " %(rank[1][0],rank[1][1]), "3. %s : %s " %(rank[2][0], rank[2][1])]
    return rank_

def network_fit(adj):
    np.random.seed(3)
    # define network in networkx
    G = nx.from_numpy_matrix(adj)
    # labels are CIK numbers
    #labels = list(set(df['quarter_3']['Entity name'].str.lower()))
#    labels = {i: adj[1].index[i] for i in G.nodes}

 #   G = nx.relabel_nodes(G, labels)
    # calculate centrality metrics and assign to node attributes
    centrality_attr(G)
    return G

# TODO: instead of CIK numbers company names
def plot_network(adj, centrality_metric):
    # positions of nodes according to spring algorithm
    G= network_fit(adj)
    pos = nx.spring_layout(G, dim=2)

    # we need to seperate the X,Y coordinates for Plotly
    x_nodes = [pos[i][0] for i in G.nodes]  # x-coordinates of nodes
    y_nodes = [pos[i][1] for i in G.nodes]  # y-coordinates

    # hover info for node
    node_info = ['CIK: ' + str(i) + '<br>' + str(centrality_metric) + ' centrality :' + str(
        np.round(G.nodes[i][centrality_metric], 4)) for i in (G.nodes)]
    # edge_info=['MV of shared sec.:' + str(i) for i in adj]

    # traces for edges: different weights -> different widths of lines (I scale them to 0-1 so that abs differences are not to big)
    edge_list = G.edges
    total_weight = []
    for edge in edge_list:
        total_weight.append(list(G[edge[0]][edge[1]].values())[0])
    edges_list = [dict(type='scatter',
                       x=[pos[edge[0]][0], pos[edge[1]][0]],
                       y=[pos[edge[0]][1], pos[edge[1]][1]],
                       mode='lines', hoverinfo='skip', text=np.max(G[edge[0]][edge[1]]['weight']),
                       line=dict(width=(list(G[edge[0]][edge[1]].values())[0] - np.min(total_weight)) / (
                                   np.max(total_weight) - np.min(total_weight)) * 4 + 0.05, color='blue')) for edge in
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
    trace_nodes = go.Scatter(x=x_nodes,
                             y=y_nodes,
                             # z=z_nodes,
                             mode='markers',
                             marker=dict(symbol='circle', size=[G.nodes[i][centrality_metric] * 20 for i in G.nodes],
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


# In[19]:

#plot_network(q2[0], q2[1], 'closeness')

