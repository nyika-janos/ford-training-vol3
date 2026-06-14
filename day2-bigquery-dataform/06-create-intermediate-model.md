# 06 - Az INTERMEDIATE layer létrehozása

## Cél

Ebben a gyakorlatban felépítjük a warehouse első business transformation layerét.

A STAGE layer előkészítette és standardizálta a source data-t.

Most ezeket a dataseteket egy business-friendly structure-ben egyesítjük, amely minden, a reportinghoz és analysishez szükséges információt tartalmaz.

A gyakorlat végére rendelkezünk majd az alábbival:

```text
<your_name>_stage.sales_enriched
```

Ez a table az alábbiakat tartalmazza:

- sales transactionök
- dealer information
- product classification information

mindezt egyetlen datasetben.

---

# Mi az INTERMEDIATE layer?

Az INTERMEDIATE layerben kezdődik a business logic.

A layer célja:

- datasetek joinolása
- transactionök enrich-elése
- derived fieldek kiszámítása
- újrafelhasználható datasetek előkészítése

A folyamatban elfoglalt helye:

```text
RAW
↓
STAGE
↓
INTERMEDIATE
↓
GOLD
```

Az INTERMEDIATE layernek több GOLD model által is újrafelhasználhatónak kell lennie.

---

# Miért nem a GOLD layerben joinolunk mindent?

Gyakori kezdő hiba:

```text
RAW
↓
GOLD
```

egyetlen hatalmas SQL statementtel.

Ez kezdetben működik, de nehezen karbantarthatóvá válik.

Ehelyett szétválasztjuk a felelősségi köröket:

```text
STAGE
= tiszta adatok

INTERMEDIATE
= business enrichment

GOLD
= reporting
```

Ez jelentősen megkönnyíti a troubleshootingot és a karbantartást.

---

# A sales_enrich.sqlx megnyitása

Navigálj ide:

```text
definitions/sales_enrich.sqlx
```

Ez az INTERMEDIATE modelünk.

---

# A configuration block áttekintése

A fájl tetején az alábbit kell látnod:

```sql
config {
  type: "table",
  schema: require("../includes/config").stage_dataset,
  name: "sales_enriched"
}
```

Figyeld meg, hogy a:

```text
sales_enriched
```

továbbra is a STAGE datasetben található.

A training céljaira ez teljesen megfelelő.

Nagyobb environmentekben sok team külön:

```text
intermediate
```

datasetet hoz létre.

---

# A model céljának áttekintése

A model célja ennek:

```text
sales_stage
```

az összekapcsolása ezzel:

```text
dealer_stage
```

és ezzel:

```text
mapping_stage
```

egy gazdagabb dataset létrehozásához.

---

# A business logic megértése

Enrichment előtt:

```text
DealerCode = D001
MLI = 1001
```

Ezek az értékek technikailag helyesek, de a reporting szempontjából nem különösebben hasznosak.

A business usereknek általában az alábbiakra van szükségük:

```text
Dealer Name
Basket
PCT
MPL Code
```

a transaction data mellett.

Ez a model biztosítja ezt a contextet.

---

# Az első Dataform dependency áttekintése

Keresd meg:

```sql
FROM ${ref("sales_stage")} s
```

Itt használjuk először a:

```text
ref()
```

---

# Mit csinál a ref()?

Ahelyett, hogy ezt írnánk:

```sql
FROM janos_stage.sales_stage
```

ezt használjuk:

```sql
${ref("sales_stage")}
```

A Dataform automatikusan:

- feloldja a table nevét
- feloldja a datasetet
- létrehozza a dependencyket
- felépíti a lineage-et

Ez a Dataform egyik legnagyobb előnye.

---

# A dealer join áttekintése

Keresd meg:

```sql
LEFT JOIN ${ref("dealer_stage")} d
```

ezzel:

```sql
ON s.DealerCode = d.DealerCode
```

Ez az alábbival enrich-eli a sales recordokat:

```text
DealerName
```

---

# A mapping join áttekintése

Keresd meg:

```sql
LEFT JOIN ${ref("mapping_stage")} m
```

ezzel:

```sql
ON s.MLI = m.MLI
```

Ez az alábbiakkal enrich-eli a transactionöket:

```text
Basket
PCT
MPL_Code
```

---

# Miért alakítottuk korábban STRING-gé az MLI-t?

Ne feledd, hogy a:

```text
sales_data.MLI
```

és

```text
mli_mapping.MLI
```

eredetileg INTEGER értékként érkezett.

A STAGE layerben mindkét oldalt erre standardizáltuk:

```text
STRING
```

Így ez a join már megbízhatóan működik.

Ez tökéletes példa arra, hogy miért létezik a STAGE layer.

---

# Az output columnok áttekintése

A végeredmény az alábbiakat tartalmazza:

```text
Sales Data
+
Dealer Information
+
Classification Information
```

Példák:

```text
Market
DealerCode
DealerName
MLI
Basket
PCT
MPL_Code
Month
Qty
Revenue
```

Ez a dataset már sokkal közelebb áll egy business reporting table-höz.

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
```

---

# Miért fontos a lineage?

A lineage segít megválaszolni az alábbi kérdéseket:

```text
Honnan származik ez a column?
```

vagy:

```text
Mely modellekre lesz hatással, ha módosítok egy source table-t?
```

Nagyobb projectekben ez rendkívül értékessé válik.

---

# A sales_enriched futtatása

Futtasd:

```text
sales_enriched
```

Várd meg, amíg az execution befejeződik.

---

# Az output table ellenőrzése

Navigálj ide:

```text
BigQuery Studio
```

Nyisd meg:

```text
<your_name>_stage.sales_enriched
```

Tekintsd meg az adatok Preview-ját.

---

# A join eredmények validálása

Futtasd:

```sql
SELECT *
FROM `<your_name>_stage.sales_enriched`
LIMIT 20;
```

Tekintsd át az eredményeket.

Most már az alábbiakat kell látnod:

```text
DealerName
Basket
PCT
MPL_Code
```

a sales transaction information mellett.

---

# A record countok ellenőrzése

Hasonlítsd össze:

```sql
SELECT COUNT(*)
FROM `<your_name>_stage.sales_stage`;
```

és:

```sql
SELECT COUNT(*)
FROM `<your_name>_stage.sales_enriched`;
```

A countoknak azonosnak kell lenniük.

Miért?

Mert mindkét join:

```sql
LEFT JOIN
```

és nem távolíthat el recordokat.

---

# A hiányzó mappingek vizsgálata

Futtasd:

```sql
SELECT *
FROM `<your_name>_stage.sales_enriched`
WHERE Basket IS NULL
LIMIT 20;
```

Ha sorok jelennek meg, az azt jelenti:

```text
Az MLI létezik a sales adatokban,
de a mappingben nem.
```

Ez gyakori data quality issue valós projectekben.

---

# Összehasonlítás az Alteryxszel

Az imént implementált logic az alábbival egyenértékű:

```text
Input
↓
Join
↓
Join
↓
Output
```

egy Alteryx workflow-ban.

A különbség az, hogy a Dataform version-controlled SQL-ként tárolja a transformationt.

---

# Checkpoint

Mostanra rendelkezned kell az alábbiakkal:

✓ sales_enriched

✓ Működő Dataform dependencyk

✓ A `ref()` első használata

✓ Ellenőrzött lineage

✓ Sikeres joinok

✓ Business-enriched dataset

---

# Mi következik?

A következő gyakorlatban felépítjük a GOLD layert.

Az enriched adatokat egy reporting-ready table-be aggregáljuk és összegezzük, amelyet közvetlenül használhat a Power BI, az Excel vagy más downstream reporting tool.
