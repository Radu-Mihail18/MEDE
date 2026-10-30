# Matricea X - U14 (CP2)

Document despre matricea X: ce contine, cum s-au adus cele 3 surse la aceeasi unitate si acelasi pas de timp, de unde vine fiecare trasatura si ce arata statisticile. Numerele sunt cele produse de `construieste_X.py` (folderul `outputs/`), pe datele PEMS-BAY.

## Forma matricei

- Unitate (linie): un senzor. n = 325.
- Coloane: d = 58 trasaturi, grupate pe sursa: viteze 36, retea (graf) 5, metadate 17.
- Raportul d / n = 0,18. Din cele 58 coloane, 13 sunt 0/1 (autostrada, directie, tip) si 45 sunt numerice.
- Fisiere: `matrice_X.csv` (nescalat), `matrice_X_scalata.csv`, `provenienta_trasaturi.csv` (definitia fiecarei trasaturi).

## Cum s-au adus sursele la aceeasi unitate si acelasi pas de timp

| Pas | Ce am facut |
|---|---|
| Unitate | senzorul (cheia `sensor_id`); cele 325 de ID-uri sunt aceleasi, in aceeasi ordine, in CSV, in .pkl si in META |
| Grila de timp | pasul nativ de 5 minute, fara reesantionare; grila completa are 52128 de pasi (1 ian. - 30 iun. 2017); cei 12 pasi lipsa din fisier sunt adaugati ca NaN |
| Perioada folosita | doar antrenarea: primii 36490 de pasi, pana la 2017-05-07 16:45:00 (70%). Validarea (5213 pasi, pana la 2017-05-25 19:10:00) si testul (10425 pasi) nu sunt folosite la trasaturi, ca sa nu apara leakage |
| Agregare | seria de 5 minute a fiecarui senzor devine o linie in X: medie, abatere standard, percentile, medie pe ore (zile lucratoare), medie la varf dimineata (07-10) si seara (16-19), noaptea (00-05), raport weekend / zile lucratoare, autocorelatie la 1 ora |
| Interpolare | nu se interpoleaza. Mediile si percentilele ignora valorile lipsa |
| Goluri | zerourile din viteze (0,0031%) sunt tratate ca lipsa; NaN-urile (0,023%) raman NaN. Dupa agregare nicio trasatura nu a ramas fara valoare, deci nu s-a imputat nimic |
| Retea | trasaturile din graf se calculeaza din matricea 325 x 325, fara diagonala; graful e orientat si ponderat |
| Metadate | se leaga prin `sensor_id`; autostrada si directia devin coloane 0/1 |
| Scalare | z-score (media si abaterea standard pe cei 325 de senzori) pe coloanele numerice; coloanele 0/1 raman neschimbate |

## Trasaturile, pe sursa

### Senzori

Fisier sursa: `PEMS-BAY.csv`

| Trasatura | Definitie | Unitate |
|---|---|---|
| viteza_medie | media vitezei, toate momentele valide | mph |
| viteza_std | abaterea standard a vitezei | mph |
| viteza_p05 | percentila 5 a vitezei | mph |
| viteza_p50 | mediana vitezei | mph |
| viteza_p95 | percentila 95 a vitezei (viteza libera) | mph |
| coef_variatie | abaterea standard / medie | fara unitate |
| pct_congestie | % din momentele zilelor lucratoare cu viteza < 60% din percentila 95 a senzorului | % |
| viteza_varf_dim | viteza medie 07:00-09:59, zile lucratoare | mph |
| viteza_varf_seara | viteza medie 16:00-18:59, zile lucratoare | mph |
| viteza_noapte | viteza medie 00:00-04:59, toate zilele | mph |
| raport_weekend | viteza medie weekend / viteza medie zile lucratoare | fara unitate |
| autocorel_1h | autocorelatia vitezei la intarziere de 1 ora (12 pasi) | fara unitate |
| prof_h00 ... prof_h23 | viteza medie pe fiecare ora a zilei (24 de coloane), zile lucratoare | mph |

### Retea

Fisier sursa: `adj_mx_bay.pkl`

| Trasatura | Definitie | Unitate |
|---|---|---|
| grad_iesire | numar de muchii care pleaca din senzor (linia matricei, fara diagonala) | numar |
| grad_intrare | numar de muchii care intra in senzor (coloana matricei, fara diagonala) | numar |
| putere_iesire | suma ponderilor muchiilor care pleaca | fara unitate |
| putere_intrare | suma ponderilor muchiilor care intra | fara unitate |
| pagerank | PageRank (amortizare 0,85) pe graful orientat, ponderat | fara unitate |

### Metadate

Fisier sursa: `PEMS-BAY-META.csv`

| Trasatura | Definitie | Unitate |
|---|---|---|
| latitudine | coloana Latitude din META | grade |
| longitudine | coloana Longitude din META | grade |
| benzi | coloana Lanes din META | numar |
| lungime | coloana Length din META | mile |
| fwy_17 | 1 daca senzorul e pe autostrada/drumul 17 | 0/1 |
| fwy_85 | 1 daca senzorul e pe autostrada/drumul 85 | 0/1 |
| fwy_87 | 1 daca senzorul e pe autostrada/drumul 87 | 0/1 |
| fwy_101 | 1 daca senzorul e pe autostrada/drumul 101 | 0/1 |
| fwy_237 | 1 daca senzorul e pe autostrada/drumul 237 | 0/1 |
| fwy_280 | 1 daca senzorul e pe autostrada/drumul 280 | 0/1 |
| fwy_680 | 1 daca senzorul e pe autostrada/drumul 680 | 0/1 |
| fwy_880 | 1 daca senzorul e pe autostrada/drumul 880 | 0/1 |
| dir_E | 1 daca directia este E | 0/1 |
| dir_N | 1 daca directia este N | 0/1 |
| dir_S | 1 daca directia este S | 0/1 |
| dir_W | 1 daca directia este W | 0/1 |
| tip_HV | 1 daca tipul senzorului este HV (banda HOV); restul sunt ML | 0/1 |

Pragul de congestie (60% din viteza libera a senzorului) este o alegere a mea si se schimba din constanta `PRAG_CONGESTIE` din script. Nu am folosit `Abs_PM` (kilometrajul nu se compara intre autostrazi diferite).

## Statistici descriptive (trasaturile numerice, fara profilul orar)

| Trasatura | Medie | Abatere std. | Q1 | Mediana | Q3 | Min | Max | Asimetrie |
|---|---|---|---|---|---|---|---|---|
| viteza_medie | 62,74 | 2,59 | 61,03 | 62,87 | 64,65 | 53,61 | 68,07 | -0,44 |
| viteza_std | 8,38 | 3,49 | 5,76 | 8,10 | 10,98 | 1,01 | 17,92 | 0,27 |
| viteza_p05 | 43,15 | 13,68 | 31,60 | 44,30 | 55,70 | 12,50 | 65,00 | -0,28 |
| viteza_p50 | 65,39 | 2,13 | 63,90 | 65,50 | 66,80 | 56,30 | 70,70 | -0,46 |
| viteza_p95 | 68,60 | 1,68 | 67,80 | 68,70 | 69,50 | 63,70 | 73,10 | -0,05 |
| coef_variatie | 0,14 | 0,06 | 0,09 | 0,13 | 0,18 | 0,02 | 0,32 | 0,38 |
| pct_congestie | 6,79 | 5,72 | 2,01 | 5,44 | 11,06 | 0,00 | 25,49 | 0,77 |
| viteza_varf_dim | 55,27 | 10,69 | 47,77 | 59,40 | 63,68 | 25,87 | 69,44 | -0,89 |
| viteza_varf_seara | 52,50 | 13,68 | 42,99 | 58,26 | 63,65 | 16,91 | 70,61 | -0,78 |
| viteza_noapte | 66,46 | 2,03 | 65,44 | 66,71 | 67,60 | 59,08 | 71,49 | -0,52 |
| raport_weekend | 1,06 | 0,04 | 1,03 | 1,06 | 1,09 | 0,96 | 1,24 | 1,04 |
| autocorel_1h | 0,68 | 0,10 | 0,62 | 0,69 | 0,75 | 0,30 | 0,86 | -0,60 |
| grad_iesire | 7,29 | 4,06 | 5,00 | 7,00 | 9,00 | 0,00 | 22,00 | 0,74 |
| grad_intrare | 7,29 | 4,19 | 5,00 | 7,00 | 10,00 | 0,00 | 22,00 | 0,51 |
| putere_iesire | 4,09 | 2,33 | 2,62 | 3,78 | 5,33 | 0,00 | 11,56 | 0,79 |
| putere_intrare | 4,09 | 2,31 | 2,63 | 3,82 | 5,59 | 0,00 | 11,73 | 0,42 |
| pagerank | 0,0031 | 0,0031 | 0,0016 | 0,0023 | 0,0036 | 0,0005 | 0,0310 | 4,61 |
| latitudine | 37,34 | 0,05 | 37,32 | 37,34 | 37,39 | 37,25 | 37,43 | -0,29 |
| longitudine | -121,94 | 0,07 | -122,00 | -121,92 | -121,88 | -122,08 | -121,84 | -0,54 |
| benzi | 3,59 | 0,84 | 3,00 | 4,00 | 4,00 | 1,00 | 6,00 | 0,20 |
| lungime | 0,55 | 0,41 | 0,33 | 0,46 | 0,60 | 0,05 | 2,89 | 3,24 |

Coloanele 0/1 (numar de senzori): fwy_17 = 12, fwy_85 = 70, fwy_87 = 44, fwy_101 = 68, fwy_237 = 18, fwy_280 = 44, fwy_680 = 29, fwy_880 = 40, dir_E = 7, dir_N = 156, dir_S = 151, dir_W = 11, tip_HV = 2.

Observatii: 12 senzori nu au muchii care pleaca din ei si 17 nu au muchii care intra; `lungime` si `pagerank` au distributii cu coada lunga (asimetrie mare); `pct_congestie` are asimetrie pozitiva (majoritatea senzorilor se congestioneaza rar, cativa des).

Histogramele celor 6 trasaturi principale sunt in `fig_distributii.png`.

## Corelatii intre surse (Spearman, pe cei 325 de senzori)

| Perechea de surse | Perechi de trasaturi | Medie din valorile absolute | Maxim (valoare absoluta) |
|---|---|---|---|
| graf x meta | 85 | 0,112 | 0,431 |
| graf x viteze | 180 | 0,071 | 0,181 |
| meta x viteze | 612 | 0,119 | 0,770 |

Cele mai mari 5 corelatii intre trasaturi din surse diferite:

- prof_h17 (viteze) cu dir_N (meta): rho = 0,770
- prof_h18 (viteze) cu dir_N (meta): rho = 0,768
- viteza_varf_seara (viteze) cu dir_N (meta): rho = 0,768
- prof_h16 (viteze) cu dir_N (meta): rho = 0,739
- viteza_varf_seara (viteze) cu dir_S (meta): rho = -0,716

Citire: profilul de viteza depinde mult de directia senzorului (seara sunt mai lenti cei spre nord, dimineata cei spre sud), si aproape deloc de pozitia in graf (cea mai mare corelatie intre un indicator din graf si o trasatura de viteza este 0,181). Gradul si puterea din graf sunt legate mai mult de lungimea segmentului (rho = -0,431 pentru `putere_intrare`), ceea ce sugereaza ca graful din distante rutiere reflecta in parte geometria retelei. Asta confirma riscul din CP1, ca graful nu aduce neaparat informatie noua.

Matricea completa si rezumatul pe grupuri: `corelatii_intre_surse.csv`, `corelatii_pe_grupuri.csv`, `fig_corelatii.png`.

## Prima proiectie PCA (pe X scalat)

- PC1 explica 31,6% din varianta, PC2 22,2%; primele 5 componente 78,2%.
- Pentru 80% din varianta sunt necesare 6 componente, pentru 90% sunt necesare 11.
- PC1 (nivelul general al vitezei): viteza_p50 (-0,24), viteza_medie (-0,24), prof_h21 (-0,23), prof_h22 (-0,23).
- PC2 (scaderea de la varful de seara): viteza_varf_seara (-0,27), prof_h16 (-0,27), prof_h18 (-0,27), prof_h17 (-0,27).
- Primele componente sunt dominate de grupul de viteze (36 din 58 de coloane, puternic corelate intre ele). In primele 15 incarcari (ca valoare absoluta) ale lui PC1 si PC2 apar doar trasaturi de viteza, niciuna din graf sau din metadate. Trasaturile din graf apar abia la PC4 (6,4% din varianta): putere_intrare (-0,41), grad_intrare (-0,38), putere_iesire (-0,36), grad_iesire (-0,35), impreuna cu lungimea segmentului (+0,33). Figura: `fig_scree.png`; tabele: `varianta_explicata_pca.csv`, `incarcari_pca.csv`.
- Alternativa declarata: PCA doar pe grupul de viteze, ca sa vad cat adauga graful si metadatele (urmeaza la CP3).

## Limite

- X are o linie per senzor (n = 325). Propagarea congestiei cere dependenta in timp intre senzori vecini, care nu apare intr-un X static. De aceea, la CP3 trec la perechi de senzori si intarzieri.
- Cele 24 de medii orare sunt puternic corelate, deci d = 58 are mai putine directii independente decat arata; PCA arata asta.
- Pragul de congestie (60%) si intervalele de varf sunt alegeri de lucru; trebuie testate in sensibilitate.
- Trasaturile din viteze folosesc doar perioada de antrenare; valorile pot diferi usor daca se schimba punctul de taiere.

## Cum se reproduce

```
python construieste_X.py --data-dir data --out-dir outputs
```
(din folderul in care sunt `load_sources.py` si `construieste_X.py`; fisierele sursa sunt in `data/`)