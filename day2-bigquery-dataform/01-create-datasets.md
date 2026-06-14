# 01 - BigQuery datasetek létrehozása

## Cél

Ebben a gyakorlatban létrehozod azokat a dataseteket, amelyek egy modern data warehouse különböző layereit képviselik.

A gyakorlat végére az alábbi datasetekkel fogsz rendelkezni:

```text
<your_name>_raw
<your_name>_stage
<your_name>_gold
```

Ezeket a dataseteket a training további részében végig használni fogjuk.

---

## Miért csináljuk ezt?

A data projectek egyik leggyakoribb hibája, hogy mindent egyetlen datasetben tárolnak.

A modern data platformok különböző layerekre választják szét az adatokat:

```text
Landing
   ↓
RAW
   ↓
STAGE
   ↓
INTERMEDIATE
   ↓
GOLD
```

Minden layernek eltérő felelősségi köre van.

| Layer | Cél |
|---------|---------|
| RAW | Eredeti adatok |
| STAGE | Technikai adattisztítás |
| INTERMEDIATE | Business logic |
| GOLD | Reporting és dashboardok |

Ma külön dataseteket használunk ezeknek a layereknek a megjelenítésére.

---

## A BigQuery Studio megnyitása

1. Nyisd meg a Google Cloud Console-t.

2. Navigálj ide:

```text
BigQuery Studio
```

3. Ellenőrizd, hogy a training projectben dolgozol:

```text
ford-training-430008
```

---

## A RAW dataset létrehozása

1. Keresd meg az Explorer panelen:

```text
ford-training-430008
```

2. Kattints a project neve melletti három pontra.

3. Válaszd ki:

```text
Create Dataset
```

4. Töltsd ki a formot:

### Dataset ID

Cseréld le a `<your_name>` értéket a saját nevedre.

Példa:

```text
janos_raw
```

### Region

Válaszd ki:

```text
europe-west4 (Netherlands)
```

vagy a trainer által megadott regiont.

### Expiration

Hagyd meg a default értékeket.

5. Kattints erre:

```text
Create Dataset
```

---

## A STAGE dataset létrehozása

Ismételd meg az előző lépéseket.

Dataset ID:

```text
<your_name>_stage
```

Példa:

```text
janos_stage
```

---

## A GOLD dataset létrehozása

Ismételd meg az előző lépéseket.

Dataset ID:

```text
<your_name>_gold
```

Példa:

```text
janos_gold
```

---

## Ellenőrzés

Az Explorer panelnek most az alábbiakat kell tartalmaznia:

```text
ford-training-430008
│
├── janos_raw
├── janos_stage
└── janos_gold
```

A te datasetneveid ettől eltérnek majd.

---

## Miért nem egyetlen datasetet használunk?

Képzelj el egy valódi production environmentet.

Ha minden table-t együtt tárolnánk:

```text
sales_raw
sales_stage
sales_gold
dealer_raw
dealer_stage
dealer_gold
```

az environment hamar nehezen áttekinthetővé válna.

A layerek külön datasetekbe választásának előnyei:

- Jobb szervezettség
- Egyszerűbb troubleshooting
- Átláthatóbb jogosultságok
- Egyszerűbb karbantartás

Ezt a megközelítést gyakran használják enterprise data platformokon.

---

## Checkpoint

Mostanra rendelkezned kell az alábbiakkal:

✓ RAW dataset

✓ STAGE dataset

✓ GOLD dataset

---

## Mi következik?

A következő gyakorlatban betöltjük a source fájlokat a RAW layerbe.

A fájlok:

```text
mli_mapping.csv
dealer_master.csv
sales_data.csv
```

Ezekből készülnek el az első BigQuery table-jeink.
