# 03 - Explore Data

## Data Profiling and Data Quality Checks

### Why is this important?

Before building transformations, we should always understand:

- What is the business key?
- Is the key unique?
- Are there NULL values?
- Can we safely join the tables?
- Do we have missing reference data?

These checks are commonly performed before creating production pipelines.

---

# Check the Mapping Table

## Row Count

```sql
SELECT COUNT(*) AS row_count
FROM `<your_name>_raw.mli_mapping`;
```

---

## Is MLI Unique?

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT MLI) AS distinct_mli
FROM `<your_name>_raw.mli_mapping`;
```

### Expected Result

```text
total_rows = distinct_mli
```

This suggests that:

```text
MLI
```

can potentially be used as a business key.

---

## Find Duplicate MLIs

```sql
SELECT
    MLI,
    COUNT(*) AS cnt
FROM `<your_name>_raw.mli_mapping`
GROUP BY MLI
HAVING COUNT(*) > 1;
```

### Expected Result

```text
0 rows returned
```

---

## Check for NULL MLI Values

```sql
SELECT
    COUNT(*) AS null_mli
FROM `<your_name>_raw.mli_mapping`
WHERE MLI IS NULL;
```

### Expected Result

```text
0
```

---

# Check the Dealer Master Table

## Row Count

```sql
SELECT COUNT(*) AS row_count
FROM `<your_name>_raw.dealer_master`;
```

---

## Is DealerCode Unique?

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT DealerCode) AS distinct_dealers
FROM `<your_name>_raw.dealer_master`;
```

### Expected Result

```text
total_rows = distinct_dealers
```

---

## Find Duplicate Dealer Codes

```sql
SELECT
    DealerCode,
    COUNT(*) AS cnt
FROM `<your_name>_raw.dealer_master`
GROUP BY DealerCode
HAVING COUNT(*) > 1;
```

### Expected Result

```text
0 rows returned
```

---

## Check for NULL Dealer Codes

```sql
SELECT
    COUNT(*) AS null_dealers
FROM `<your_name>_raw.dealer_master`
WHERE DealerCode IS NULL;
```

### Expected Result

```text
0
```

---

# Check the Sales Table

Unlike the previous tables, sales_data is a fact table.

We do not expect the key columns to be unique.

---

## Row Count

```sql
SELECT COUNT(*) AS row_count
FROM `<your_name>_raw.sales_data`;
```

---

## Distinct Dealers

```sql
SELECT
    COUNT(DISTINCT DealerCode) AS dealer_count
FROM `<your_name>_raw.sales_data`;
```

---

## Distinct Products

```sql
SELECT
    COUNT(DISTINCT MLI) AS mli_count
FROM `<your_name>_raw.sales_data`;
```

---

## Available Markets

```sql
SELECT
    Market,
    COUNT(*) AS rows
FROM `<your_name>_raw.sales_data`
GROUP BY Market
ORDER BY rows DESC;
```

---

# Validate the Future Joins

Before joining tables we should verify that the reference data exists.

---

## Missing Dealers

```sql
SELECT
    COUNT(*) AS missing_dealers
FROM `<your_name>_raw.sales_data` s
LEFT JOIN `<your_name>_raw.dealer_master` d
    ON s.DealerCode = d.DealerCode
WHERE d.DealerCode IS NULL;
```

### Expected Result

```text
0
```

---

## Missing Product Mappings

```sql
SELECT
    COUNT(*) AS missing_mapping
FROM `<your_name>_raw.sales_data` s
LEFT JOIN `<your_name>_raw.mli_mapping` m
    ON s.MLI = m.MLI
WHERE m.MLI IS NULL;
```

### Expected Result

```text
0
```

---

# Mini Data Quality Report

Run the following query:

```sql
SELECT
    (SELECT COUNT(*) FROM `<your_name>_raw.sales_data`) AS sales_rows,
    (SELECT COUNT(*) FROM `<your_name>_raw.dealer_master`) AS dealer_rows,
    (SELECT COUNT(*) FROM `<your_name>_raw.mli_mapping`) AS mapping_rows;
```

### Example Result

| sales_rows | dealer_rows | mapping_rows |
|------------|-------------|--------------|
| 10000 | 10000 | 10000 |

---

# What did we learn?

Before writing a single Dataform model we already know:

✓ Which tables are fact tables

✓ Which tables are lookup tables

✓ Which columns are business keys

✓ Which columns will be used for joins

✓ Whether the keys are unique

✓ Whether the reference data is complete

✓ Whether our future joins are safe

This is exactly the type of analysis that should happen before building production transformations.