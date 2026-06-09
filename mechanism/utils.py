from imports import *

def all_possible_directed_edges(G: nx.DiGraph):
 
    nodes = list(G.nodes())
    return [(u, v) for u in nodes for v in nodes if u != v]


def num_possible_edges(G: nx.DiGraph) -> int:
    n = len(G.nodes())
    return n * (n - 1)