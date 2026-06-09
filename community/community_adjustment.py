from community.community import *



def community_adjustment_directed(
    G: nx.DiGraph,
    node_to_comm: Dict,
    epsilon2: float,
) -> Dict:
    
 
    CF = dict(node_to_comm)          
 
    delta_fc  = 1.0
    eps_a     = 0.5 * epsilon2        
 
    for node in G.nodes():

        conn: Dict[int, float] = defaultdict(float)
 
        for nb in G.successors(node):
            if nb != node:
                conn[CF[nb]] += 1.0
 
        for nb in G.predecessors(node):
            if nb != node:
                conn[CF[nb]] += 1.0
 
        candidates = list(set(CF.values()))
        scores     = np.array([conn[c] for c in candidates], dtype=float)
 
        log_w  = (eps_a / (2.0 * delta_fc)) * scores
        log_w -= log_w.max()          
        probs  = np.exp(log_w)
        probs /= probs.sum()
 
        chosen   = np.random.choice(len(candidates), p=probs)
        CF[node] = candidates[chosen]
 
    return CF
 
 
def community_division_directed(
    G: nx.DiGraph,
    N: int = 20,
    epsilon: float = 1.0,
    epsilon1: float | None = None,
    epsilon2: float | None = None,
) -> Dict:

    if epsilon1 is None:
        epsilon1 = epsilon / 2.0
    if epsilon2 is None:
        epsilon2 = epsilon / 2.0

 
    node_to_comm = community_initialization_directed(G, N, epsilon1)
 
    node_to_comm = community_adjustment_directed(G, node_to_comm, epsilon2)
 
    return node_to_comm
