# 02 - RAW table-ök betöltése

## Cél

Ebben a gyakorlatban betöltöd a source fájlokat a data warehouse RAW layerébe.

A gyakorlat végére az alábbi table-ökkel fogsz rendelkezni:

```text
<your_name>_raw.mli_mapping
<your_name>_raw.dealer_master
<your_name>_raw.sales_data
```

Ezek a table-ök lesznek a Dataform pipeline kiindulópontjai.

---

## Miért csináljuk ezt?

Tegnap megtanultuk, hogyan érkeznek meg a fájlok a Cloud Storage-ba.

Ma a warehouse oldalára koncentrálunk.

Egy valós solutionben a Cloud Run automatikusan betöltené a fájlokat.

A mai gyakorlatban manuálisan végezzük el a betöltést, hogy az alábbiakra összpontosíthassunk:

- BigQuery
- Warehouse layers
- Dataform

anélkül, hogy további componenteket vezetnénk be.

A célunk annak az állapotnak a szimulálása, amelyben az ingestion process már sikeresen befejeződött.

---

# Source fájlok

Az alábbi fájlokat kellett megkapnod:

```text
mli_mapping.csv
dealer_master.csv
sales_data.csv
```

Ezek a fájlok a következőket tartalmazzák:

| Fájl | Leírás |
|--------|--------|
| mli_mapping.csv | Product classification mapping |
| dealer_master.csv | Dealer master data |
| sales_data.csv | Sales transactionök |

---

# Az mli_mapping.csv betöltése

## 1. lépés

Nyisd meg:

```text
BigQuery Studio
```

---

## 2. lépés

Nyisd le a RAW datasetedet.

Példa:

```text
janos_raw
```

---

## 3. lépés

Kattints erre:

```text
Create Table
```

---

## 4. lépés

Konfiguráld a source-t.

### Create table from

Válaszd ki:

```text
Upload
```

### Select file

Válaszd ki:

```text
mli_mapping.csv
```

---

## 5. lépés

Konfiguráld a destinationt.

### Dataset

Válaszd ki:

```text
<your_name>_raw
```

### Table Name

```text
mli_mapping
```

---

## 6. lépés

Konfiguráld a schemát.

Válaszd ki:

```text
Auto detect
```

A BigQuery automatikusan meghatározza:

- a column neveket
- a column type-okat

---

## 7. lépés

Kattints erre:

```text
Create Table
```

Várd meg, amíg befejeződik a table létrehozása.

---

## Ellenőrzés

Nyisd meg a table-t.

Válaszd ki:

```text
Preview
```

Az alábbihoz hasonló adatokat kell látnod:

| MLI | Basket | PCT | MPL_Code |
|------|------|------|------|
| 1000 | Engine | A | MPL_000 |
| 1001 | Parts | B | MPL_001 |

---

# A dealer_master.csv betöltése

Ismételd meg ugyanezt a folyamatot.

### File

```text
dealer_master.csv
```

### Table Name

```text
dealer_master
```

---

## Ellenőrzés

Tekintsd meg a table Preview-ját.

Példaadatok:

| Market | DealerCode | DealerName |
|---------|---------|---------|
| HU | D00001 | Dealer_1 |
| NL | D00002 | Dealer_2 |

---

# A sales_data.csv betöltése

Ismételd meg ugyanezt a folyamatot.

### File

```text
sales_data.csv
```

### Table Name

```text
sales_data
```

---

## Ellenőrzés

Tekintsd meg a table Preview-ját.

Példaadatok:

| Market | DealerCode | MLI | Month | Qty | Revenue |
|---------|---------|---------|---------|---------|---------|
| HU | D00001 | 1000 | 1 | 10 | 1000 |

---

# Az összes table ellenőrzése

A RAW datasetednek most az alábbiakat kell tartalmaznia:

```text
<your_name>_raw
│
├── mli_mapping
├── dealer_master
└── sales_data
```

Példa:

```text
janos_raw
│
├── mli_mapping
├── dealer_master
└── sales_data
```

---

# Miért RAW?

Figyeld meg, hogy még nem:

- neveztük át a columnokat
- tisztítottuk meg az adatokat
- joinoltuk a table-öket
- alkalmaztunk business logicot

A RAW layernek a lehető legközelebb kell maradnia az eredeti source-hoz.

Ennek előnyei:

- reprodukálhatóság
- auditálhatóság
- egyszerűbb troubleshooting
- egyszerűbb reprocessing

A következő layerek tartalmazzák majd a tényleges transformationöket.

---

# Checkpoint

Mostanra rendelkezned kell az alábbiakkal:

✓ mli_mapping table

✓ dealer_master table

✓ sales_data table

a RAW dataseteden belül.

---

# Mi következik?

A következő gyakorlatban SQL segítségével megvizsgáljuk az adatokat, és megismerkedünk a table-ök tartalmával, mielőtt felépítjük a Dataform modelleket.
