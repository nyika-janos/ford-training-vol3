# 08 - A teljes Dataform pipeline futtatása

## Cél

Ebben az utolsó gyakorlatban end-to-end futtatjuk a teljes warehouse pipeline-t.

A cél az alábbiak megértése:

- execution order
- dependencyk
- lineage
- assertionök
- monitoring

A gyakorlat végére egy teljesen működő Dataform pipeline-nal rendelkezel, amely a RAW adatokat reporting-ready GOLD table-lé alakítja.

---

# Mit építettünk fel?

Az előző gyakorlatok során az alábbiakat hoztuk létre:

```text
RAW
├── sales_data
├── dealer_master
└── mli_mapping

        ↓

STAGE
├── sales_stage
├── dealer_stage
├── mapping_stage
└── sales_enriched

        ↓

GOLD
└── sales_gold
```

Ez már egy valós cloud data warehouse egyszerűsített változata.

---

# Miért futtatjuk a teljes pipeline-t?

Eddig különálló modelleket futtattunk.

Production environmentekben általában ezt futtatjuk:

```text
A teljes pipeline
```

az egyes table-ök helyett.

Ez biztosítja:

- a helyes execution ordert
- a dependency managementet
- a data quality validationt
- a reprodukálhatóságot

---

# A Dataform megnyitása

Navigálj ide:

```text
Dataform
```

Nyisd meg:

```text
<your_name>_training_dataform
```

és válaszd ki a:

```text
development
```

workspace-t.

---

# A repository áttekintése

Ellenőrizd, hogy léteznek-e az alábbi fájlok:

```text
definitions/

├── sales_stage.sqlx
├── dealer_stage.sqlx
├── mapping_stage.sqlx
├── sales_enrich.sqlx
└── sales_gold.sqlx

includes/

└── config.js
```

---

# A workflow_settings.yaml áttekintése

Nyisd meg:

```text
workflow_settings.yaml
```

Ellenőrizd, hogy megfelelően van-e konfigurálva a username-ed.

Példa:

```yaml
vars:
  username: "janos"
```

vagy:

```yaml
vars:
  username: "barni"
```

Ez a setting határozza meg, hogy a Dataform mely dataseteket használja.

---

# A generált datasetek áttekintése

Ne feledd, hogy a username automatikusan generálja az alábbiakat:

```text
<username>_raw
<username>_stage
<username>_gold
```

Például:

```text
janos_raw
janos_stage
janos_gold
```

Ezek a nevek az alábbiakon keresztül jönnek létre:

```text
workflow_settings.yaml
```

és

```text
includes/config.js
```

---

# A repository compile-olása

Kattints erre:

```text
Compile
```

A repositorynak sikeresen kell compile-olódnia.

Ha a compilation sikertelen:

- ellenőrizd a `workflow_settings.yaml` fájlt
- ellenőrizd a username-et
- ellenőrizd, hogy minden SQLX-fájl megtalálható-e
- ellenőrizd, hogy létezik-e az `includes/config.js`

---

# A Dependency Graph áttekintése

Nyisd meg:

```text
Lineage
```

vagy

```text
Dependency Graph
```

Az alábbihoz hasonlót kell látnod:

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

---

# A Dependency Graph megértése

Figyeld meg, hogy a:

```text
sales_gold
```

ettől függ:

```text
sales_enriched
```

amely az alábbiaktól függ:

```text
sales_stage
dealer_stage
mapping_stage
```

Ezeket a dependencyket az alábbi statementek automatikusan hozták létre:

```sql
${ref("...")}
```

Nem volt szükség manuális dependency configurationre.

---

# Miért fontos ez?

Képzelj el egy warehouse-t, amely ennyi table-t tartalmaz:

```text
50 tables
100 tables
500 tables
```

A dependencyk manuális követése lehetetlenné válik.

A Dataform ezt automatikusan kezeli.

---

# Pipeline execution indítása

Kattints erre:

```text
Start Execution
```

---

# Execution mode kiválasztása

Válaszd ki:

```text
Run all actions
```

Ez arra utasítja a Dataformot, hogy futtassa a teljes transformation pipeline-t.

---

# Execution indítása

Kattints erre:

```text
Start Execution
```

A Dataform most automatikusan:

1. Felépíti a STAGE modelleket
2. Felépíti a `sales_enriched` modelt
3. Felépíti a `sales_gold` modelt
4. Futtatja az assertionöket

---

# Az Execution Graph megfigyelése

Figyeld az execution folyamatát.

Az alábbihoz hasonlót kell látnod:

```text
sales_stage
dealer_stage
mapping_stage
        ↓
sales_enriched
        ↓
sales_gold
        ↓
assertions
```

Figyeld meg, hogy a Dataform automatikusan meghatározza a helyes execution ordert.

---

# Az execution részleteinek áttekintése

Nyisd meg az execution details oldalt.

Figyeld meg:

- execution duration
- execution order
- model status
- assertion status

Ez az információ rendkívül hasznos a troubleshooting során.

---

# A sikeres befejezés ellenőrzése

Minden objectnek ezt kell mutatnia:

```text
SUCCESS
```

Ha minden sikeresen befejeződött:

✓ A pipeline lefutott

✓ Az assertionök sikeresek

✓ A GOLD table frissült

---

# A STAGE dataset ellenőrzése

Navigálj ide:

```text
BigQuery Studio
```

Nyisd meg:

```text
<your_name>_stage
```

Ellenőrizd, hogy léteznek-e az alábbi table-ök:

```text
sales_stage
dealer_stage
mapping_stage
sales_enriched
```

---

# A GOLD dataset ellenőrzése

Nyisd meg:

```text
<your_name>_gold
```

Ellenőrizd, hogy a:

```text
sales_gold
```

létezik-e.

---

# A végeredmények áttekintése

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

Ezek business-facing metrikák.

---

# Az assertionök áttekintése

Nyisd meg:

```text
definitions/sales_gold.sqlx
```

Tekintsd át:

```sql
assertions: {
  nonNull: ["Market", "Basket"],
  uniqueKey: ["Market", "Basket"]
}
```

Ne feledd:

Ezek a validationök automatikusan lefutnak a model minden futtatásakor.

---

# Mi történik, ha egy assertion sikertelen?

Képzeld el, hogy holnap az alábbi érték:

```text
Basket = NULL
```

megjelenik a GOLD table-ben.

A Dataform folyamata:

```text
Assertion futtatása
        ↓
Sikertelen assertion
        ↓
Sikertelen execution
```

A problémát még azelőtt észleljük, hogy a hibás adat elérné a reporting toolokat.

---

# Miért fontos ez?

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

# Összehasonlítás az Alteryxszel

Gondolj a training elején áttekintett workflow-kra.

Az Alteryxben:

```text
Input
 ↓
Select
 ↓
Formula
 ↓
Join
 ↓
Summarize
 ↓
Output
```

A GCP-ben:

```text
RAW
 ↓
STAGE
 ↓
INTERMEDIATE
 ↓
GOLD
```

az alábbiakon keresztül implementálva:

```text
BigQuery
+
Dataform
```

A business logic szinte azonos.

Az implementation approach eltérő.

---

# Mit tanultunk ma?

Ma az alábbiakat tanultuk:

✓ BigQuery warehouse structure

✓ RAW layer

✓ STAGE layer

✓ INTERMEDIATE layer

✓ GOLD layer

✓ Dataform repositoryk

✓ Dataform modellek

✓ `ref()` dependencyk

✓ Lineage

✓ Assertionök

✓ Automatizált data quality validation

---

# Végső architecture

Sikeresen felépítetted az alábbit:

```text
CSV Files
      ↓

RAW Tables
      ↓

STAGE Models
      ↓

sales_enriched
      ↓

sales_gold
      ↓

Power BI / Excel
```

Ugyanezt az architectural patternt használja számos modern cloud data platform.

---

# Előretekintés

Ma manuálisan töltöttük be a source fájlokat.

Holnap automatizáljuk az ingestion processt.

A CSV-fájlok BigQuerybe történő manuális feltöltése helyett:

```text
Excel File
      ↓
Cloud Storage
      ↓
Cloud Run
      ↓
RAW Tables
      ↓
Dataform
      ↓
GOLD Tables
```

A ma felépített Dataform pipeline változatlan marad.

Csak az ingestion process válik automatizálttá.

A felelősségi körök ilyen szétválasztása a layered architecture egyik fő előnye.
