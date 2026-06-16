from imports import *
from mechanism.utils import all_possible_directed_edges


def sample_graph_given_t_hamming(G: nx.DiGraph, t: int) -> nx.DiGraph:
   
    if t == 0:
        return G.copy()

    nodes          = list(G.nodes())
    possible_edges = all_possible_directed_edges(G)
    m              = len(possible_edges)

    if t > m:
        raise ValueError(f"t={t} > m={m}:")

    flipped_indices = random.sample(range(m), t)
    flipped_set     = {possible_edges[i] for i in flipped_indices}

    E_original = set(G.edges())
    E_new      = (E_original - flipped_set) | (flipped_set - E_original)

    Gp = nx.DiGraph()
    Gp.add_nodes_from(nodes)
    Gp.add_edges_from(E_new)

    return Gp