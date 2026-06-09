from imports import * 


def _geometric_noise(scale: float, size: int) -> np.ndarray:

    p  = min(1.0 - math.exp(-1.0 / scale), 1.0 - 1e-10)
    g1 = np.random.geometric(p, size=size) - 1
    g2 = np.random.geometric(p, size=size) - 1
    return (g1 - g2).astype(float)


def _redistribute_negatives(vals: np.ndarray) -> np.ndarray:
 
    vals = vals.copy()
    neg_total = float(np.sum(np.abs(vals[vals < 0])))
    vals[vals < 0] = 0.0
    if neg_total > 0:
        vals += neg_total / len(vals)
    return vals


def comm_dict_to_lists(node_to_comm: Dict) -> List[List]:
    groups: Dict[int, List] = defaultdict(list)

    for node, cid in node_to_comm.items():
        groups[cid].append(node)
    
    return list(groups.values())

def nx_to_igraph_directed(G: nx.DiGraph) -> ig.Graph:
    nodes = list(G.nodes())
    node_index = {n: i for i, n in enumerate(nodes)}
    g_ig = ig.Graph(n=len(nodes), directed=True)
    g_ig.vs["name"] = nodes
    edges = [(node_index[u], node_index[v]) for u, v in G.edges()]
    g_ig.add_edges(edges)
    return g_ig

def community_initialization_directed(
    G: nx.DiGraph,
    N: int,
    epsilon1: float
    
    ) -> Dict:
      
     
        nodes = list(G.nodes())
        n = len(nodes)

        shuffled_nodes = [nodes[i] for i in np.random.permutation(n)]

        m1   = (n + N - 1) // N 
        
        node_to_sn: Dict = {node: idx // N for idx, node in enumerate(shuffled_nodes)}
        inner_weight: Dict[int, float]         = defaultdict(float)
        outer_weight: Dict[Tuple[int,int], float] = defaultdict(float)

        for u, v in G.edges():
            su = node_to_sn[u]
            sv = node_to_sn[v]
            if su == sv:
                inner_weight[su] += 1.0
            else:
                outer_weight[(su, sv)] += 1.0

        for s in range(m1):
            inner_weight.setdefault(s, 0.0)

        delta_fi = 2.0   
        delta_fo = 1.0   

        inner_vals = np.array([inner_weight[s] for s in range(m1)], dtype=float)
        inner_vals = inner_vals + _geometric_noise(delta_fi / epsilon1, size=m1)
        inner_vals = _redistribute_negatives(inner_vals)

        outer_keys = list(outer_weight.keys())
        outer_vals = np.array([outer_weight[k] for k in outer_keys], dtype=float)
        outer_vals = outer_vals + _geometric_noise(delta_fo / epsilon1, size=len(outer_vals))
        outer_vals = _redistribute_negatives(outer_vals)

        noisy_outer: Dict[Tuple[int,int], float] = {
            k: float(v) for k, v in zip(outer_keys, outer_vals)
        }
        g_ig = ig.Graph(n=m1, directed=True)
 
        edge_list:   List[Tuple[int, int]] = []
        weight_list: List[float]           = []
    
        for (s1, s2), w in noisy_outer.items():
            if w > 0:
                edge_list.append((s1, s2))
                weight_list.append(w)

        for s in range(m1):
            w = float(inner_vals[s])
            if w > 0:
                edge_list.append((s, s))
                weight_list.append(w)
    
        if edge_list:
            g_ig.add_edges(edge_list)
            g_ig.es["weight"] = weight_list

        partition = leidenalg.find_partition(
                    g_ig,
                    leidenalg.ModularityVertexPartition,
                    weights="weight" if edge_list else None,
                )

        sn_to_comm: Dict[int, int] = {}
        for comm_id, members in enumerate(partition):
            for s in members:
                sn_to_comm[s] = comm_id
    
        node_to_comm: Dict = {
            node: sn_to_comm[node_to_sn[node]] for node in G.nodes()
        }

        return node_to_comm