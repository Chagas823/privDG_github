from imports import *
from community.community import *
from community.community_adjustment import *
from mechanism.exponential_subgraph import apply_exponential_level
from reconstruction.reconnect_communities import *
from reconstruction.degree_correction import compute_noisy_degrees, degree_correction_coin_uniform_nodes


def split_three_phase_budget(epsilon: float):
    epsilon_comm = epsilon / 3.0
    epsilon_intra = epsilon / 3.0
    epsilon_recon = epsilon / 3.0

    internal = {
        "epsilon1": epsilon_comm / 2.0,
        "epsilon2": epsilon_comm / 2.0,
        "epsilon3": epsilon_intra,
        "epsilon4": epsilon_recon / 2.0,
        "epsilon5": epsilon_recon / 2.0
    }

    macro = {
        "epsilon_comm": epsilon_comm,
        "epsilon_intra": epsilon_intra,
        "epsilon_recon": epsilon_recon
    }
    return macro, internal

def privDG(G: nx.DiGraph, epsilon: float, N, verbose):
    def log(s):
        if verbose:
            print(s)

    print(f"number of nodes: {G.number_of_nodes()}")
    print(f"number of edges: {G.number_of_edges()}")

    macro, internal = split_three_phase_budget(epsilon)
    epsilon_comm = macro["epsilon_comm"]
    epsilon_intra = macro["epsilon_intra"]
    epsilon_recon = macro["epsilon_recon"]

    epsilon1 = internal["epsilon1"]
    epsilon2 = internal["epsilon2"]
    epsilon3 = internal["epsilon3"]
    epsilon4 = internal["epsilon4"]
    epsilon5 = internal["epsilon5"]

    log(
        f"Orçamento em 3 fases: "
        f"comunidades={epsilon_comm:.4f}, "
        f"exponencial={epsilon_intra:.4f}, "
        f"reconstrução={epsilon_recon:.4f}"
    )

    

    log("1) Phase 1: Private Community Division")

    node_to_comm = community_initialization_directed(G, N, epsilon1)
    node_to_comm = community_adjustment_directed(G, node_to_comm, epsilon2)

    partition = comm_dict_to_lists(node_to_comm)
    log(f"number of communities: {len(partition)}")

    log("2) Phase 2: Private Intra-Community Graph Synthesis")

    private_subgraphs, community_info = apply_exponential_level(
        G,
        partition,
        epsilon_exponential=epsilon3,
    )


    log("3) Phase 3: Private Reconstruction and Structural Adjustment")
    noisy_counts = extract_inter_community_counts(G, partition, epsilon4)
    G_synth = reconnect_communities(private_subgraphs, partition, noisy_counts)
    out_target, in_target = compute_noisy_degrees(G, epsilon5)
    G_synth = degree_correction_coin_uniform_nodes(G_synth, G, epsilon5, out_target=out_target, in_target=in_target)

    return G_synth








