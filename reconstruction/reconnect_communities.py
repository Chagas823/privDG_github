
from imports import *
from tqdm import tqdm
from community.community import _geometric_noise, _redistribute_negatives



def extract_inter_community_counts(
    G: nx.DiGraph,
    partition: List[List],
    epsilon4: float,
) -> Dict[Tuple[int, int], float]:
   
    node_to_cid: Dict = {}
    for cid, nodes in enumerate(partition):
        for node in nodes:
            node_to_cid[node] = cid

    K = len(partition)

    true_counts: Dict[Tuple[int, int], float] = defaultdict(float)
    for u, v in G.edges():
        cu = node_to_cid[u]
        cv = node_to_cid[v]
        if cu != cv:
            true_counts[(cu, cv)] += 1.0

    pairs = [(i, j) for i in range(K) for j in range(K) if i != j]

    vals = np.array([true_counts.get(p, 0.0) for p in pairs], dtype=float)
    vals = vals + _geometric_noise(1.0 / epsilon4, size=len(vals))
    vals = _redistribute_negatives(vals)

    noisy_counts = {p: float(v) for p, v in zip(pairs, vals)}
    return noisy_counts



def _sample_inter_edges(
    src_nodes: List,
    dst_nodes: List,
    target: int,
) -> List[Tuple]:
    
    Na, Nb = len(src_nodes), len(dst_nodes)
    target = max(0, min(target, Na * Nb))

    if target == 0:
        return []

    all_pairs = [(u, v) for u in src_nodes for v in dst_nodes]
    return random.sample(all_pairs, target)



def _allocate_stubs(total: int, weights: List[float]) -> List[int]:
   
    K = len(weights)
    if total == 0 or K == 0:
        return [0] * K

    total_w = sum(weights)
    if total_w == 0:
        base, rem = divmod(total, K)
        result = [base] * K
        for i in range(rem):
            result[i] += 1
        return result

    quotas  = [total * w / total_w for w in weights]
    floors  = [int(q) for q in quotas]
    resids  = [q - f for q, f in zip(quotas, floors)]
    remainder = total - sum(floors)
    order   = sorted(range(K), key=lambda i: resids[i], reverse=True)
    for i in order[:remainder]:
        floors[i] += 1

    return floors




def reconnect_communities(
    private_subgraphs: Dict[int, nx.DiGraph],
    partition: List[List],
    noisy_counts: Dict[Tuple[int, int], float],
) -> nx.DiGraph:
   
    G_synth = nx.DiGraph()

    for cid, Gc in private_subgraphs.items():
        G_synth.add_nodes_from(Gc.nodes())
        G_synth.add_edges_from(Gc.edges())

    K = len(partition)

    for i in range(K):
        for j in range(K):
            if i == j:
                continue
            src_nodes = list(partition[i])
            dst_nodes = list(partition[j])
            target    = int(round(noisy_counts.get((i, j), 0.0)))
            inter_edges = _sample_inter_edges(src_nodes, dst_nodes, target)
            G_synth.add_edges_from(inter_edges)

    G_synth = _rewire_isolated_nodes(G_synth)
    return G_synth



def _rewire_isolated_nodes(G: nx.DiGraph) -> nx.DiGraph:
    
    Gc    = G.copy()
    nodes = list(Gc.nodes())
    n     = len(nodes)

    if n < 2:
        return Gc

    isolated = [v for v in nodes if Gc.degree(v) == 0]

    if not isolated:
        return Gc

    for v in isolated:
        degrees = [Gc.degree(u) + 1 for u in nodes]  

        candidates_out = [u for u in nodes if u != v]
        weights_out    = [degrees[nodes.index(u)] for u in candidates_out]
        u_out = random.choices(candidates_out, weights=weights_out, k=1)[0]
        Gc.add_edge(v, u_out)

        candidates_in = [u for u in nodes if u != v and u != u_out]
        if candidates_in:
            weights_in = [degrees[nodes.index(u)] for u in candidates_in]
            u_in = random.choices(candidates_in, weights=weights_in, k=1)[0]
            Gc.add_edge(u_in, v)

    return Gc