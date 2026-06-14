# 03 - Az adatok feltérképezése

## Data profiling és data quality checkek

### Miért fontos ez?

A transformationök felépítése előtt mindig tisztáznunk kell:

- Mi a business key?
- Egyedi a key?
- Vannak NULL értékek?
- Biztonságosan joinolhatók a table-ök?
- Hiányzik valamilyen reference data?

Ezeket a checkeket általában a production pipeline-ok létrehozása előtt végzik el.

---

# A mapping table ellenőrzése

## Sorszám

```sql
SELECT COUNT(*) AS row_count
FROM `<your_name>_raw.mli_mapping`;
```

---

## Egyedi az MLI?

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT MLI) AS distinct_mli
FROM `<your_name>_raw.mli_mapping`;
```

### Várt eredmény

```text
total_rows = distinct_mli
```

Ez arra utal, hogy az:

```text
MLI
```

potenciálisan business keyként használható.

---

## Duplikált MLI-k keresése

```sql
SELECT
    MLI,
    COUNT(*) AS cnt
FROM `<your_name>_raw.mli_mapping`
GROUP BY MLI
HAVING COUNT(*) > 1;
```

### Várt eredmény

```text
0 rows returned
```

---

## NULL MLI-értékek ellenőrzése

```sql
SELECT
    COUNT(*) AS null_mli
FROM `<your_name>_raw.mli_mapping`
WHERE MLI IS NULL;
```

### Várt eredmény

```text
0
```

---

# A dealer master table ellenőrzése

## Sorszám

```sql
SELECT COUNT(*) AS row_count
FROM `<your_name>_raw.dealer_master`;
```

---

## Egyedi a DealerCode?

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT DealerCode) AS distinct_dealers
FROM `<your_name>_raw.dealer_master`;
```

### Várt eredmény

```text
total_rows = distinct_dealers
```

---

## Duplikált DealerCode-ok keresése

```sql
SELECT
    DealerCode,
    COUNT(*) AS cnt
FROM `<your_name>_raw.dealer_master`
GROUP BY DealerCode
HAVING COUNT(*) > 1;
```

### Várt eredmény

```text
0 rows returned
```

---

## NULL DealerCode-ok ellenőrzése

```sql
SELECT
    COUNT(*) AS null_dealers
FROM `<your_name>_raw.dealer_master`
WHERE DealerCode IS NULL;
```

### Várt eredmény

```text
0
```

---

# A sales table ellenőrzése

Az előző table-ökkel ellentétben a `sales_data` egy fact table.

Nem várjuk el, hogy a key columnok egyediek legyenek.

---

## Sorszám

```sql
SELECT COUNT(*) AS row_count
FROM `<your_name>_raw.sales_data`;
```

---

## Különböző dealerek

```sql
SELECT
    COUNT(DISTINCT DealerCode) AS dealer_count
FROM `<your_name>_raw.sales_data`;
```

---

## Különböző productok

```sql
SELECT
    COUNT(DISTINCT MLI) AS mli_count
FROM `<your_name>_raw.sales_data`;
```

---

## Elérhető marketek

```sql
SELECT
    Market,
    COUNT(*) AS rows
FROM `<your_name>_raw.sales_data`
GROUP BY Market
ORDER BY rows DESC;
```

---

# A későbbi joinok validálása

A table-ök joinolása előtt ellenőriznünk kell, hogy létezik-e a szükséges reference data.

---

## Hiányzó dealerek

```sql
SELECT
    COUNT(*) AS missing_dealers
FROM `<your_name>_raw.sales_data` s
LEFT JOIN `<your_name>_raw.dealer_master` d
    ON s.DealerCode = d.DealerCode
WHERE d.DealerCode IS NULL;
```

### Várt eredmény

```text
0
```

---

## Hiányzó product mappingek

```sql
SELECT
    COUNT(*) AS missing_mapping
FROM `<your_name>_raw.sales_data` s
LEFT JOIN `<your_name>_raw.mli_mapping` m
    ON s.MLI = m.MLI
WHERE m.MLI IS NULL;
```

### Várt eredmény

```text
0
```

---

# Mini data quality report

Futtasd az alábbi queryt:

```sql
SELECT
    (SELECT COUNT(*) FROM `<your_name>_raw.sales_data`) AS sales_rows,
    (SELECT COUNT(*) FROM `<your_name>_raw.dealer_master`) AS dealer_rows,
    (SELECT COUNT(*) FROM `<your_name>_raw.mli_mapping`) AS mapping_rows;
```

### Példaeredmény

| sales_rows | dealer_rows | mapping_rows |
|------------|-------------|--------------|
| 10000 | 10000 | 10000 |

---

# Mit tanultunk?

Már az első Dataform model megírása előtt tudjuk:

✓ Mely table-ök fact table-ök

✓ Mely table-ök lookup table-ök

✓ Mely columnok business key-ek

✓ Mely columnokat használjuk majd a joinokhoz

✓ Egyediek-e a key-ek

✓ Teljes-e a reference data

✓ Biztonságosak-e a későbbi joinjaink

Pontosan ilyen elemzést kell végezni a production transformationök felépítése előtt.
