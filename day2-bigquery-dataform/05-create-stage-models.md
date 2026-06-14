# 05 - STAGE modellek létrehozása

## Cél

Ebben a gyakorlatban megvizsgáljuk a STAGE layert, és futtatjuk az első Dataform transformationöket.

A STAGE layer célja nem a business logic implementálása.

A célja az adatok előkészítése a későbbi processinghez.

A tipikus STAGE tevékenységek:

- Data type-ok harmonizálása
- Columnok standardizálása
- Szöveges értékek trimelése
- Key-ek egységes formátumra alakítása
- Adatok előkészítése a joinokhoz

A gyakorlat végére három STAGE table-lel fogsz rendelkezni:

```text
<your_name>_stage.sales_stage
<your_name>_stage.dealer_stage
<your_name>_stage.mapping_stage
```

---

# Miért van szükség STAGE layerre?

Sokan hajlamosak közvetlenül a RAW table-ökből joinolni és aggregálni az adatokat.

Ez kezdetben általában működik.

Idővel azonban:

- változnak a source systemek
- változnak a data type-ok
- változnak a file formatok
- további business rule-ok jelennek meg

A STAGE layer védelmi határként szolgál a source systemek és a business logic között.

Jó ökölszabály:

```text
RAW = Amit megkaptunk

STAGE = Amiben megbízunk
```

---

# A data warehouse layerek áttekintése

A warehouse jelenleg így néz ki:

```text
RAW
├── sales_data
├── dealer_master
└── mli_mapping
```

Ma az alábbiakat hozzuk létre:

```text
STAGE
├── sales_stage
├── dealer_stage
└── mapping_stage
```

Később az alábbiakat építjük fel:

```text
INTERMEDIATE
└── sales_enriched

GOLD
└── sales_gold
```

---

# A sales_stage.sqlx megnyitása

Navigálj ide:

```text
definitions/sales_stage.sqlx
```

Tekintsd át a modelt.

---

# A configuration block áttekintése

A fájl tetején az alábbit kell látnod:

```sql
config {
  type: "table",
  schema: require("../includes/config").stage_dataset,
  name: "sales_stage"
}
```

Ez azt mondja meg a Dataformnak, hogy:

- hozzon létre egy table-t
- helyezze a STAGE datasetbe
- nevezze el a table-t `sales_stage`-nek

Figyeld meg, hogy nem hardcode-oljuk ezt:

```text
janos_stage
```

vagy

```text
barni_stage
```

A dataset automatikusan generálódik a username alapján.

---

# A source table áttekintése

Keresd meg:

```sql
FROM `${raw_dataset}.sales_data`
```

Ez a RAW source table-ünk.

Ne feledd:

```text
A RAW table-öket soha nem módosítjuk.
```

Minden transformation egy új layerben történik.

---

# A data type conversion áttekintése

Keresd meg:

```sql
CAST(MLI AS STRING) AS MLI
```

Miért van erre szükség?

Mert a CSV import az alábbit hozta létre:

```text
MLI = INTEGER
```

Azonban az:

```text
MLI
```

valójában egy business key.

A business key-eket általában stringként kezeljük.

Ezzel elkerülhetők a későbbi problémák, amikor az alábbiakat:

```text
0001
0010
0100
1000
```

kell ábrázolni.

---

# A további standardizálás áttekintése

Figyeld meg:

```sql
UPPER(Market)
```

és

```sql
TRIM(DealerCode)
```

Ezek egyszerű, de fontos transformationök.

Segítenek elkerülni például azt, hogy az alábbi értékeket:

```text
HU
Hu
hu
HU
```

különböző értékekként kezeljük.

---

# A sales_stage.sqlx compile-olása

Kattints erre:

```text
Compile
```

A modelnek sikeresen kell compile-olódnia.

---

# A dealer_stage.sqlx megnyitása

Navigálj ide:

```text
definitions/dealer_stage.sqlx
```

Tekintsd át a modelt.

---

# A dealer_stage célja

Ez a model előkészíti a dealer master data-t.

A transformationök szándékosan egyszerűek:

```sql
UPPER(Market)

TRIM(DealerCode)

TRIM(DealerName)
```

A cél a konzisztencia.

A dealer informationt később a sales data-hoz joinoljuk.

---

# A dealer_stage.sqlx compile-olása

Ellenőrizd, hogy a model sikeresen compile-olódik-e.

---

# A mapping_stage.sqlx megnyitása

Navigálj ide:

```text
definitions/mapping_stage.sqlx
```

Tekintsd át a modelt.

---

# A mapping_stage célja

Ez a table business mappingeket tartalmaz.

Az eredeti Alteryx workflow-kban ez a mapping egy Excel-fájlból származott.

Példák:

```text
MLI
Basket
PCT
MPL_Code
```

A model célja ezeknek az értékeknek az előkészítése a későbbi enrichmenthez.

---

# Az MLI conversion áttekintése

Keresd meg:

```sql
CAST(MLI AS STRING) AS MLI
```

Az MLI-t ismét STRING-gé alakítjuk.

Ez biztosítja, hogy:

```text
sales_stage.MLI
```

és

```text
mapping_stage.MLI
```

ugyanazzal a data type-pal rendelkezzen.

Ez elengedhetetlen a sikeres joinokhoz.

---

# A mapping_stage.sqlx compile-olása

Ellenőrizd, hogy a compilation sikeres-e.

---

# Az egyes modellek futtatása

Most futtatjuk a három STAGE modelt.

Futtasd:

```text
sales_stage
```

Várd meg, amíg az execution befejeződik.

---

Futtasd:

```text
dealer_stage
```

Várd meg, amíg az execution befejeződik.

---

Futtasd:

```text
mapping_stage
```

Várd meg, amíg az execution befejeződik.

---

# A létrehozott table-ök ellenőrzése

Navigálj ide:

```text
BigQuery Studio
```

Nyisd meg:

```text
<your_name>_stage
```

Az alábbiakat kell látnod:

```text
sales_stage
dealer_stage
mapping_stage
```

---

# A sales_stage vizsgálata

Futtasd:

```sql
SELECT *
FROM `<your_name>_stage.sales_stage`
LIMIT 20;
```

Tekintsd át:

- Market
- DealerCode
- MLI
- Month
- Qty
- Revenue

---

# Az MLI data type ellenőrzése

Nyisd meg a schemát.

Ellenőrizd, hogy az:

```text
MLI
```

most már:

```text
STRING
```

Ez a STAGE layer egyik fő célkitűzése.

---

# A RAW és a STAGE összehasonlítása

RAW:

```text
Eredeti source structure
```

STAGE:

```text
Standardizált structure
```

Figyeld meg, hogy a business meaning nem változott.

Csak a konzisztencián és a használhatóságon javítottunk.

---

# Checkpoint

Mostanra rendelkezned kell az alábbiakkal:

✓ sales_stage

✓ dealer_stage

✓ mapping_stage

✓ Sikeres execution

✓ Ellenőrzött schemák

✓ Standardizált business key-ek

---

# Mi következik?

A STAGE layer előkészíti az adatokat.

A következő gyakorlatban létrehozzuk az első business transformation layert.

Joinoljuk az alábbiakat:

```text
sales_stage
+
dealer_stage
+
mapping_stage
```

így létrehozunk egy enriched datasetet, amely transactional és business context informationt egyaránt tartalmaz.
