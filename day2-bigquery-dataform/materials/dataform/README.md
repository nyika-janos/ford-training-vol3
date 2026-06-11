# Ford Training Volume 3 - Dataform sample repository

Ez a Dataform minta a Day 3 Data Importer által betöltött RAW táblákra épül.

## Bemeneti RAW táblák

```text
<username>_raw.sales
<username>_raw.dealer_master
<username>_raw.mli_mapping
```

A `workflow_settings.yaml` fájlban a `vars.username` értéke alapján állnak össze a dataset nevek.

Példa:

```yaml
vars:
  username: "janos"
```

Ebből:

```text
janos_raw
janos_stage
janos_gold
```

## Feldolgozási lánc

```text
RAW
 |
 v
stage/sales_stage.sqlx
stage/dealer_stage.sqlx
stage/mapping_stage.sqlx
 |
 v
intermediate/sales_enrich.sqlx
 |
 v
gold/sales_gold.sqlx
```

## Gold eredmény

A `sales_gold` tábla piac, szegmens és modell szerint aggregál.

Fő metrikák:

```text
dealer_count
total_units
total_revenue
average_unit_revenue
transaction_count
first_sales_date
last_sales_date
```

Ez a gold tábla már alkalmas egyszerű Power BI vagy BigQuery Studio riport bemutatására.

A `monthly_sales.xlsx` minta alapján várhatóan ilyen jellegű sorok jönnek létre:

```text
CZ | Crossover     | Puma           | total_units: 2 | total_revenue: 54000
HU | Electric      | Mustang Mach-E | total_units: 1 | total_revenue: 62000
HU | Passenger Car | Focus          | total_units: 3 | total_revenue: 72000
SK | SUV           | Kuga           | total_units: 1 | total_revenue: 39000
```

## Megjegyzés a mintafájlokhoz

A `sales_stage` üzleti mezők alapján `SELECT DISTINCT` logikát használ. Ez azért hasznos a tréningben, mert ugyanazt a sales mintát CSV-ben és Excelben is ki lehet próbálni anélkül, hogy a gold riport véletlenül duplázódna.

## Assertionök

A minta Dataform projekt több adatminőségi ellenőrzést is tartalmaz.

```text
STAGE
  assertion_sales_stage_required_fields
  assertion_sales_stage_numeric_fields

INTERMEDIATE
  assertion_sales_enriched_dealer_join
  assertion_sales_enriched_mapping_join

GOLD
  assertion_sales_gold_positive_metrics
  assertion_sales_gold_unique_market_segment_model
```

Ezek célja, hogy ne csak a transzformáció lefutását mutassuk meg, hanem azt is, hogyan lehet Dataformmal adatminőségi kapukat építeni a pipeline-ba.

## Demo reset

Demó előtt a BigQuery táblák tiszta állapotba hozhatók ezzel a scripttel:

```text
sql/reset_demo_tables.sql
```

A script:

- truncate-eli a `training_config.file_ingestion_run_log` táblát,
- eldobja az importer által újragenerálható RAW táblákat,
- eldobja a Dataform által újragenerálható stage, intermediate és gold táblákat,
- eldobja a Dataform assertion view-kat.

Alapértelmezett felhasználó:

```sql
DECLARE username STRING DEFAULT "janos";
```

Más résztvevő esetén ezt az értéket kell átírni.
