# Tabel SOA U14 (10 articole)

Articolele 1-7 sunt despre prognoza vitezei pe grafuri de trafic. Articolele 8-10 sunt despre propagarea congestiei, adica exact intrebarea mea. La 1-7 rezultatul este MAE la 60 de minute pe PEMS-BAY (in mph), luat din Tabelul 3 al articolului STID (Shao et al., 2022), unde toate modelele sunt comparate pe acelasi split (70/10/20). Cifrele din articolele originale pot fi usor diferite (vezi nota de mai jos). Pentru comparatie, un baseline banal (Historical Inertia) are MAE 3,05 in acelasi tabel.

| # | Articol | Surse de date | Metoda de explorare | Metrica | Rezultat | Link |
|---|---|---|---|---|---|---|
| 1 | Li, Yu, Shahabi, Liu (2018), Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting, ICLR | METR-LA, PEMS-BAY (viteze + graf din distante rutiere) | convolutie de difuziune pe graf + GRU | MAE, RMSE, MAPE | MAE la 60 min = 1,99 | arXiv: https://arxiv.org/abs/1707.01926 |
| 2 | Yu, Yin, Zhu (2018), Spatio-Temporal Graph Convolutional Networks: A Deep Learning Framework for Traffic Forecasting, IJCAI | BJER4, PeMSD7 | convolutie de graf spectrala + convolutie temporala | MAE, RMSE, MAPE | MAE la 60 min = 2,01 | arXiv: https://arxiv.org/abs/1709.04875 |
| 3 | Wu, Pan, Long, Jiang, Zhang (2019), Graph WaveNet for Deep Spatial-Temporal Graph Modeling, IJCAI | METR-LA, PEMS-BAY | matrice de adiacenta invatata din date + convolutii dilatate | MAE, RMSE, MAPE | MAE la 60 min = 1,95 | arXiv: https://arxiv.org/abs/1906.00121 |
| 4 | Wu, Pan, Long, Jiang, Chang, Zhang (2020), Connecting the Dots: Multivariate Time Series Forecasting with Graph Neural Networks, KDD | serii multivariate, printre care METR-LA si PEMS-BAY | invata si structura grafului (MTGNN) | MAE, RMSE, MAPE | MAE la 60 min = 1,97 | arXiv: https://arxiv.org/abs/2005.11650 |
| 5 | Bai, Yao, Li, Wang, Wang (2020), Adaptive Graph Convolutional Recurrent Network for Traffic Forecasting, NeurIPS | PEMSD4, PEMSD8 | parametri separati pe nod + graf adaptiv, fara graf dat | MAE, RMSE, MAPE | MAE la 60 min = 1,99 | arXiv: https://arxiv.org/abs/2007.02842 |
| 6 | Zheng, Fan, Wang, Qi (2020), GMAN: A Graph Multi-Attention Network for Traffic Prediction, AAAI | Xiamen, PeMS (Bay Area) | atentie spatiala si temporala pe graf | MAE, RMSE, MAPE | MAE la 60 min = 1,89 | arXiv: https://arxiv.org/abs/1911.08415 |
| 7 | Shao, Zhang, Wang, Wei, Xu (2022), Spatial-Temporal Identity: A Simple yet Effective Baseline for Multivariate Time Series Forecasting, CIKM | PEMS04, PEMS07, PEMS08, PEMS-BAY, Electricity | MLP cu embeddings pentru senzor si moment al zilei, fara graf | MAE, RMSE, MAPE, timp pe epoca | MAE la 60 min = 1,89; 15,8 s pe epoca fata de 351 s la DCRNN | arXiv: https://arxiv.org/abs/2208.05233 |
| 8 | Nguyen, Liu, Chen (UrbComp 2015; IEEE Trans. on Big Data 2017), Discovering Congestion Propagation Patterns in Spatio-Temporal Traffic Data | timpi de parcurs pe segmente, Victoria (Australia): 281 de situri, 586 de segmente, 4 saptamani, pas de 5 min | arbori de congestie + subarbori frecventi + retea bayesiana dinamica | frecventa subarborilor, probabilitate de propagare | propagare de maximum 75 min; probabilitate 2,24 % (4,26 % in ora de varf) | PDF (UTS): https://opus.lib.uts.edu.au/bitstream/10453/116769/4/7AB8B032-DEDF-4F45-9E2A-54CA6E39D3D1%20am.pdf |
| 9 | Chen, Yang, Huang, Wang, Li (2018), Discovering Urban Traffic Congestion Propagation Patterns with Taxi Trajectory Data, IEEE Access | traiectorii de taxi din Shanghai + reteaua rutiera | subgraf spatio-temporal de congestie + subgrafuri frecvente, cu completarea muchiilor lipsa | frecventa subgrafurilor (evaluare calitativa) | subgrafurile frecvente arata tipare de propagare | DOI: https://doi.org/10.1109/ACCESS.2018.2881039 (IEEE Access) |
| 10 | Xiong, Zhou, Bennett (2023), Detecting spatiotemporal propagation patterns of traffic congestion from fine-grained vehicle trajectory data, IJGIS 37(5) | traiectorii fine din simulare + taxiuri reale | Dynamic Time Warping + grafuri aciclice de evenimente | comparatie cu o metoda existenta, pe date simulate | depaseste metoda existenta; spune ca pasul de 5 min ascunde interactiuni fine | DOI: https://doi.org/10.1080/13658816.2023.2178653 |

## Atentie: de unde vin cifrele si sursele (important)

La randurile 1-7, coloana "Surse de date" arata pe ce date a fost testat articolul ORIGINAL (de exemplu STGCN pe BJER4 si PeMSD7, AGCRN pe PEMSD4 si PEMSD8). Coloana "Rezultat" este insa MAE la 60 min pe PEMS-BAY, luat din Tabelul 3 din STID, unde autorii au rulat toate modelele pe acelasi split. Deci la STGCN, AGCRN si GMAN cifra nu vine din articolul lor, ci din reproducerea din STID. Trebuie spus asta si la prezentare.

## Cum verifici tu fiecare rand

1. Deschide linkul din ultima coloana (arXiv sau DOI) si verifica titlul, autorii si anul.
2. La randurile 1-6: cauta in articol sectiunea "Experiments" / "Datasets" si verifica ce seturi de date folosesc (coloana "Surse").
3. La randurile 1-7: deschide articolul STID (arXiv 2208.05233), Tabelul 3, coloana PEMS-BAY, linia "Horizon 3 / 60 min", si verifica MAE-ul fiecarui model (1,99 / 2,01 / 1,95 / 1,97 / 1,99 / 1,89 / 1,89). Verifica si baseline-ul Historical Inertia (3,05).
4. La randul 8: in PDF cauta "281 sites", "75 minutes", "2.24%", "4.26%". Articolul din PDF e varianta acceptata a versiunii IEEE din 2017; anul 2015 este de la workshop-ul UrbComp.
5. La randul 9: linkul DOI te duce la articol. Revista (IEEE Access) am dedus-o din prefixul DOI "ACCESS", asa ca confirma pe pagina IEEE. Volumul si paginile nu le am, completeaza-le daca le vrei.
6. La randul 10: pe pagina DOI verifica volumul 37, numarul 5, paginile 1157-1179 si abstractul (DTW, grafuri aciclice, 5 minute).
7. Cauta fiecare titlu si pe Google Scholar ca sa vezi ca exista si ca poti copia citarea oficiala.

## Ce retin pentru proiect

- Un model fara graf (STID) ajunge la acelasi MAE ca cel mai bun model cu graf (GMAN), deci nu pot presupune ca graful aduce informatie in plus. Il voi testa: comparatia per senzor vs. graf + timp.
- Articolele 8-10 lucreaza pe evenimente de congestie, nu pe prognoza. De acolo iau ideea de a defini congestia printr-un prag (o percentila a vitezei fiecarui senzor) si de a urmari cum trece de la un senzor la vecinii lui.
- Articolul 10 spune ca un pas de 5 minute poate ascunde propagari rapide. O sa trec asta la limitari.
