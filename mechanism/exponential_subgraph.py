from mechanism.exponential_sampling import sample_exponential_hamming_log
from mechanism.sample_graph_given import sample_graph_given_t_hamming
from imports import *

def level(Gc, epsilon, sensitivity):
    t, log_counts, log_weights = sample_exponential_hamming_log(
            Gc,
            epsilon=epsilon,
            sensitivity=sensitivity,
        )

    Gc_priv = sample_graph_given_t_hamming(Gc, t)
    return Gc_priv, t

def apply_exponential_level(
    G: nx.DiGraph,
    partition,
    epsilon_exponential: float,
    sensitivity: float = 1.0,
):
  
    private_subgraphs = {}
    community_info    = []

    for cid, nodes in enumerate(partition):
        nodes = set(nodes)
        Gc    = G.subgraph(nodes).copy()

        if Gc.number_of_nodes() <= 1 or Gc.number_of_edges() == 0:
            private_subgraphs[cid] = Gc.copy()
            community_info.append({
                "cid":          cid,
                "n_nodes":      Gc.number_of_nodes(),
                "n_edges":      Gc.number_of_edges(),
                "t":            0,
                "epsilon_used": epsilon_exponential,
                "mechanism":    "hamming",
                "skipped":      True,
            })
            continue

        
        Gc_priv, t = level(Gc, epsilon_exponential, sensitivity)


        private_subgraphs[cid] = Gc_priv
        community_info.append({
            "cid":          cid,
            "n_nodes":      Gc.number_of_nodes(),
            "n_edges":      Gc.number_of_edges(),
            "t":            t,
            "epsilon_used": epsilon_exponential,
            "mechanism":    "hamming",
            "skipped":      False,
        })

    return private_subgraphs, community_info