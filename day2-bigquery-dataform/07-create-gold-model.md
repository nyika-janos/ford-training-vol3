# 07 - Create the GOLD Layer and Data Quality Checks

## Objective

In this exercise we will create the final reporting layer of the warehouse.

The GOLD layer contains business-ready data that can be consumed directly by:

- Power BI
- Excel
- Looker
- Reporting applications
- Downstream data products

At the end of this exercise we will have:

```text
<your_name>_gold.sales_gold
```

and our first automated Dataform data quality checks.

---

# What is a GOLD Layer?

The GOLD layer represents the final version of the data.

Unlike RAW or STAGE tables, GOLD tables are designed for business consumption.

A GOLD table should:

- have clear business meaning
- be easy to query
- hide technical complexity
- contain aggregated and enriched data

Think of it as:

```text
RAW
↓
STAGE
↓
INTERMEDIATE
↓
GOLD
↓
Business Users
```

---

# What Should NOT Be in a GOLD Layer?

Business users should not need to know:

```text
DealerCode
MLI
Source File Names
Technical Keys
```

Instead they should see:

```text
Market
Basket
Revenue
Quantity
```

The GOLD layer translates technical data into business data.

---

# Review the Current Warehouse

We currently have:

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

Today we will create:

```text
GOLD
└── sales_gold
```

---

# Open sales_gold.sqlx

Navigate to:

```text
definitions/sales_gold.sqlx
```

This model creates our final reporting table.

---

# Review the Configuration Block

At the top of the file you should see:

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

Several important concepts appear here.

---

# Why Are We Using a Separate Dataset?

Notice:

```sql
schema: require("../includes/config").gold_dataset
```

For a user named:

```text
janos
```

the table will be created in:

```text
janos_gold
```

This keeps reporting tables separate from staging and transformation tables.

---

# Review the Source Table

Locate:

```sql
FROM ${ref("sales_enriched")}
```

Again we use:

```text
ref()
```

instead of hardcoded table names.

Dataform automatically manages dependencies.

---

# Review the Aggregation Logic

The GOLD table groups data by:

```sql
Market,
Basket
```

and calculates:

```sql
SUM(Qty)
SUM(Revenue)
COUNT(*)
```

The result becomes:

```text
Market
Basket
Total_Qty
Total_Revenue
Transaction_Count
```

---

# Why Aggregate?

The source table contains transaction-level data.

Business users usually do not need every transaction.

Instead they want summaries such as:

```text
Revenue by Market
Revenue by Product Group
Quantity by Basket
```

The GOLD layer prepares exactly this type of information.

---

# Review the Output Columns

The final GOLD table contains:

```text
Market
Basket
Total_Qty
Total_Revenue
Transaction_Count
```

Notice that:

```text
DealerCode
MLI
DealerName
Month
```

are no longer included.

Those details are useful for processing but not necessary for this report.

---

# What Are Assertions?

The next section is:

```sql
assertions: {
  nonNull: ["Market", "Basket"],
  uniqueKey: ["Market", "Basket"]
}
```

Assertions are automated data quality checks.

They run every time the model executes.

---

# Why Do We Need Data Quality Checks?

Without validation:

```text
Broken Data
↓
Power BI
↓
Wrong Reports
↓
Wrong Decisions
```

With validation:

```text
Broken Data
↓
Assertion Failure
↓
Pipeline Stops
```

Problems are detected much earlier.

---

# Understanding nonNull

The first assertion:

```sql
nonNull: ["Market", "Basket"]
```

means:

```text
Market must always contain a value
Basket must always contain a value
```

If a NULL value appears, Dataform will fail the execution.

---

# Understanding uniqueKey

The second assertion:

```sql
uniqueKey: ["Market", "Basket"]
```

means:

```text
Each Market + Basket combination
must appear only once.
```

Examples:

Valid:

```text
HU | SUV
HU | Parts
NL | SUV
```

Invalid:

```text
HU | SUV
HU | SUV
```

The second example would fail validation.

---

# Where Did These Checks Come From?

Earlier today we manually investigated:

```sql
COUNT(*)

COUNT(DISTINCT ...)

NULL checks
```

during data profiling.

Now we are automating those checks.

This is exactly how mature warehouse projects evolve.

---

# Compile the Model

Click:

```text
Compile
```

The model should compile successfully.

---

# Review the Dependency Graph

Open:

```text
Lineage
```

You should now see:

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

The entire transformation flow is now visible.

---

# Execute sales_gold

Run:

```text
sales_gold
```

Wait until execution completes.

---

# Verify the GOLD Dataset

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_gold
```

You should see:

```text
sales_gold
```

---

# Inspect the Results

Run:

```sql
SELECT *
FROM `<your_name>_gold.sales_gold`
ORDER BY Total_Revenue DESC
LIMIT 20;
```

Review:

- Market
- Basket
- Total_Qty
- Total_Revenue
- Transaction_Count

This is now a reporting-ready table.

---

# Validate Uniqueness

Run:

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

Expected result:

```text
0 rows
```

This confirms the uniqueness assumption.

---

# Validate Null Values

Run:

```sql
SELECT *
FROM `<your_name>_gold.sales_gold`
WHERE Market IS NULL
   OR Basket IS NULL;
```

Expected result:

```text
0 rows
```

This confirms the non-null assumption.

---

# Compare to Alteryx

The logic we just implemented is equivalent to:

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

inside an Alteryx workflow.

The difference is that Dataform:

- tracks dependencies
- stores everything in Git
- performs automated testing
- documents lineage

---

# Why Is This Important for Power BI?

Most reporting tools should connect to:

```text
GOLD
```

not:

```text
RAW
```

and usually not:

```text
STAGE
```

The GOLD layer acts as the contract between the data team and business users.

---

# Checkpoint

You should now have:

✓ sales_gold

✓ Automated assertions

✓ Reporting-ready dataset

✓ Aggregated business metrics

✓ Full warehouse lineage

✓ End-to-end Dataform pipeline

---

# What Comes Next?

Today we loaded CSV files manually and transformed them using Dataform.

Tomorrow we will automate the ingestion process.

Instead of manually loading files into BigQuery:

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

The warehouse architecture remains exactly the same.

Only the ingestion layer becomes automated.