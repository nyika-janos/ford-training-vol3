# 07 - A GOLD layer és data quality checkek létrehozása

## Cél

Ebben a gyakorlatban létrehozzuk a warehouse végső reporting layerét.

A GOLD layer business-ready adatokat tartalmaz, amelyeket közvetlenül használhat:

- Power BI
- Excel
- Looker
- Reporting applicationök
- Downstream data productok

A gyakorlat végére rendelkezünk majd az alábbival:

```text
<your_name>_gold.sales_gold
```

valamint az első automatizált Dataform data quality checkjeinkkel.

---

# Mi a GOLD layer?

A GOLD layer az adatok végleges verzióját képviseli.

A RAW vagy STAGE table-ökkel ellentétben a GOLD table-öket business consumptionre tervezzük.

Egy GOLD table:

- egyértelmű business meaninggel rendelkezik
- könnyen queryzhető
- elrejti a technikai komplexitást
- aggregált és enriched adatokat tartalmaz

A folyamatban elfoglalt helye:

```text
RAW
↓
STAGE
↓
INTERMEDIATE
↓
GOLD
↓
Business userek
```

---

# Mi NEM kerülhet a GOLD layerbe?

A business usereknek nem kell ismerniük az alábbiakat:

```text
DealerCode
MLI
Source File Names
Technical Keys
```

Ehelyett az alábbiakat kell látniuk:

```text
Market
Basket
Revenue
Quantity
```

A GOLD layer a technikai adatokat business data-vá alakítja.

---

# A jelenlegi warehouse áttekintése

Jelenleg az alábbiakkal rendelkezünk:

```text
RAW
├── sales_data
├── dealer_master
└── mli_mapping

STAGE
├── sales_stage
├── dealer_stage
├── mapping_stage
└── sales_enriched
```

Ma ezt hozzuk létre:

```text
GOLD
└── sales_gold
```

---

# A sales_gold.sqlx megnyitása

Navigálj ide:

```text
definitions/sales_gold.sqlx
```

Ez a model hozza létre a végső reporting table-t.

---

# A configuration block áttekintése

A fájl tetején az alábbit kell látnod:

```sql
config {
  type: "table",
  schema: require("../includes/config").gold_dataset,
  name: "sales_gold",

  assertions: {
    nonNull: ["Market", "Basket"],
    uniqueKey: ["Market", "Basket"]
  }
}
```

Itt több fontos concept is megjelenik.

---

# Miért használunk külön datasetet?

Figyeld meg:

```sql
schema: require("../includes/config").gold_dataset
```

Egy ilyen nevű user esetén:

```text
janos
```

a table itt jön létre:

```text
janos_gold
```

Így a reporting table-ök elkülönülnek a staging és transformation table-öktől.

---

# A source table áttekintése

Keresd meg:

```sql
FROM ${ref("sales_enriched")}
```

Ismét ezt használjuk:

```text
ref()
```

a hardcode-olt tablenevek helyett.

A Dataform automatikusan kezeli a dependencyket.

---

# Az aggregation logic áttekintése

A GOLD table az alábbiak szerint groupolja az adatokat:

```sql
Market,
Basket
```

és kiszámítja:

```sql
SUM(Qty)
SUM(Revenue)
COUNT(*)
```

Az eredmény:

```text
Market
Basket
Total_Qty
Total_Revenue
Transaction_Count
```

---

# Miért aggregálunk?

A source table transaction-level adatokat tartalmaz.

A business usereknek általában nincs szükségük minden egyes transactionre.

Ehelyett ilyen summarykra van szükségük:

```text
Revenue by Market
Revenue by Product Group
Quantity by Basket
```

A GOLD layer pontosan ezt a fajta információt készíti elő.

---

# Az output columnok áttekintése

A végső GOLD table az alábbiakat tartalmazza:

```text
Market
Basket
Total_Qty
Total_Revenue
Transaction_Count
```

Figyeld meg, hogy az alábbiak:

```text
DealerCode
MLI
DealerName
Month
```

már nem szerepelnek benne.

Ezek a részletek hasznosak a processinghez, de ehhez a reporthoz nem szükségesek.

---

# Mik az assertionök?

A következő section:

```sql
assertions: {
  nonNull: ["Market", "Basket"],
  uniqueKey: ["Market", "Basket"]
}
```

Az assertionök automatizált data quality checkek.

A model minden futtatásakor végrehajtódnak.

---

# Miért van szükség data quality checkekre?

Without validation:

```text
Hibás adatok
↓
Power BI
↓
Hibás reportok
↓
Hibás döntések
```

With validation:

```text
Hibás adatok
↓
Assertion failure
↓
A pipeline leáll
```

A problémákat így sokkal korábban észleljük.

---

# A nonNull megértése

Az első assertion:

```sql
nonNull: ["Market", "Basket"]
```

jelentése:

```text
A Marketnek mindig tartalmaznia kell értéket
A Basketnek mindig tartalmaznia kell értéket
```

Ha NULL érték jelenik meg, a Dataform sikertelenre állítja az executiont.

---

# A uniqueKey megértése

A második assertion:

```sql
uniqueKey: ["Market", "Basket"]
```

jelentése:

```text
Minden Market + Basket kombináció
csak egyszer szerepelhet.
```

Példák:

Érvényes:

```text
HU | SUV
HU | Parts
NL | SUV
```

Érvénytelen:

```text
HU | SUV
HU | SUV
```

A második példa validation failure-t eredményezne.

---

# Honnan származnak ezek a checkek?

Korábban manuálisan vizsgáltuk az alábbiakat:

```sql
COUNT(*)

COUNT(DISTINCT ...)

NULL checks
```

a data profiling során.

Most automatizáljuk ezeket a checkeket.

Pontosan így fejlődnek az érett warehouse projectek.

---

# A model compile-olása

Kattints erre:

```text
Compile
```

A modelnek sikeresen kell compile-olódnia.

---

# A Dependency Graph áttekintése

Nyisd meg:

```text
Lineage
```

Most az alábbit kell látnod:

```text
sales_stage
      ↓

dealer_stage
      ↓

mapping_stage
      ↓

sales_enriched
      ↓

sales_gold
```

Most már a teljes transformation flow látható.

---

# A sales_gold futtatása

Futtasd:

```text
sales_gold
```

Várd meg, amíg az execution befejeződik.

---

# A GOLD dataset ellenőrzése

Navigálj ide:

```text
BigQuery Studio
```

Nyisd meg:

```text
<your_name>_gold
```

Az alábbit kell látnod:

```text
sales_gold
```

---

# Az eredmények vizsgálata

Futtasd:

```sql
SELECT *
FROM `<your_name>_gold.sales_gold`
ORDER BY Total_Revenue DESC
LIMIT 20;
```

Tekintsd át:

- Market
- Basket
- Total_Qty
- Total_Revenue
- Transaction_Count

Ez most már egy reporting-ready table.

---

# Az egyediség validálása

Futtasd:

```sql
SELECT
    Market,
    Basket,
    COUNT(*) cnt
FROM `<your_name>_gold.sales_gold`
GROUP BY
    Market,
    Basket
HAVING COUNT(*) > 1;
```

Várt eredmény:

```text
0 rows
```

Ez megerősíti az egyediségre vonatkozó feltételezést.

---

# A NULL értékek validálása

Futtasd:

```sql
SELECT *
FROM `<your_name>_gold.sales_gold`
WHERE Market IS NULL
   OR Basket IS NULL;
```

Várt eredmény:

```text
0 rows
```

Ez megerősíti a non-null feltételezést.

---

# Összehasonlítás az Alteryxszel

Az imént implementált logic az alábbival egyenértékű:

```text
Input
↓
Join
↓
Formula
↓
Summarize
↓
Output
```

egy Alteryx workflow-ban.

A különbség az, hogy a Dataform:

- követi a dependencyket
- mindent Gitben tárol
- automatizált testinget végez
- dokumentálja a lineage-et

---

# Miért fontos ez a Power BI számára?

A legtöbb reporting toolnak ehhez kell csatlakoznia:

```text
GOLD
```

nem ehhez:

```text
RAW
```

és általában ehhez sem:

```text
STAGE
```

A GOLD layer contractként szolgál a data team és a business userek között.

---

# Checkpoint

Mostanra rendelkezned kell az alábbiakkal:

✓ sales_gold

✓ Automatizált assertionök

✓ Reporting-ready dataset

✓ Aggregált business metrikák

✓ Teljes warehouse lineage

✓ End-to-end Dataform pipeline

---

# Mi következik?

Ma manuálisan töltöttük be a CSV-fájlokat, majd a Dataform segítségével transformáltuk őket.

Holnap automatizáljuk az ingestion processt.

A fájlok BigQuerybe történő manuális betöltése helyett:

```text
Excel File
      ↓
Cloud Storage
      ↓
Cloud Run
      ↓
RAW
      ↓
Dataform
      ↓
GOLD
```

A warehouse architecture pontosan ugyanaz marad.

Csak az ingestion layer válik automatizálttá.
