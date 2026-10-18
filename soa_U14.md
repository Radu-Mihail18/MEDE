# Tabel SOA · U14 (10 articole)

Rezultatul pentru modelele de prognoză este MAE la orizont 12 (60 min) pe PEMS-BAY, **reprodus în Shao et al. (STID, CIKM 2022), Tabelul 3** (split 7:1:2). Cifrele din articolele originale pot diferi. Pentru referință, baseline-ul trivial „Historical Inertia” are MAE 3,05 în același tabel.

| # | Articol | Surse de date | Metodă de explorare | Metrică | Rezultat |
|---|---|---|---|---|---|
| 1 | Li, Yu, Shahabi, Liu (2018), *Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting*, ICLR | METR-LA, PEMS-BAY (viteze + graf din distanțe rutiere) | Convoluție de difuziune pe graf + GRU | MAE / RMSE / MAPE | MAE@60 min = 1,99 |
| 2 | Yu, Yin, Zhu (2018), *Spatio-Temporal Graph Convolutional Networks: A Deep Learning Framework for Traffic Forecasting*, IJCAI | BJER4, PeMSD7 | Convoluție de graf spectrală + convoluție temporală cauzală | MAE / RMSE / MAPE | MAE@60 min = 2,01 |
| 3 | Wu, Pan, Long, Jiang, Zhang (2019), *Graph WaveNet for Deep Spatial-Temporal Graph Modeling*, IJCAI | METR-LA, PEMS-BAY | Matrice de adiacență adaptivă, învățată din date + convoluții dilatate | MAE / RMSE / MAPE | MAE@60 min = 1,95 |
| 4 | Wu, Pan, Long, Jiang, Chang, Zhang (2020), *Connecting the Dots: Multivariate Time Series Forecasting with Graph Neural Networks*, KDD | serii multivariate, incl. METR-LA, PEMS-BAY | Învățarea structurii grafului (MTGNN) | MAE / RMSE / MAPE | MAE@60 min = 1,97 |
| 5 | Bai, Yao, Li, Wang, Wang (2020), *Adaptive Graph Convolutional Recurrent Network for Traffic Forecasting*, NeurIPS | PEMSD4, PEMSD8 | Parametri specifici nodului + graf adaptiv, fără graf predefinit | MAE / RMSE / MAPE | MAE@60 min = 1,99 |
| 6 | Zheng, Fan, Wang, Qi (2020), *GMAN: A Graph Multi-Attention Network for Traffic Prediction*, AAAI | Xiamen, PeMS (Bay Area) | Atenție spațială și temporală pe graf | MAE / RMSE / MAPE | MAE@60 min = 1,89 |
| 7 | Shao, Zhang, Wang, Wei, Xu (2022), *Spatial-Temporal Identity: A Simple yet Effective Baseline for Multivariate Time Series Forecasting*, CIKM | PEMS04/07/08, PEMS-BAY, Electricity | MLP cu embeddings de identitate spațială și temporală, fără graf | MAE / RMSE / MAPE; timp/epocă | MAE@60 min = 1,89; 15,8 s/epocă vs. 351 s la DCRNN |
| 8 | Nguyen, Liu, Chen (UrbComp 2015; IEEE Trans. Big Data 2017), *Discovering Congestion Propagation Patterns in Spatio-Temporal Traffic Data* | Timp de parcurs pe segmente, Victoria (Australia): 281 situri, 586 segmente, 4 săptămâni, 5 min | Arbori de congestie (STCTree) + subarbori frecvenți + rețea bayesiană dinamică | Frecvența subarborilor; probabilitatea de propagare | Propagare de maximum 75 min; probabilitate 2,24 % (4,26 % în ora de vârf) |
| 9 | Chen, Yang, Huang, Wang, Li (2018), *Discovering Urban Traffic Congestion Propagation Patterns with Taxi Trajectory Data* | Traiectorii de taxi Shanghai + rețeaua rutieră | Subgraf spațio-temporal de congestie (STCS) + subgrafuri frecvente, cu completarea muchiilor lipsă | Frecvența subgrafurilor (calitativ) | Subgrafurile frecvente dezvăluie tipare de propagare |
| 10 | Xiong, Zhou, Bennett (2023), *Detecting spatiotemporal propagation patterns of traffic congestion from fine-grained vehicle trajectory data*, IJGIS 37(5) | Traiectorii fine (simulare agent-based) + taxiuri reale | Dynamic Time Warping + grafuri aciclice de evenimente | Comparație cu o metodă existentă, pe date simulate | Depășește metoda existentă; agregarea la 5 min ascunde interacțiuni fine |

## Concluzii pentru proiect
- Un MLP fără graf (STID) egalează cel mai bun model cu graf (GMAN) pe PEMS-BAY: graful trebuie testat, nu presupus (comparația „per senzor vs. graf + timp”).
- Metodele de propagare (8–10) lucrează pe evenimente de congestie și pe grafuri de legături: de aici pornesc definiția de congestie (percentilă a vitezei per senzor) și alegerea pasului de 5 min.
- Articolul 10 avertizează că pasul de 5 min poate ascunde propagări rapide: devine o limitare declarată.
