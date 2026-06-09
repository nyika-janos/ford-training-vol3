# 06 - Create INTERMEDIATE Model

## Objective

In this exercise we will build our first business transformation.

Until now we have only cleaned data.

Now we will start combining datasets together and enriching our sales records with additional business information.

At the end of this exercise you will have:

```text
sales_enriched
```

inside:

```text
<your_name>_stage
```

This table will represent our INTERMEDIATE layer.

---

# Why do we need an INTERMEDIATE layer?

The purpose of the INTERMEDIATE layer is to combine data sources and apply business logic.

Typical activities include:

- JOIN operations
- Lookup enrichment
- Business classifications
- KPI calculations
- Data preparation for reporting

In the Alteryx workflows we analyzed, most of the logic happened in this layer.

For example:

```text
Sales Data
      +
Dealer Master
      +
MLI Mapping
```

These datasets were combined before the final aggregation.

Today we will do exactly the same thing.

---

# Current Architecture

At the moment our pipeline looks like this:

```text
RAW
├── sales_data
├── dealer_master
└── mli_mapping

          ↓

STAGE
├── sales_stage
├── dealer_stage
└── mapping_stage
```

After this exercise:

```text
RAW
          ↓

STAGE
          ↓

INTERMEDIATE
└── sales_enriched
```

---

# Introducing ref()

This is the first exercise where we will use:

```sql
ref()
```

Dataform function.

Example:

```sql
${ref("sales_stage")}
```

Instead of hardcoding table names.

---

# Why use ref()?

Without ref():

```sql
SELECT *
FROM ford-training-430008.janos_stage.sales_stage
```

With ref():

```sql
SELECT *
FROM ${ref("sales_stage")}
```

Advantages:

- Easier maintenance
- Dependency tracking
- Automatic lineage generation
- Safer refactoring

This is one of the key features of Dataform.

---

# Create sales_enriched.sqlx

Navigate to:

```text
definitions
```

Click:

```text
Create File
```

File name:

```text
sales_enriched.sqlx
```

---

# Add Configuration

Paste:

```sql
config {
  type: "table",
  schema: "<your_name>_stage",
  name: "sales_enriched"
}
```

Replace:

```text
<your_name>
```

with your own name.

Example:

```text
janos_stage
```

---

# Add the SQL Logic

Paste the following query:

```sql
SELECT
    s.Market,
    s.DealerCode,
    d.DealerName,
    s.MLI,
    m.Basket,
    m.PCT,
    m.MPL_Code,
    s.Month,
    s.Qty,
    s.Revenue
FROM ${ref("sales_stage")} s

LEFT JOIN ${ref("dealer_stage")} d
    ON s.DealerCode = d.DealerCode

LEFT JOIN ${ref("mapping_stage")} m
    ON s.MLI = m.MLI
```

---

# What are we doing?

This query combines:

```text
sales_stage
```

with:

```text
dealer_stage
```

using:

```text
DealerCode
```

and:

```text
mapping_stage
```

using:

```text
MLI
```

---

# Alteryx Equivalent

This Dataform model corresponds roughly to:

```text
Input
  ↓
Join
  ↓
Join
  ↓
Output
```

inside an Alteryx workflow.

The business logic is exactly the same.

Only the implementation technology changes.

---

# Compile the Repository

Click:

```text
Compile
```

Dataform should successfully compile the repository.

If errors occur:

- Check spelling
- Verify model names
- Verify ref() references

---

# Observe the Dependency Graph

After compilation, Dataform should now understand:

```text
sales_stage
         \
          \
           \
            sales_enriched
           /
          /
dealer_stage

mapping_stage
```

This dependency graph is automatically generated from the ref() statements.

---

# Run the Model

Click:

```text
Start Execution
```

Select:

```text
sales_enriched
```

Execute the model.

Wait for successful completion.

---

# Verify the Output

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_stage.sales_enriched
```

Preview the data.

You should see columns from:

- sales_stage
- dealer_stage
- mapping_stage

combined into a single table.

---

# Verify Record Count

Run:

```sql
SELECT COUNT(*)
FROM `<your_name>_stage.sales_enriched`;
```

Expected result:

```text
10000
```

The row count should remain unchanged because we used:

```sql
LEFT JOIN
```

---

# Validate Missing Dealers

Run:

```sql
SELECT
    COUNT(*) AS missing_dealers
FROM `<your_name>_stage.sales_enriched`
WHERE DealerName IS NULL;
```

Expected:

```text
0
```

---

# Validate Missing Product Mapping

Run:

```sql
SELECT
    COUNT(*) AS missing_mapping
FROM `<your_name>_stage.sales_enriched`
WHERE Basket IS NULL;
```

Expected:

```text
0
```

---

# Business Validation

Let's verify that the enrichment worked.

Run:

```sql
SELECT *
FROM `<your_name>_stage.sales_enriched`
LIMIT 20;
```

You should now see:

```text
DealerName
Basket
PCT
MPL_Code
```

which did not exist in the original sales table.

---

# Data Quality Check

How many baskets do we have?

```sql
SELECT
    Basket,
    COUNT(*) AS records
FROM `<your_name>_stage.sales_enriched`
GROUP BY Basket
ORDER BY records DESC;
```

This confirms that the mapping table was successfully applied.

---

# Understanding the Result

The sales table now contains:

```text
Sales Data
+
Dealer Information
+
Product Classification
```

This is often the most important transformation layer in a warehouse.

Most business logic is built on top of this type of enriched dataset.

---

# Checkpoint

You should now have:

✓ sales_enriched

generated by Dataform.

The table should contain:

✓ DealerName

✓ Basket

✓ PCT

✓ MPL_Code

alongside the original sales data.

---

# What comes next?

In the next exercise we will build our GOLD layer.

We will aggregate the enriched data and create a reporting-ready table that could be consumed directly by:

- Power BI
- Excel
- Looker
- Business users

This will be the final step of our warehouse pipeline.