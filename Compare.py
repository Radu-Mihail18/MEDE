
import argparse, json, sys, warnings
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE, trustworthiness
from sklearn.neighbors import NearestNeighbors

from load_sources import load_speeds, load_graph, load_meta, SPEED_FILE, GRAPH_FILE, META_FILE
from matrice_X_build import (trasaturi_viteze, trasaturi_graf, trasaturi_meta, STEP, FRAC_TRAIN,
                            PRAG_CONGESTIE, VARF_DIM, VARF_SEARA)

K = 10                 # vecini pentru trustworthiness si pentru suprapunerea de vecini
N_REP = 10             # repetari pe esantioane de 80% din senzori
FRAC_ESANTION = 0.80
SEEDURI_TSNE = [0, 1, 2, 3, 4]
PERPLEXITATE = 30

# sarbatori federale SUA in perioada datelor (ianuarie - iunie 2017), sursa: calendarul OPM
SARBATORI = ["2017-01-02", "2017-01-16", "2017-02-20", "2017-05-29"]


def trasaturi_evenimente(speeds, n_train):
    """Efectul zilelor speciale (sarbatori, weekend) asupra vitezei fiecarui senzor, doar pe antrenare."""
    W = speeds.iloc[:n_train]
    W = W.mask(W <= 0)
    idx = W.index
    ora = idx.hour
    sarb = np.isin(idx.normalize(), pd.to_datetime(SARBATORI))
    weekend = idx.dayofweek >= 5
    normal = ~weekend & ~sarb
    p95 = W.quantile(0.95)

    def medie(mask_zi, a, b):
        return W[mask_zi & (ora >= a) & (ora < b)].mean()

    def congestie(mask_zi):
        Z = W[mask_zi & (ora >= 6) & (ora < 20)]
        return ((Z < PRAG_CONGESTIE * p95).where(Z.notna())).mean() * 100

    F = {
        "efect_sarb_dim": medie(sarb, *VARF_DIM) - medie(normal, *VARF_DIM),
        "efect_sarb_seara": medie(sarb, *VARF_SEARA) - medie(normal, *VARF_SEARA),
        "efect_sarb_zi": medie(sarb, 6, 20) - medie(normal, 6, 20),
        "dif_congestie_sarb": congestie(sarb) - congestie(normal),
        "efect_weekend_dim": medie(weekend, *VARF_DIM) - medie(normal, *VARF_DIM),
        "efect_weekend_seara": medie(weekend, *VARF_SEARA) - medie(normal, *VARF_SEARA),
    }
    defs = {
        "efect_sarb_dim": ("viteza medie 07:00-09:59 in zilele de sarbatoare minus aceeasi medie in zilele lucratoare normale", "mph"),
        "efect_sarb_seara": ("viteza medie 16:00-18:59 in zilele de sarbatoare minus zilele lucratoare normale", "mph"),
        "efect_sarb_zi": ("viteza medie 06:00-19:59 in zilele de sarbatoare minus zilele lucratoare normale", "mph"),
        "dif_congestie_sarb": ("% congestie (06:00-19:59) in zilele de sarbatoare minus zilele lucratoare normale", "puncte procentuale"),
        "efect_weekend_dim": ("viteza medie 07:00-09:59 in weekend minus zilele lucratoare normale", "mph"),
        "efect_weekend_seara": ("viteza medie 16:00-18:59 in weekend minus zilele lucratoare normale", "mph"),
    }
    n_sarb = int(pd.Series(idx.normalize()[sarb]).nunique())
    X = pd.DataFrame(F)
    P = pd.DataFrame([(k, "evenimente", "calendar (sarbatori federale SUA 2017) + " + SPEED_FILE, defs[k][0], defs[k][1]) for k in F],
                     columns=["trasatura", "grup", "fisier_sursa", "definitie", "unitate"])
    return X, P, n_sarb


def scaleaza(X):
    """z-score pe coloanele numerice; coloanele 0/1 raman neschimbate (ca la CP2)."""
    X = X.astype(float).fillna(X.median())
    binare = [c for c in X.columns if set(X[c].unique()) <= {0.0, 1.0}]
    num = [c for c in X.columns if c not in binare]
    Z = X.copy()
    sd = X[num].std(ddof=0).replace(0, 1)
    Z[num] = (X[num] - X[num].mean()) / sd
    return Z.values


def pca2(Z):
    p = PCA(n_components=2).fit(Z)
    E = p.transform(Z)
    rec = p.inverse_transform(E)
    zc = Z - Z.mean(axis=0)
    err = float(((Z - rec) ** 2).sum() / (zc ** 2).sum())      # eroare relativa de reconstructie
    return E, float(p.explained_variance_ratio_.sum()), err


def tsne2(Z, seed):
    perp = min(PERPLEXITATE, (Z.shape[0] - 1) // 3)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return TSNE(n_components=2, perplexity=perp, init="random", learning_rate="auto",
                    random_state=seed).fit_transform(Z)


def vecini(E, k=K):
    nn = NearestNeighbors(n_neighbors=k + 1).fit(E)
    return nn.kneighbors(E, return_distance=False)[:, 1:]


def suprapunere(E1, E2, k=K):
    """Cat din cei k vecini ai fiecarui senzor in E1 sunt vecini si in E2 (medie, 0-1)."""
    a, b = vecini(E1, k), vecini(E2, k)
    return float(np.mean([len(set(x) & set(y)) / k for x, y in zip(a, b)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out-dir", default="outputs")
    a = ap.parse_args()
    data, out = Path(a.data_dir), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ---- incarcare si aliniere (la fel ca la CP1 / CP2) ----
    speeds = load_speeds(data / SPEED_FILE)
    ids_g, id_to_ind, adj = load_graph(data / GRAPH_FILE)
    meta = load_meta(data / META_FILE)
    common = [s for s in ids_g if s in set(speeds.columns)]
    speeds = speeds[common]
    adj = adj[np.ix_([id_to_ind[s] for s in common], [id_to_ind[s] for s in common])]
    grid = pd.date_range(speeds.index.min(), speeds.index.max(), freq=STEP)
    speeds = speeds.reindex(grid)
    n_train = int(round(FRAC_TRAIN * len(grid)))
    id_col = max(meta.columns, key=lambda c: len(set(meta[c].astype(str)) & set(common)))

    # ---- blocurile de trasaturi ----
    Xv, _ = trasaturi_viteze(speeds, n_train)
    Xg, _ = trasaturi_graf(adj, common)
    Xm, _ = trasaturi_meta(meta, id_col, common)
    Xe, Pe, n_sarb = trasaturi_evenimente(speeds, n_train)
    for X in (Xv, Xg, Xm, Xe):
        X.index = pd.Index(common, name="sensor_id")
    pd.concat([Xv, Xg, Xm, Xe], axis=1).astype(float).to_csv(out / "matrice_X_extinsa.csv")
    Pe.to_csv(out / "provenienta_evenimente.csv", index=False)

    seturi = {
        "viteze": Xv, "graf": Xg, "metadate": Xm, "evenimente": Xe,
        "combinat fara evenimente": pd.concat([Xv, Xg, Xm], axis=1),
        "combinat cu evenimente": pd.concat([Xv, Xg, Xm, Xe], axis=1),
    }
    Z = {k: scaleaza(v) for k, v in seturi.items()}
    n = len(common)

    # ---- tabelul principal: PCA vs t-SNE, cu intervale pe esantioane de 80% ----
    rows, proiectii = [], {}
    for nume, z in Z.items():
        E_pca, var2, err = pca2(z)
        t_pca_full = trustworthiness(z, E_pca, n_neighbors=K)
        E_ts = tsne2(z, 0)
        t_ts_full = trustworthiness(z, E_ts, n_neighbors=K)
        proiectii[nume] = (E_pca, E_ts)
        tp, tt, vv = [], [], []
        for rep in range(N_REP):
            rng = np.random.default_rng(rep)
            sel = np.sort(rng.choice(n, size=int(FRAC_ESANTION * n), replace=False))
            zs = z[sel]
            Ep, v, _ = pca2(zs)
            tp.append(trustworthiness(zs, Ep, n_neighbors=K))
            tt.append(trustworthiness(zs, tsne2(zs, rep), n_neighbors=K))
            vv.append(v)
        rows.append({
            "sursa": nume, "d": z.shape[1],
            "pca_varianta_2comp": var2, "pca_eroare_reconstructie": err,
            "pca_trust": t_pca_full, "tsne_trust": t_ts_full,
            "pca_trust_medie": np.mean(tp), "pca_trust_std": np.std(tp, ddof=1),
            "tsne_trust_medie": np.mean(tt), "tsne_trust_std": np.std(tt, ddof=1),
            "diferenta_medie": np.mean(np.array(tt) - np.array(tp)),
            "diferenta_std": np.std(np.array(tt) - np.array(tp), ddof=1),
            "pca_varianta_std": np.std(vv, ddof=1),
        })
        print(f"{nume}: PCA trust {np.mean(tp):.3f}, t-SNE trust {np.mean(tt):.3f}")
    T = pd.DataFrame(rows)
    T.round(4).to_csv(out / "tabel_principal.csv", index=False)

    # ---- stabilitate la seed (t-SNE, toti senzorii) ----
    rs = []
    for nume, z in Z.items():
        embs = [tsne2(z, s) for s in SEEDURI_TSNE]
        ov = [suprapunere(e1, e2) for e1, e2 in combinations(embs, 2)]
        tr = [trustworthiness(z, e, n_neighbors=K) for e in embs]
        rs.append({"sursa": nume, "vecini_pastrati_medie": np.mean(ov), "vecini_pastrati_min": np.min(ov),
                   "trust_medie": np.mean(tr), "trust_std": np.std(tr, ddof=1)})
    S = pd.DataFrame(rs)
    S.round(4).to_csv(out / "stabilitate_seeduri.csv", index=False)

    # ---- stabilitate pe subperioade (cele 2 jumatati ale antrenarii) ----
    h = n_train // 2
    Xv1, _ = trasaturi_viteze(speeds.iloc[:h], h)
    Xv2, _ = trasaturi_viteze(speeds.iloc[h:n_train], n_train - h)
    for X in (Xv1, Xv2):
        X.index = Xg.index
    perioade = {
        "viteze": (Xv1, Xv2),
        "combinat fara evenimente": (pd.concat([Xv1, Xg, Xm], axis=1), pd.concat([Xv2, Xg, Xm], axis=1)),
    }
    rp = []
    for nume, (A, B) in perioade.items():
        za, zb = scaleaza(A), scaleaza(B)
        rp.append({"sursa": nume, "metoda": "spatiul initial (fara reducere)", "vecini_pastrati": suprapunere(za, zb)})
        rp.append({"sursa": nume, "metoda": "PCA", "vecini_pastrati": suprapunere(pca2(za)[0], pca2(zb)[0])})
        ov = [suprapunere(tsne2(za, s), tsne2(zb, s)) for s in SEEDURI_TSNE]
        rp.append({"sursa": nume, "metoda": "t-SNE", "vecini_pastrati": np.mean(ov), "std_pe_seeduri": np.std(ov, ddof=1)})
    Pp = pd.DataFrame(rp)
    Pp.round(4).to_csv(out / "stabilitate_subperioade.csv", index=False)

    # ---- legatura cu intrebarea: vecinii din proiectia vitezelor sunt vecini si in graf? ----
    A = np.array(adj, dtype=float)
    np.fill_diagonal(A, 0)
    und = (A > 0) | (A.T > 0)
    sansa = float(und.sum() / (n * (n - 1)))
    def in_graf(E):
        v = vecini(E)
        return float(np.mean([und[i, v[i]].mean() for i in range(n)]))
    graf_vs = {"sansa_intamplare": sansa,
               "pca_viteze": in_graf(proiectii["viteze"][0]), "tsne_viteze": in_graf(proiectii["viteze"][1]),
               "spatiu_initial_viteze": float(np.mean([und[i, vecini(Z["viteze"])[i]].mean() for i in range(n)]))}

    # ---- rezumat ----
    rez = {
        "n_senzori": n, "k_vecini": K, "repetari": N_REP, "esantion": FRAC_ESANTION,
        "seeduri_tsne": SEEDURI_TSNE, "perplexitate": PERPLEXITATE,
        "antrenare_pana_la": str(grid[n_train - 1]), "jumatate_antrenare_la": str(grid[h - 1]),
        "sarbatori_in_antrenare": n_sarb,
        "tabel_principal": T.round(4).to_dict("records"),
        "stabilitate_seeduri": S.round(4).to_dict("records"),
        "stabilitate_subperioade": Pp.round(4).to_dict("records"),
        "vecini_din_proiectie_care_sunt_vecini_in_graf": {k: round(v, 4) for k, v in graf_vs.items()},
    }
    (out / "rezumat_reprezentari.json").write_text(json.dumps(rez, indent=2, ensure_ascii=True), encoding="utf-8")

    # ---- figuri ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        dirs = meta.assign(**{id_col: meta[id_col].astype(str)}).set_index(id_col).loc[common, "Dir"].values
        culori = {"N": "#c0392b", "S": "#2c6fbb", "E": "#27ae60", "W": "#8e44ad"}
        fig, ax = plt.subplots(2, 2, figsize=(10, 8.5))
        for r, nume in enumerate(["viteze", "combinat cu evenimente"]):
            for c, (met, E) in enumerate(zip(["PCA", "t-SNE"], proiectii[nume])):
                for dname, col in culori.items():
                    m = dirs == dname
                    ax[r, c].scatter(E[m, 0], E[m, 1], s=14, color=col, label=f"directia {dname}", alpha=0.8)
                ax[r, c].set_title(f"{met} - {nume}", fontsize=10)
                ax[r, c].set_xticks([]); ax[r, c].set_yticks([])
        ax[0, 0].legend(fontsize=8)
        fig.tight_layout(); fig.savefig(out / "fig_proiectii.png", dpi=150); plt.close(fig)

        fig, a_ = plt.subplots(figsize=(8.5, 4.2))
        x = np.arange(len(T)); w = 0.38
        a_.bar(x - w / 2, T["pca_trust_medie"], w, yerr=T["pca_trust_std"], label="PCA", color="#4a6fa5", capsize=3)
        a_.bar(x + w / 2, T["tsne_trust_medie"], w, yerr=T["tsne_trust_std"], label="t-SNE", color="#c0392b", capsize=3)
        a_.set_xticks(x); a_.set_xticklabels(T["sursa"], rotation=20, ha="right", fontsize=8)
        a_.set_ylabel(f"trustworthiness (k = {K})"); a_.set_ylim(0.5, 1.0); a_.legend()
        fig.tight_layout(); fig.savefig(out / "fig_trustworthiness.png", dpi=150); plt.close(fig)
    except ImportError:
        print("matplotlib lipseste: figurile nu s-au generat (pip install matplotlib)", file=sys.stderr)

    print(json.dumps(rez["vecini_din_proiectie_care_sunt_vecini_in_graf"], indent=2))


if __name__ == "__main__":
    main()
