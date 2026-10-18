# Data card U14: senzori de trafic (PEMS-BAY)

Unitate de analiza: senzor de trafic x interval de 5 minute.
Intrebare: congestia rutiera se propaga de la un senzor la senzorii vecini din retea sau ramane locala?

Folosesc 3 fisiere din aceeasi colectie de pe Zenodo (https://zenodo.org/records/4264445), toate sub licenta CC BY 4.0 conform paginii Zenodo. Structura fisei urmeaza cerintele din curs (provenienta, perioada, rezolutie, unitati, goluri, licenta), inspirata din datasheets for datasets si dataset cards de pe Hugging Face. Cifrele de la sectiunea "Valori calculate" vin din scriptul `load_sources.py` din repo.

## 1. PEMS-BAY.csv (viteze)

- Provenienta: detectoare cu bucla inductiva din sistemul PeMS al Caltrans (departamentul de transport din California), zona golfului San Francisco. Setul a fost pregatit de Li et al. pentru articolul DCRNN (ICLR 2018) si pus pe Zenodo.
- Perioada: 1 ianuarie 2017 00:00 pana la 30 iunie 2017 23:55. Unele articole scriu 31 mai, dar datele ajung pana pe 30 iunie.
- Rezolutie spatiala: 325 de statii fixe pe autostrazi, identificate printr-un ID de senzor.
- Rezolutie temporala: 5 minute (valori agregate din masuratori brute la 30 de secunde).
- Unitati: viteza medie in mile pe ora. In fisier nu exista debit sau ocupare, doar viteza.
- Forma: o linie pe moment de timp, o coloana pe senzor. Pe grila completa de 5 minute sunt 52.128 de pasi, deci 325 x 52.128 = 16.941.600 de observatii.
- Goluri: fisierul are 52.116 randuri, adica lipsesc 12 pasi (o ora intreaga), la toti senzorii. Pe langa asta, 0,0031 % din valori sunt zero, care ar putea fi cod de lipsa si nu viteza reala. 99,97 % din momente au toti cei 325 de senzori valizi.
- Licenta: CC BY 4.0. Datele originale apartin Caltrans PeMS.
- Limitari: doar 6 luni si o singura regiune, deci nu acopera toate anotimpurile. Avem doar viteza. Media pe 5 minute poate ascunde propagari mai rapide de atat.

## 2. adj_mx_bay.pkl (graful senzorilor)

- Provenienta: facut de autorii DCRNN din distantele rutiere dintre senzori, cu un nucleu gaussian si un prag (scriptul gen_adj_mx din repo-ul liyaguang/DCRNN). Deci e o ipoteza de vecinatate, nu ceva masurat din trafic.
- Continut: un pickle cu lista ID-urilor de senzori, dictionarul ID -> indice si matricea de adiacenta.
- Perioada: statica, nu depinde de timp.
- Rezolutie spatiala: perechi de senzori, matrice 325 x 325 cu 2.369 de muchii nenule.
- Rezolutie temporala: nu e cazul.
- Unitati: ponderi fara unitate, intre 0 si 1, care scad cu distanta rutiera.
- Goluri: nu sunt. ID-urile coincid cu cele din CSV, in aceeasi ordine. Matricea nu e simetrica, deci graful e orientat.
- Licenta: CC BY 4.0 (aceeasi inregistrare Zenodo).
- Limitari: fiind construit din distanta, daca caut propagarea direct pe el risc sa obtin un rezultat circular. De aceea il voi compara cu un graf kNN facut din corelatiile vitezelor (CP3).

## 3. PEMS-BAY-META.csv (metadate senzori)

- Provenienta: aceeasi colectie Zenodo, metadate despre statiile de masura.
- Perioada: statica.
- Rezolutie spatiala: 325 de randuri (cate unul pe senzor) si 18 coloane: sensor_id, Fwy, Dir, District, County, City, State_PM, Abs_PM, Latitude, Longitude, Length, Type, Lanes, Name, User_ID_1 pana la User_ID_4.
- Rezolutie temporala: nu e cazul.
- Unitati: coordonate geografice (Latitude, Longitude), lungime, numar de benzi, autostrada si directie.
- Goluri: toate cele 325 de ID-uri din CSV au rand in META.
- Licenta: CC BY 4.0.
- Limitari: sunt doar descrieri ale statiilor, nu masuratori de trafic.

## Valori calculate
<!-- MEASURED:START -->
Valori calculate de load_sources.py la ultima rulare:

- senzori in CSV / in graf / potriviti: 325 / 325 / 325 (aceeasi multime de ID-uri: True, aceeasi ordine: True)
- perioada: 2017-01-01 00:00:00 pana la 2017-06-30 23:55:00; grila completa are 52128 pasi de 5 min, fisierul are 52116 randuri, pasi lipsa: 12
- observatii (senzor x timp): 16,941,600
- goluri: NaN 0.023 %, zerouri 0.0031 %
- viteza: min 0.0, mediana 65.3, max 85.1
- momente cu toti senzorii valizi: 52,112 (99.9693 %)
- graf: forma (325, 325), 2,369 muchii nenule (fara diagonala), simetric: False, ponderi intre 0.0000 si 1.0000
- META: 325 randuri, cheie `sensor_id`, 325 ID-uri potrivite cu CSV
- META, coloane: sensor_id, Fwy, Dir, District, County, City, State_PM, Abs_PM, Latitude, Longitude, Length, Type, Lanes, Name, User_ID_1, User_ID_2, User_ID_3, User_ID_4
<!-- MEASURED:END -->
