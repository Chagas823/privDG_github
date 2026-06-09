from imports import * 
from pipeline import privDG
DATASET = "data/Wiki-Vote.txt"
G = nx.read_edgelist(DATASET, nodetype=int, create_using=nx.DiGraph())


N        = 10
N_RUNS   = 10 
EPSILONS = [1.0, 2.0, 4.0, 6.0]

OUTPUT_CSV  = f"results/graus_wiki_nos.csv"
OUTPUT_PLOT = f"results/graus_plot_wiki_nos.png"



output_graph_dir = "results/generated_graphs/small/wiki"
os.makedirs(output_graph_dir, exist_ok=True)

def run_evaluation(G: nx.DiGraph) -> pd.DataFrame:
 
    records = []

    for eps in EPSILONS:
        print(f" --------------------- epsilon = {eps} ---------------------")

        for run in range(1, N_RUNS + 1):
            print(f"  execução {run}/{N_RUNS} ...", end=" ", flush=True)

            G_synth = privDG(G=G, epsilon=eps, N=N, verbose=True)

            graph_path = os.path.join(
                output_graph_dir,
                f"G_synth_eps_{eps}_run_{run}.txt"
            )

            nx.write_edgelist(
                G_synth,
                graph_path,
                data=False
            )



            record = {"epsilon": eps, "run": run}
            records.append(record)

    return pd.DataFrame(records)
if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)

    print(f"loading dataset: {DATASET}")
    print(f"Grafo: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    df = run_evaluation(G)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nResultados brutos salvos em: {OUTPUT_CSV}")


