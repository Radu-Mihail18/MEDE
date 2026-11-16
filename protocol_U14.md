# Protocolul de comparare a reprezentarilor - U14 (CP3)

Document despre cum am comparat PCA (baseline) cu t-SNE pe matricea X a senzorilor PEMS-BAY: ce se compara, cu ce metrici, cum am verificat stabilitatea si ce a iesit. Numerele sunt produse de `Compare.py` (folderul `outputs/`).

## Ce se compara

- Metode: PCA (baseline liniar) si t-SNE (metoda neliniara aleasa). Ambele reduc la 2 dimensiuni.
- Date: fiecare sursa separat (viteze, graf, metadate, evenimente) si datele combinate, o data fara blocul de evenimente (58 de coloane, ca la CP2) si o data cu el (64 de coloane).
- De ce t-SNE: X are doar 325 de linii, deci t-SNE ruleaza in cateva secunde, este in scikit-learn (fara biblioteci in plus) si pastreaza vecinatatile locale, exact ce masoara trustworthiness.
- Setari t-SNE: perplexitate 30, initializare aleatoare, 2 dimensiuni. Scalare: z-score pe coloanele numerice, coloanele 0/1 neschimbate (la fel ca la CP2).

## Sursa noua: evenimente (calendar)

Am adaugat calendarul ca sursa externa: sarbatorile federale din SUA din ianuarie - iunie 2017 (2 ian., 16 ian., 20 feb., 29 mai) si zilele de weekend. In perioada de antrenare intra 3 zile de sarbatoare. Din calendar si viteze rezulta 6 trasaturi pe senzor:

| Trasatura | Definitie | Unitate |
|---|---|---|
| efect_sarb_dim | viteza medie 07:00-09:59 in zilele de sarbatoare minus aceeasi medie in zilele lucratoare normale | mph |
| efect_sarb_seara | viteza medie 16:00-18:59 in zilele de sarbatoare minus zilele lucratoare normale | mph |
| efect_sarb_zi | viteza medie 06:00-19:59 in zilele de sarbatoare minus zilele lucratoare normale | mph |
| dif_congestie_sarb | % congestie (06:00-19:59) in zilele de sarbatoare minus zilele lucratoare normale | puncte procentuale |
| efect_weekend_dim | viteza medie 07:00-09:59 in weekend minus zilele lucratoare normale | mph |
| efect_weekend_seara | viteza medie 16:00-18:59 in weekend minus zilele lucratoare normale | mph |

Limita: sunt putine zile de sarbatoare, iar trasaturile se calculeaza tot din viteze, deci blocul nu este complet independent. Meteo (NOAA ISD) sau incidentele CHP raman de adaugat.

## Metrici

| Metrica | La ce metoda | Ce arata |
|---|---|---|
| Varianta explicata de primele 2 componente | PCA | cat din informatie ramane in 2 dimensiuni |
| Eroarea relativa de reconstructie | PCA | cat se pierde cand refac datele din cele 2 componente (0 = nimic, 1 = tot) |
| Trustworthiness, k = 10 | PCA si t-SNE | daca vecinii din proiectie erau vecini si in datele initiale (1 = perfect) |

t-SNE nu are transformare inversa, deci nu are varianta explicata sau eroare de reconstructie. De aceea metrica de comparatie intre cele doua metode este trustworthiness.

## Stabilitate

- Intervale: 10 repetari; fiecare foloseste un esantion de 80% din senzori ales cu alt seed (0-9), iar t-SNE porneste cu acelasi seed. Raportez media si abaterea standard.
- Seed-uri: t-SNE rulat cu 5 seed-uri (0-4) pe toti senzorii; masor cat din cei 10 vecini ai fiecarui senzor se pastreaza intre doua rulari.
- Subperioade: trasaturile din viteze calculate separat pe cele doua jumatati ale antrenarii (pana la 2017-03-05 08:20:00 si dupa); masor cat din cei 10 vecini se pastreaza intre jumatati. Graful si metadatele nu depind de timp.
- Split: toate trasaturile dependente de timp folosesc doar antrenarea (pana la 2017-05-07 16:45:00); validarea si testul raman neatinse.

## Tabelul principal (medie +/- abatere standard pe 10 esantioane)

| Sursa | d | PCA: varianta 2 comp. | PCA: eroare reconstructie | Trustworthiness PCA | Trustworthiness t-SNE | Diferenta (t-SNE - PCA) |
|---|---|---|---|---|---|---|
| viteze | 36 | 68,0% | 0,32 | 0,879 +/- 0,005 | 0,978 +/- 0,003 | +0,099 +/- 0,004 |
| graf | 5 | 82,8% | 0,17 | 0,980 +/- 0,002 | 0,985 +/- 0,001 | +0,005 +/- 0,002 |
| metadate | 17 | 52,9% | 0,47 | 0,891 +/- 0,007 | 0,988 +/- 0,003 | +0,096 +/- 0,008 |
| evenimente | 6 | 93,2% | 0,07 | 0,981 +/- 0,002 | 0,988 +/- 0,001 | +0,007 +/- 0,002 |
| combinat fara evenimente | 58 | 53,8% | 0,46 | 0,855 +/- 0,005 | 0,958 +/- 0,005 | +0,103 +/- 0,008 |
| combinat cu evenimente | 64 | 52,8% | 0,47 | 0,861 +/- 0,007 | 0,958 +/- 0,006 | +0,097 +/- 0,005 |

Varianta si eroarea de reconstructie sunt calculate pe toti cei 325 de senzori.

## Stabilitate la seed (t-SNE, 5 seed-uri, toti senzorii)

| Sursa | Vecini pastrati (medie) | Vecini pastrati (minim) | Trustworthiness (medie +/- abatere) |
|---|---|---|---|
| viteze | 0,83 | 0,78 | 0,981 +/- 0,002 |
| graf | 0,97 | 0,97 | 0,986 +/- 0,000 |
| metadate | 0,95 | 0,93 | 0,992 +/- 0,001 |
| evenimente | 0,95 | 0,92 | 0,989 +/- 0,001 |
| combinat fara evenimente | 0,75 | 0,70 | 0,963 +/- 0,003 |
| combinat cu evenimente | 0,76 | 0,71 | 0,966 +/- 0,002 |

## Stabilitate pe subperioade (cele 2 jumatati ale antrenarii)

| Sursa | Metoda | Vecini pastrati |
|---|---|---|
| viteze | spatiul initial (fara reducere) | 0,50 |
| viteze | PCA | 0,34 |
| viteze | t-SNE | 0,41 +/- 0,01 |
| combinat fara evenimente | spatiul initial (fara reducere) | 0,61 |
| combinat fara evenimente | PCA | 0,34 |
| combinat fara evenimente | t-SNE | 0,43 +/- 0,01 |

## Legatura cu intrebarea (graful)

Am verificat daca senzorii cu profil de viteza asemanator sunt vecini si in graf. Din cei 10 cei mai apropiati senzori dupa trasaturile de viteza, 17,3% sunt vecini in graf (in proiectia t-SNE 14,9%, in proiectia PCA 8,5%). La intamplare ar fi 4,0%.

## Ce reiese

- Pe viteze, metadate si pe datele combinate, t-SNE pastreaza vecinatatile mai bine decat PCA cu aproximativ 0,10 la trustworthiness, iar diferenta e mult peste abaterea dintre esantioane.
- Pe graf si pe evenimente (5 si 6 trasaturi) PCA este aproape la fel de bun: 2 componente explica deja 83% si 93% din varianta.
- Blocul de evenimente nu schimba calitatea reprezentarii combinate (t-SNE: aceeasi valoare cu si fara).
- Proiectiile nu sunt foarte stabile in timp: intre cele doua jumatati ale antrenarii se pastreaza 34% (PCA) si 41-43% (t-SNE) din vecini; chiar si fara reducere, doar 50-61%.
- t-SNE depinde de seed la nivel de vecini (75-83% pastrati pe viteze si combinat), dar trustworthiness aproape nu se schimba.

## Limite

- t-SNE nu poate proiecta senzori noi si distantele mari din proiectie nu se interpreteaza; il folosesc doar pentru vecinatati.
- Datele combinate sunt dominate de blocul de viteze (36 din 64 de coloane); o ponderare pe bloc ramane de testat.
- Sursa externa este deocamdata doar calendarul; comparatia completa cu si fara meteo/evenimente se face cand adaug meteo NOAA sau incidente CHP.

## Cum se reproduce

```
pip install scikit-learn matplotlib
python Compare.py --data-dir data --out-dir outputs
```
(din folderul in care sunt `load_sources.py` si `matrice_X_build.py` si data/)