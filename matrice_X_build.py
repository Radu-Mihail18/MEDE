import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

from load_sources import load_speeds, load_graph, load_meta, SPEED_FILE, GRAPH_FILE, META_FILE

STEP = pd.Timedelta(minutes=5)
FRAC_TRAIN = 0.70          # split temporal 70/10/20 (planificat in data card)
PRAG_CONGESTIE = 0.60      # congestie = viteza < 60% din viteza "libera" a senzorului (percentila 95)
VARF_DIM = (7, 10)         # ore, zile lucratoare: 07:00-09:59
VARF_SEARA = (16, 19)      # 16:00-18:59
NOAPTE = (0, 5)            # 00:00-04:59

GRUP_ETICHETE = {
    "viteze": "Senzori (PEMS-BAY.csv)",
    "graf": "Retea (adj_mx_bay.pkl)",
    "meta": "Metadate (PEMS-BAY-META.csv)",
}


def pagerank(adj_w, d=0.85, iters=200, tol=1e-12):
    """PageRank simplu cu numpy, pe graful orientat (linia i -> coloana j), ponderi = adj."""
    n = adj_w.shape[0]
    out = adj_w.sum(axis=1)
    P = np.zeros_like(adj_w, dtype=float)
    nz = out > 0
    P[nz] = adj_w[nz] / out[nz, None]
    r = np.full(n, 1.0 / n)
    for _ in range(iters):
        dangling = r[~nz].sum() / n
        r_new = (1 - d) / n + d * (P.T @ r + dangling)
        if np.abs(r_new - r).sum() < tol:
            r = r_new
            break
        r = r_new
    return r / r.sum()


def trasaturi_viteze(speeds, n_train):
    """speeds: DataFrame (timp x senzori) pe grila completa de 5 min. Folosim doar primii n_train pasi."""
    W = speeds.iloc[:n_train].copy()
    W = W.mask(W <= 0)                      
    idx = W.index
    zi_lucr = idx.dayofweek < 5
    ora = idx.hour

    F, prov = {}, []

    def add(nume, serie, definitie, unitate):
        F[nume] = serie
        prov.append((nume, "viteze", SPEED_FILE, definitie, unitate))

    add("viteza_medie", W.mean(), "media vitezei, toate momentele valide", "mph")
    add("viteza_std", W.std(), "abaterea standard a vitezei", "mph")
    p = W.quantile([0.05, 0.50, 0.95])
    add("viteza_p05", p.loc[0.05], "percentila 5 a vitezei", "mph")
    add("viteza_p50", p.loc[0.50], "mediana vitezei", "mph")
    add("viteza_p95", p.loc[0.95], "percentila 95 a vitezei (viteza libera)", "mph")
    add("coef_variatie", W.std() / W.mean(), "abaterea standard / medie", "fara unitate")

    Wl = W[zi_lucr]
    cong = (Wl < PRAG_CONGESTIE * p.loc[0.95]).where(Wl.notna())
    add("pct_congestie", cong.mean() * 100,
        f"% din momentele zilelor lucratoare cu viteza < {int(PRAG_CONGESTIE*100)}% din percentila 95 a senzorului", "%")

    def medie_ore(mask_zi, a, b):
        m = mask_zi & (ora >= a) & (ora < b)
        return W[m].mean()

    add("viteza_varf_dim", medie_ore(zi_lucr, *VARF_DIM), "viteza medie 07:00-09:59, zile lucratoare", "mph")
    add("viteza_varf_seara", medie_ore(zi_lucr, *VARF_SEARA), "viteza medie 16:00-18:59, zile lucratoare", "mph")
    add("viteza_noapte", medie_ore(np.ones(len(W), bool), *NOAPTE), "viteza medie 00:00-04:59, toate zilele", "mph")
    add("raport_weekend", W[~zi_lucr].mean() / W[zi_lucr].mean(), "viteza medie weekend / viteza medie zile lucratoare", "fara unitate")

    # autocorelatie la 1 ora (12 pasi), pe serie cu goluri (pandas ignora perechile cu NaN)
    ac = pd.Series({c: W[c].autocorr(lag=12) for c in W.columns})
    add("autocorel_1h", ac, "autocorelatia vitezei la intarziere de 1 ora (12 pasi)", "fara unitate")

    prof = Wl.groupby(Wl.index.hour).mean()
    for h in range(24):
        add(f"prof_h{h:02d}", prof.loc[h], f"viteza medie in ora {h:02d}:00-{h:02d}:59, zile lucratoare", "mph")

    X = pd.DataFrame(F)
    P = pd.DataFrame(prov, columns=["trasatura", "grup", "fisier_sursa", "definitie", "unitate"])
    return X, P


def trasaturi_graf(adj, sensor_ids):
    A = np.array(adj, dtype=float)
    np.fill_diagonal(A, 0)
    nz = A > 0
    F = {
        "grad_iesire": nz.sum(axis=1),
        "grad_intrare": nz.sum(axis=0),
        "putere_iesire": A.sum(axis=1),
        "putere_intrare": A.sum(axis=0),
        "pagerank": pagerank(A),
    }
    defs = {
        "grad_iesire": ("numar de muchii care pleaca din senzor (linia matricei, fara diagonala)", "numar"),
        "grad_intrare": ("numar de muchii care intra in senzor (coloana matricei, fara diagonala)", "numar"),
        "putere_iesire": ("suma ponderilor muchiilor care pleaca", "fara unitate"),
        "putere_intrare": ("suma ponderilor muchiilor care intra", "fara unitate"),
        "pagerank": ("PageRank (amortizare 0,85) pe graful orientat, ponderat", "fara unitate"),
    }
    X = pd.DataFrame(F, index=sensor_ids)
    P = pd.DataFrame([(k, "graf", GRAPH_FILE, defs[k][0], defs[k][1]) for k in F],
                     columns=["trasatura", "grup", "fisier_sursa", "definitie", "unitate"])
    return X, P


def trasaturi_meta(meta, id_col, sensor_ids):
    m = meta.copy()
    m[id_col] = m[id_col].astype(str)
    m = m.set_index(id_col).loc[sensor_ids]
    F, prov = {}, []

    def add(nume, serie, definitie, unitate):
        F[nume] = serie
        prov.append((nume, "meta", META_FILE, definitie, unitate))

    for col, nume, unit in [("Latitude", "latitudine", "grade"), ("Longitude", "longitudine", "grade"),
                            ("Lanes", "benzi", "numar"), ("Length", "lungime", "mile")]:
        add(nume, pd.to_numeric(m[col], errors="coerce"), f"coloana {col} din META", unit)
    for v in sorted(m["Fwy"].dropna().unique()):
        add(f"fwy_{v}", (m["Fwy"] == v).astype(float), f"1 daca senzorul e pe autostrada/drumul {v}", "0/1")
    for v in sorted(m["Dir"].dropna().unique()):
        add(f"dir_{v}", (m["Dir"] == v).astype(float), f"1 daca directia este {v}", "0/1")
    add("tip_HV", (m["Type"] == "HV").astype(float), "1 daca tipul senzorului este HV (banda HOV); restul sunt ML", "0/1")
    X = pd.DataFrame(F)
    P = pd.DataFrame(prov, columns=["trasatura", "grup", "fisier_sursa", "definitie", "unitate"])
    return X, P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="outputs")
    a = ap.parse_args()
    data, out = Path(a.data_dir), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ---- incarcare + aliniere (aceeasi ca la CP1) ----
    speeds = load_speeds(data / SPEED_FILE)
    ids_g, id_to_ind, adj = load_graph(data / GRAPH_FILE)
    meta = load_meta(data / META_FILE)
    cols = list(speeds.columns)
    common = [s for s in ids_g if s in set(cols)]
    speeds = speeds[common]
    adj = adj[np.ix_([id_to_ind[s] for s in common], [id_to_ind[s] for s in common])]
    grid = pd.date_range(speeds.index.min(), speeds.index.max(), freq=STEP)
    speeds = speeds.reindex(grid)
    n_steps = len(grid)
    n_train = int(round(FRAC_TRAIN * n_steps))
    n_val = int(round(0.10 * n_steps))
    t_train_end = grid[n_train - 1]
    print(f"grila: {n_steps} pasi, antrenare = primii {n_train} (pana la {t_train_end})")

    best, best_n = None, 0
    for c in meta.columns:
        n = len(set(meta[c].astype(str)) & set(common))
        if n > best_n:
            best, best_n = c, n
    id_col = best

    # ---- trasaturi pe grupuri ----
    Xv, Pv = trasaturi_viteze(speeds, n_train)
    Xg, Pg = trasaturi_graf(adj, common)
    Xm, Pm = trasaturi_meta(meta, id_col, common)
    Xv.index = Xg.index = Xm.index = pd.Index(common, name="sensor_id")
    X = pd.concat([Xv, Xg, Xm], axis=1).astype(float)
    P = pd.concat([Pv, Pg, Pm], ignore_index=True)
    P["grup_eticheta"] = P["grup"].map(GRUP_ETICHETE)
    assert list(X.columns) == list(P["trasatura"])

    # ---- lipsuri: imputare cu mediana pe coloana (doar daca exista) ----
    nan_inainte = X.isna().sum()
    imputate = nan_inainte[nan_inainte > 0].to_dict()
    X = X.fillna(X.median())
    X.to_csv(out / "matrice_X.csv")

    # ---- scalare (z-score doar pe coloanele numerice, nu pe cele 0/1) ----
    binare = [c for c in X.columns if set(X[c].unique()) <= {0.0, 1.0}]
    num = [c for c in X.columns if c not in binare]
    Xs = X.copy()
    sd = X[num].std(ddof=0).replace(0, 1)
    Xs[num] = (X[num] - X[num].mean()) / sd
    Xs.to_csv(out / "matrice_X_scalata.csv")
    P["scalare"] = np.where(P["trasatura"].isin(binare), "nu (0/1)", "z-score pe 325 senzori")
    P.to_csv(out / "provenienta_trasaturi.csv", index=False)

    # ---- statistici descriptive ----
    st = X.describe(percentiles=[0.25, 0.5, 0.75]).T
    st["asimetrie"] = X.skew()
    st["lipsa_inainte_imputare"] = nan_inainte.reindex(X.columns).fillna(0).astype(int)
    st.insert(0, "grup", P.set_index("trasatura")["grup"])
    st.round(4).to_csv(out / "statistici_descriptive.csv", index_label="trasatura")

    # ---- corelatii intre surse (Spearman, pe cei 325 senzori) ----
    C = X.corr(method="spearman")
    grup = P.set_index("trasatura")["grup"]
    rows = []
    cs = list(X.columns)
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            if grup[cs[i]] != grup[cs[j]] and np.isfinite(C.iloc[i, j]):
                rows.append((cs[i], grup[cs[i]], cs[j], grup[cs[j]], C.iloc[i, j]))
    cr = pd.DataFrame(rows, columns=["trasatura_1", "grup_1", "trasatura_2", "grup_2", "rho_spearman"])
    cr["abs_rho"] = cr["rho_spearman"].abs()
    cr = cr.sort_values("abs_rho", ascending=False)
    cr.head(40).round(3).to_csv(out / "corelatii_intre_surse.csv", index=False)
    cg = (cr.assign(pereche=lambda d: d.apply(lambda r: " x ".join(sorted([r.grup_1, r.grup_2])), axis=1))
            .groupby("pereche")["abs_rho"].agg(["count", "mean", "max"]).round(3))
    cg.to_csv(out / "corelatii_pe_grupuri.csv", index_label="pereche")

    # ---- PCA pe X scalat (SVD) ----
    M = Xs.values - Xs.values.mean(axis=0)
    U, S, Vt = np.linalg.svd(M, full_matrices=False)
    var = S ** 2 / (M.shape[0] - 1)
    ev = var / var.sum()
    pca = pd.DataFrame({"componenta": np.arange(1, len(ev) + 1), "varianta_explicata": ev,
                        "varianta_cumulata": np.cumsum(ev)})
    pca.round(5).to_csv(out / "varianta_explicata_pca.csv", index=False)
    load = pd.DataFrame(Vt[:5].T, index=X.columns, columns=[f"PC{k}" for k in range(1, 6)])
    load.insert(0, "grup", grup)
    load.round(4).to_csv(out / "incarcari_pca.csv", index_label="trasatura")

    # ---- rezumat ----
    d_pe_grup = P.groupby("grup").size().to_dict()
    cum = np.cumsum(ev)
    rez = {
        "n_senzori": int(X.shape[0]), "d_trasaturi": int(X.shape[1]), "d_pe_grup": {k: int(v) for k, v in d_pe_grup.items()},
        "raport_d_la_n": round(X.shape[1] / X.shape[0], 3),
        "split": {"pasi_total": n_steps, "pasi_antrenare": n_train, "pasi_validare": n_val,
                  "pasi_test": n_steps - n_train - n_val,
                  "antrenare_pana_la": str(t_train_end), "validare_pana_la": str(grid[n_train + n_val - 1])},
        "trasaturi_imputate_cu_mediana": {k: int(v) for k, v in imputate.items()},
        "coloane_binare": len(binare), "coloane_numerice": len(num),
        "pca": {"prima_componenta": round(float(ev[0]), 4), "a_doua": round(float(ev[1]), 4),
                "primele_5_cumulat": round(float(cum[4]), 4),
                "componente_pentru_80": int(np.searchsorted(cum, 0.80) + 1),
                "componente_pentru_90": int(np.searchsorted(cum, 0.90) + 1)},
        "corelatii_pe_grupuri": cg.reset_index().to_dict("records"),
        "top_corelatii": cr.head(8).round(3).to_dict("records"),
        "pct_congestie_p25_p50_p75": [round(float(X["pct_congestie"].quantile(q)), 2) for q in (0.25, 0.5, 0.75)],
        "viteza_medie_p25_p50_p75": [round(float(X["viteza_medie"].quantile(q)), 2) for q in (0.25, 0.5, 0.75)],
    }
    (out / "rezumat_X.json").write_text(json.dumps(rez, indent=2, ensure_ascii=True), encoding="utf-8")

    # ---- figuri ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        cheie = [("viteza_medie", "viteza medie (mph)"), ("pct_congestie", "% timp in congestie"),
                 ("viteza_varf_seara", "viteza la varf seara (mph)"), ("grad_iesire", "grad de iesire"),
                 ("pagerank", "PageRank"), ("benzi", "numar de benzi")]
        fig, ax = plt.subplots(2, 3, figsize=(11, 5.5))
        for a_, (c, t) in zip(ax.ravel(), cheie):
            a_.hist(X[c], bins=30, color="#4a6fa5", edgecolor="white")
            a_.set_title(t, fontsize=10); a_.set_ylabel("senzori")
        fig.tight_layout(); fig.savefig(out / "fig_distributii.png", dpi=150); plt.close(fig)

        sel = ["viteza_medie", "viteza_std", "pct_congestie", "viteza_varf_seara", "raport_weekend", "autocorel_1h",
               "grad_iesire", "grad_intrare", "putere_iesire", "pagerank", "latitudine", "longitudine", "benzi", "lungime"]
        sel = [c for c in sel if c in C.columns]
        fig, a_ = plt.subplots(figsize=(7.5, 6.5))
        im = a_.imshow(C.loc[sel, sel].values, cmap="RdBu_r", vmin=-1, vmax=1)
        a_.set_xticks(range(len(sel))); a_.set_xticklabels(sel, rotation=60, ha="right", fontsize=8)
        a_.set_yticks(range(len(sel))); a_.set_yticklabels(sel, fontsize=8)
        fig.colorbar(im, label="corelatie Spearman"); fig.tight_layout()
        fig.savefig(out / "fig_corelatii.png", dpi=150); plt.close(fig)

        k = min(15, len(ev))
        fig, a_ = plt.subplots(figsize=(6.5, 4))
        a_.bar(range(1, k + 1), ev[:k] * 100, color="#4a6fa5")
        a_.plot(range(1, k + 1), cum[:k] * 100, "o-", color="#c0392b", label="cumulat")
        a_.set_xlabel("componenta principala"); a_.set_ylabel("varianta explicata (%)"); a_.legend()
        fig.tight_layout(); fig.savefig(out / "fig_scree.png", dpi=150); plt.close(fig)
    except ImportError:
        print("matplotlib lipseste: figurile nu s-au generat (pip install matplotlib)", file=sys.stderr)

    print(json.dumps({k: rez[k] for k in ("n_senzori", "d_trasaturi", "d_pe_grup", "pca")}, indent=2))


if __name__ == "__main__":
    main()
