"""
MEDE - U14 - Senzor de trafic (PEMS-BAY) - pipeline de incarcare si aliniere (CP1)

Incarca cele 3 surse din data/, le verifica, le aliniaza la senzor x 5 min si scrie:
  outputs/rezumat.json          valorile masurate (n senzori, perioada, goluri, graf)
  outputs/raport_acoperire.csv   acoperirea per senzor (NaN, zerouri, % valid)
  outputs/tabel_aliniat.parquet  (sau .csv.gz fara pyarrow) tabelul aliniat: o linie = senzor x timp (optional, --write-aligned)
  <datacard>.md                 blocul "Valori masurate" actualizat (optional, --update-datacard)

Rulare:
  python src/load_sources.py --data-dir data --out-dir outputs \
      --update-datacard ../datacard_U14.md --write-aligned
"""
import argparse, json, pickle, sys
from pathlib import Path
import numpy as np
import pandas as pd

SPEED_FILE, GRAPH_FILE, META_FILE = "PEMS-BAY.csv", "adj_mx_bay.pkl", "PEMS-BAY-META.csv"
STEP = pd.Timedelta(minutes=5)


def load_speeds(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    df.columns = df.columns.astype(str)
    return df.sort_index()


def load_graph(path: Path):
    with open(path, "rb") as f:
        sensor_ids, id_to_ind, adj = pickle.load(f, encoding="latin1")
    return [str(s) for s in sensor_ids], id_to_ind, np.asarray(adj)


def load_meta(path: Path) -> pd.DataFrame:
    meta = pd.read_csv(path)
    return meta


def find_id_column(meta: pd.DataFrame, ids: set):
    """Coloana din META care contine ID-urile de senzori (cea cu cea mai mare suprapunere)."""
    best, best_n = None, 0
    for c in meta.columns:
        n = len(set(meta[c].astype(str)) & ids)
        if n > best_n:
            best, best_n = c, n
    return best, best_n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--update-datacard", default=None)
    ap.add_argument("--write-aligned", action="store_true")
    a = ap.parse_args()
    data, out = Path(a.data_dir), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1) incarcare
    speeds = load_speeds(data / SPEED_FILE)
    ids_g, id_to_ind, adj = load_graph(data / GRAPH_FILE)
    meta = load_meta(data / META_FILE)

    # 2) verificari de aliniere semantica (chei)
    cols = list(speeds.columns)
    same_set = set(cols) == set(ids_g)
    same_order = cols == ids_g
    id_col, id_overlap = find_id_column(meta, set(cols))
    if not same_set:
        print("ATENTIE: ID-urile din CSV si din .pkl nu coincid:",
              len(set(cols) - set(ids_g)), "doar in CSV,", len(set(ids_g) - set(cols)), "doar in .pkl", file=sys.stderr)

    # reordonare la ordinea grafului (cheia comuna = ID senzor)
    common = [s for s in ids_g if s in set(cols)]
    speeds = speeds[common]
    keep_idx = [id_to_ind[s] for s in common]
    adj = adj[np.ix_(keep_idx, keep_idx)]

    # 3) grila temporala de 5 min si goluri
    rows_in_file = len(speeds.index.unique())
    full_idx = pd.date_range(speeds.index.min(), speeds.index.max(), freq=STEP)
    missing_steps = len(full_idx) - len(speeds.index.unique())
    speeds = speeds.reindex(full_idx)
    n_t, n_s = speeds.shape
    nan_ratio = speeds.isna().to_numpy().mean()
    zero_ratio = (speeds == 0).to_numpy().mean()
    valid = speeds.notna() & (speeds != 0)

    cov = pd.DataFrame({
        "sensor_id": speeds.columns,
        "n_steps": n_t,
        "n_nan": speeds.isna().sum().values,
        "n_zero": (speeds == 0).sum().values,
        "pct_valid": (valid.mean().values * 100).round(4),
    })
    cov.to_csv(out / "raport_acoperire.csv", index=False)
    full_rows = int(valid.all(axis=1).sum())

    # 4) graf
    nnz = int((adj != 0).sum() - np.count_nonzero(np.diag(adj)))
    summary = {
        "speeds": {"file": SPEED_FILE, "n_sensors": n_s, "n_steps": n_t, "rows_in_file": int(rows_in_file),
                   "start": str(speeds.index.min()), "end": str(speeds.index.max()),
                   "step_minutes": 5, "steps_missing_from_grid": int(missing_steps),
                   "n_observations": int(n_t * n_s),
                   "nan_pct": round(nan_ratio * 100, 4), "zero_pct": round(zero_ratio * 100, 4),
                   "min": float(np.nanmin(speeds.values)), "max": float(np.nanmax(speeds.values)),
                   "median": float(np.nanmedian(speeds.values)),
                   "rows_with_all_sensors_valid": full_rows,
                   "rows_with_all_sensors_valid_pct": round(full_rows / n_t * 100, 4)},
        "graph": {"file": GRAPH_FILE, "shape": list(adj.shape), "nnz_offdiag": nnz,
                  "symmetric": bool(np.allclose(adj, adj.T)),
                  "weight_min": float(adj.min()), "weight_max": float(adj.max()),
                  "ids_match_csv_as_set": bool(same_set), "ids_match_csv_same_order": bool(same_order)},
        "meta": {"file": META_FILE, "n_rows": int(len(meta)), "columns": list(map(str, meta.columns)),
                 "id_column": id_col, "ids_matched_to_csv": int(id_overlap)},
    }
    (out / "rezumat.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    # 5) tabelul aliniat: o linie = senzor x timp
    if a.write_aligned:
        long = (speeds.rename_axis("timestamp").reset_index()
                .melt(id_vars="timestamp", var_name="sensor_id", value_name="speed")
                .sort_values(["sensor_id", "timestamp"], ignore_index=True))
        if id_col is not None:
            m = meta.copy(); m[id_col] = m[id_col].astype(str)
            long = long.merge(m, left_on="sensor_id", right_on=id_col, how="left")
        try:
            long.to_parquet(out / "tabel_aliniat.parquet", index=False)
        except ImportError:  # fara pyarrow: CSV comprimat
            long.to_csv(out / "tabel_aliniat.csv.gz", index=False)

    # 6) bloc "Valori masurate" in data card
    s, g, m = summary["speeds"], summary["graph"], summary["meta"]
    block = f"""<!-- MEASURED:START -->
Valori calculate de load_sources.py la ultima rulare:

- senzori in CSV / in graf / potriviti: {len(cols)} / {len(ids_g)} / {len(common)} (aceeasi multime de ID-uri: {g['ids_match_csv_as_set']}, aceeasi ordine: {g['ids_match_csv_same_order']})
- perioada: {s['start']} pana la {s['end']}; grila completa are {s['n_steps']} pasi de 5 min, fisierul are {s['rows_in_file']} randuri, pasi lipsa: {s['steps_missing_from_grid']}
- observatii (senzor x timp): {s['n_observations']:,}
- goluri: NaN {s['nan_pct']} %, zerouri {s['zero_pct']} %
- viteza: min {s['min']:.1f}, mediana {s['median']:.1f}, max {s['max']:.1f}
- momente cu toti senzorii valizi: {s['rows_with_all_sensors_valid']:,} ({s['rows_with_all_sensors_valid_pct']} %)
- graf: forma {tuple(g['shape'])}, {g['nnz_offdiag']:,} muchii nenule (fara diagonala), simetric: {g['symmetric']}, ponderi intre {g['weight_min']:.4f} si {g['weight_max']:.4f}
- META: {m['n_rows']} randuri, cheie `{m['id_column']}`, {m['ids_matched_to_csv']} ID-uri potrivite cu CSV
- META, coloane: {', '.join(m['columns'])}
<!-- MEASURED:END -->"""
    if a.update_datacard:
        p = Path(a.update_datacard)
        txt = p.read_text(encoding="utf-8")
        i, j = txt.index("<!-- MEASURED:START -->"), txt.index("<!-- MEASURED:END -->") + len("<!-- MEASURED:END -->")
        p.write_text(txt[:i] + block + txt[j:], encoding="utf-8")
        print("data card actualizat:", p)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()