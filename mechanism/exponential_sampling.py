from imports import *
from mechanism.utils import num_possible_edges



def _log_binom(m: int, t: int) -> float:
    
    if t < 0 or t > m:
        return float("-inf")
    return math.lgamma(m + 1) - math.lgamma(t + 1) - math.lgamma(m - t + 1)


def precompute_log_counts_hamming(G: nx.DiGraph):
    
    m = num_possible_edges(G)

    log_eq = [float("-inf")] * (m + 1)

    log_eq[0] = 0.0

    log_c = 0.0
    for t in range(1, m + 1):
        log_c = log_c + math.log(m - t + 1) - math.log(t)
        log_eq[t] = log_c

    return {
        "m":      m,
        "log_eq": log_eq,
    }



def sample_from_log_weights(log_weights: list, ts: list) -> int:
   
    valid_ts = [t for t in ts if math.isfinite(log_weights[t])]
    if not valid_ts:
        raise ValueError("Nenhum peso finito disponível para amostragem.")

    max_log = max(log_weights[t] for t in valid_ts)
    weights = [math.exp(log_weights[t] - max_log) for t in valid_ts]

    return random.choices(valid_ts, weights=weights, k=1)[0]


def sample_exponential_hamming_log(
    G: nx.DiGraph,
    epsilon: float,
    sensitivity: float = 1.0,
):
    
    precomp = precompute_log_counts_hamming(G)
    log_eq  = precomp["log_eq"]
    m       = precomp["m"]

    ts = list(range(m + 1))

    log_weights = [float("-inf")] * (m + 1)

    for t in ts:
        if not math.isfinite(log_eq[t]):
            continue
        log_weights[t] = log_eq[t] + (epsilon * (-t)) / (2.0 * sensitivity)

    t_sorteado = sample_from_log_weights(log_weights, ts)
    return t_sorteado, log_eq, log_weights