# PrivDG: Differentially Private Directed Graph Publishing

Framework for publishing directed graphs under edge differential privacy guarantees. Combines private community detection, intra-community synthesis via the exponential mechanism (LEVEL), and inter-community reconstruction with degree correction.

> Chagas et al., EDBT 2026 — [GitHub](https://github.com/Chagas823/privDG_github)

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

The main entry point is `main.py`.

```python
import networkx as nx
from pipeline import privDG

G = nx.read_edgelist("your_graph.txt", create_using=nx.DiGraph())

G_private = privDG(
    G,
    epsilon=2.0,  
    N=10,         
    verbose=True,
)
```

---

## Parameters

| Parameter | Description | Default in experiments |
|-----------|-------------|------------------------|
| `epsilon` | Total privacy budget ε | 1.0, 2.0, 4.0, 6.0 |
| `N` | Supernode size (Phase 1) | 10 |
| `verbose` | Print phase logs | `False` |