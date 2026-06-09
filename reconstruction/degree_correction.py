
import random
import networkx as nx
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from imports import *
from community.community import _geometric_noise, _redistribute_negatives



def compute_noisy_degrees(
    G_orig: nx.DiGraph,
    epsilon5: float,
) -> Tuple[Dict, Dict]:
 
    nodes = list(G_orig.nodes())
    n     = len(nodes)
    eps   = epsilon5 / 2.0   

    out_orig  = np.array([G_orig.out_degree(v) for v in nodes], dtype=float)
    out_noisy = out_orig + _geometric_noise(1.0 / eps, size=n)
    out_noisy = _redistribute_negatives(out_noisy)
    out_target = {v: int(round(out_noisy[i])) for i, v in enumerate(nodes)}

    in_orig  = np.array([G_orig.in_degree(v) for v in nodes], dtype=float)
    in_noisy = in_orig + _geometric_noise(1.0 / eps, size=n)
    in_noisy = _redistribute_negatives(in_noisy)
    in_target = {v: int(round(in_noisy[i])) for i, v in enumerate(nodes)}

    return out_target, in_target



def degree_correction(
    G_synth:    nx.DiGraph,
    G_orig:     nx.DiGraph,
    epsilon5:   float,
    out_target: Dict | None = None,
    in_target:  Dict | None = None,
) -> nx.DiGraph:
  
    if out_target is None or in_target is None:
        out_target, in_target = compute_noisy_degrees(G_orig, epsilon5)

    Gc    = G_synth.copy()
    nodes = list(G_orig.nodes())

    for v in nodes:
        target  = out_target[v]
        current = Gc.out_degree(v)

        if current > target:
            to_remove = random.sample(list(Gc.out_edges(v)), current - target)
            Gc.remove_edges_from(to_remove)

        elif current < target:
            existing   = set(Gc.successors(v))
            candidates = [u for u in nodes if u != v and u not in existing]
            n_add      = min(target - current, len(candidates))
            if n_add > 0:
                Gc.add_edges_from((v, u) for u in random.sample(candidates, n_add))

    for v in nodes:
        target  = in_target[v]
        current = Gc.in_degree(v)

        if current > target:
            to_remove = random.sample(list(Gc.in_edges(v)), current - target)
            Gc.remove_edges_from(to_remove)

        elif current < target:
            existing   = set(Gc.predecessors(v))
            candidates = [u for u in nodes if u != v and u not in existing]
            n_add      = min(target - current, len(candidates))
            if n_add > 0:
                Gc.add_edges_from((u, v) for u in random.sample(candidates, n_add))

    return Gc




def _split_residuals(
    target: Dict,
    degree_fn
) -> Tuple[Dict, Dict]:
    deficit: Dict = {}
    excess: Dict = {}

    for v, tgt in target.items():
        diff = int(tgt) - degree_fn(v)

        if diff > 0:
            deficit[v] = diff
        elif diff < 0:
            excess[v] = -diff

    return deficit, excess


class _RandomSet:
  

    __slots__ = ("items", "pos")

    def __init__(self, iterable=None):
        self.items = []
        self.pos = {}

        if iterable is not None:
            for x in iterable:
                self.add(x)

    def add(self, x):
        if x not in self.pos:
            self.pos[x] = len(self.items)
            self.items.append(x)

    def discard(self, x):
        idx = self.pos.pop(x, None)

        if idx is None:
            return

        last = self.items.pop()

        if idx < len(self.items):
            self.items[idx] = last
            self.pos[last] = idx

    def choice(self):
        return random.choice(self.items)

    def __contains__(self, x):
        return x in self.pos

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def to_list(self):
        return self.items



def _removal_phase(
    Gc: nx.DiGraph,
    out_excess: Dict,
    in_excess: Dict,
) -> Tuple[int, int]:
    

    total_out = sum(out_excess.values())
    total_in = sum(in_excess.values())

    cross = defaultdict(_RandomSet)     
    cross_inv = defaultdict(_RandomSet)  

    for v in list(in_excess):
        for u in Gc.predecessors(v):
            if u in out_excess:
                cross[v].add(u)
                cross_inv[u].add(v)

    valid_v = _RandomSet(v for v, s in cross.items() if len(s) > 0)
    valid_u = _RandomSet(u for u, s in cross_inv.items() if len(s) > 0)

    def _remove_pair_from_indexes(u, v):
        if v in cross:
            cross[v].discard(u)

            if len(cross[v]) == 0:
                del cross[v]
                valid_v.discard(v)

        if u in cross_inv:
            cross_inv[u].discard(v)

            if len(cross_inv[u]) == 0:
                del cross_inv[u]
                valid_u.discard(u)

    def _cleanup_u(u):
       

        if u not in cross_inv:
            valid_u.discard(u)
            return

        for v in list(cross_inv[u].to_list()):
            if v in cross:
                cross[v].discard(u)

                if len(cross[v]) == 0:
                    del cross[v]
                    valid_v.discard(v)

        del cross_inv[u]
        valid_u.discard(u)

    def _cleanup_v(v):
        

        if v not in cross:
            valid_v.discard(v)
            return

        for u in list(cross[v].to_list()):
            if u in cross_inv:
                cross_inv[u].discard(v)

                if len(cross_inv[u]) == 0:
                    del cross_inv[u]
                    valid_u.discard(u)

        del cross[v]
        valid_v.discard(v)

    while total_out > 0 and total_in > 0 and len(valid_v) > 0 and len(valid_u) > 0:

        start_with_in = random.choice((True, False))

        if start_with_in:
            v = valid_v.choice()

            if v not in cross or len(cross[v]) == 0:
                valid_v.discard(v)
                continue

            u = cross[v].choice()

        else:
            u = valid_u.choice()

            if u not in cross_inv or len(cross_inv[u]) == 0:
                valid_u.discard(u)
                continue

            v = cross_inv[u].choice()

        if not Gc.has_edge(u, v):
            _remove_pair_from_indexes(u, v)
            continue

        Gc.remove_edge(u, v)

        _remove_pair_from_indexes(u, v)

        out_excess[u] -= 1
        in_excess[v] -= 1

        total_out -= 1
        total_in -= 1

        if out_excess[u] == 0:
            del out_excess[u]
            _cleanup_u(u)

        if in_excess.get(v, 0) == 0:
            in_excess.pop(v, None)
            _cleanup_v(v)
    return total_out, total_in



def _addition_phase(
    Gc: nx.DiGraph,
    nodes: List,
    out_deficit: Dict,
    in_deficit: Dict,
) -> Tuple[int, int]:
   

    total_out = sum(out_deficit.values())
    total_in = sum(in_deficit.values())

    active_out = _RandomSet(out_deficit.keys())
    active_in = _RandomSet(in_deficit.keys())

    no_progress_limit = max(len(nodes) * 4, 64)
    no_progress = 0

    def _sample_u_for_v(v):
        if len(active_out) == 0:
            return None

        tries = min(64, max(8, len(active_out)))

        for _ in range(tries):
            u = active_out.choice()

            if u != v and not Gc.has_edge(u, v):
                return u

        candidates = [
            u for u in active_out
            if u != v and not Gc.has_edge(u, v)
        ]

        if not candidates:
            return None

        return random.choice(candidates)

    def _sample_v_for_u(u):
        if len(active_in) == 0:
            return None

        tries = min(64, max(8, len(active_in)))

        for _ in range(tries):
            v = active_in.choice()

            if v != u and not Gc.has_edge(u, v):
                return v

        candidates = [
            v for v in active_in
            if v != u and not Gc.has_edge(u, v)
        ]

        if not candidates:
            return None

        return random.choice(candidates)

    while (
        total_out > 0
        and total_in > 0
        and len(active_out) > 0
        and len(active_in) > 0
    ):

        if no_progress >= no_progress_limit:
            print(
                f"[adição] sem progresso após {no_progress} tentativas — "
                f"out_restante={total_out}, in_restante={total_in}"
            )
            break

        start_with_in = random.choice((True, False))

        if start_with_in:
            v = active_in.choice()
            u = _sample_u_for_v(v)

            if u is None:
                active_in.discard(v)
                no_progress += 1
                continue

        else:
            u = active_out.choice()
            v = _sample_v_for_u(u)

            if v is None:
                active_out.discard(u)
                no_progress += 1
                continue

        Gc.add_edge(u, v)

        no_progress = 0

        out_deficit[u] -= 1
        in_deficit[v] -= 1

        total_out -= 1
        total_in -= 1

        if out_deficit[u] == 0:
            del out_deficit[u]
            active_out.discard(u)

        if in_deficit[v] == 0:
            del in_deficit[v]
            active_in.discard(v)
    return total_out, total_in





def degree_correction_coin_uniform_nodes(
    G_synth: nx.DiGraph,
    G_orig: nx.DiGraph,
    epsilon5: float,
    out_target: Optional[Dict] = None,
    in_target: Optional[Dict] = None,
) -> nx.DiGraph:

    if out_target is None or in_target is None:
        out_target, in_target = compute_noisy_degrees(G_orig, epsilon5)

    Gc = G_synth.copy()

    nodes = list(G_orig.nodes())
    Gc.add_nodes_from(nodes)

    print(f"graus antes de tudo: {Gc.number_of_edges()}")

    out_deficit, out_excess = _split_residuals(out_target, Gc.out_degree)
    in_deficit, in_excess = _split_residuals(in_target, Gc.in_degree)

    print(
        "[degree_correction] "
        f"out_deficit={sum(out_deficit.values())}, "
        f"out_excess={sum(out_excess.values())}, "
        f"in_deficit={sum(in_deficit.values())}, "
        f"in_excess={sum(in_excess.values())}"
    )

    print("[degree_correction] iniciando fase de remoção...")

    rem_out_rest, rem_in_rest = _removal_phase(
        Gc,
        out_excess,
        in_excess
    )

    print(
        "[degree_correction] após remoção — "
        f"arestas={Gc.number_of_edges()}, "
        f"out_excess_restante={rem_out_rest}, "
        f"in_excess_restante={rem_in_rest}"
    )

    print("[degree_correction] iniciando fase de adição...")

    add_out_rest, add_in_rest = _addition_phase(
        Gc,
        nodes,
        out_deficit,
        in_deficit
    )

    print(
        "[degree_correction] após adição — "
        f"arestas={Gc.number_of_edges()}, "
        f"out_deficit_restante={add_out_rest}, "
        f"in_deficit_restante={add_in_rest}"
    )

    return Gc