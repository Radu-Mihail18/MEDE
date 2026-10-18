# MEDE U14: congestia in reteaua rutiera (PEMS-BAY)

Script de incarcare si aliniere a datelor pentru proiectul MEDE.
Unitate de analiza: senzor de trafic x interval de 5 minute.

## Surse (CC BY 4.0, Zenodo - colectia PEMS-BAY)
| Fisier | Continut |
|---|---|
| `PEMS-BAY.csv` | viteze la 5 min, 325 senzori |
| `adj_mx_bay.pkl` | matricea de adiacenta a senzorilor (graf din distante rutiere) |
| `PEMS-BAY-META.csv` | metadate ale senzorilor |

Se descarca cele 3 fisiere in `data/` (colectia: https://zenodo.org/records/4264445).

## Rulare
Se deschide un terminal in folderul unde se afla `load_sources.py` si `datacard_U14.md`:

    cd calea\catre\folder
    python load_sources.py --data-dir data --out-dir outputs --update-datacard datacard_U14.md --write-aligned

Rezultate in `outputs/`: `rezumat.json`, `raport_acoperire.csv`, `tabel_aliniat.parquet`
(sau `tabel_aliniat.csv.gz` daca `pyarrow` nu e instalat). Scriptul actualizeaza si blocul
"Valori calculate" din `datacard_U14.md`.