# 07 - Create GOLD Model

## Objective

In this exercise we will create the final reporting layer of our warehouse.

The purpose of the GOLD layer is to provide clean, business-friendly and reporting-ready datasets.

At the end of this exercise you will have:

```text
sales_gold
```

inside:

```text
<your_name>_gold
```

This table will be the final output of our Dataform pipeline.

In addition, we will introduce Dataform assertions and automated data quality validation.

---

# Why do we need a GOLD layer?

The INTERMEDIATE layer contains detailed transactional data.

This is useful for data engineers and analysts, but business users typically do not want:

- transaction-level data
- technical columns
- complex joins
- transformation logic

Business users usually want answers to questions like:

- What was the revenue by market?
- What was the revenue by product category?
- Which basket performed best?
- How many units were sold?

The GOLD layer provides exactly these types of answers.

---

# Current Architecture

At the moment our pipeline looks like this:

```text
RAW
          ↓
STAGE
          ↓
INTERMEDIATE
└── sales_enriched
```

After this exercise:

```text
RAW
          ↓
STAGE
          ↓
INTERMEDIATE
└── sales_enriched
          ↓
GOLD
└── sales_gold
```

---

# What is a GOLD Table?

A GOLD table should be:

✓ Easy to understand

✓ Easy to query

✓ Fast to consume

✓ Stable

✓ Business-oriented

A Power BI report should ideally connect directly to a GOLD table rather than rebuilding business logic inside Power BI.

---

# Create sales_gold.sqlx

Navigate to:

```text
definitions
```

Create a new file:

```text
sales_gold.sqlx
```

---

# Configure the Model

Paste:

```sql
config {
  type: "table",
  schema: "<your_name>_gold",
  name: "sales_gold",

  assertions: {
    nonNull: ["Market", "Basket"],
    uniqueKey: ["Market", "Basket"]
  }
}
```

Replace:

```text
<your_name>
```

with your own name.

Example:

```text
janos_gold
```

---

# What are Assertions?

Assertions are automated data quality checks.

Earlier in Exercise 03 we manually verified:

- uniqueness
- null values
- join quality

Now we will automate those checks.

Dataform will automatically generate validation queries behind the scenes.

If an assertion fails:

```text
Dataform Run = FAILED
```

This is extremely useful in production pipelines.

---

# Understanding the Assertions

## nonNull

```sql
nonNull: ["Market", "Basket"]
```

This means:

```text
Market cannot be NULL
Basket cannot be NULL
```

If either column contains NULL values:

```text
Assertion FAIL
```

---

## uniqueKey

```sql
uniqueKey: ["Market", "Basket"]
```

This means:

```text
Market + Basket
```

must uniquely identify every row.

Example:

Valid:

| Market | Basket |
|----------|----------|
| HU | Engine |
| HU | Parts |
| NL | Engine |

Invalid:

| Market | Basket |
|----------|----------|
| HU | Engine |
| HU | Engine |

The second example would fail the assertion.

---

# Add the Aggregation Logic

Paste:

```sql
SELECT
    Market,
    Basket,
    SUM(Qty) AS Total_Qty,
    SUM(Revenue) AS Total_Revenue,
    COUNT(*) AS Transaction_Count
FROM ${ref("sales_enriched")}
GROUP BY
    Market,
    Basket
```

---

# What are we doing?

Instead of looking at individual sales transactions, we are summarizing the data.

We group by:

```text
Market
Basket
```

and calculate:

```text
Total Quantity
Total Revenue
Transaction Count
```

This is one of the most common reporting patterns in analytics projects.

---

# Alteryx Equivalent

This Dataform model corresponds roughly to:

```text
Input
  ↓
Summarize
  ↓
Output
```

inside Alteryx.

The SQL equivalent is:

```sql
GROUP BY
SUM()
COUNT()
```

---

# Compile the Repository

Click:

```text
Compile
```

The repository should compile successfully.

At this point Dataform understands the following dependency chain:

```text
sales_data
       ↓
sales_stage
       ↓
sales_enriched
       ↓
sales_gold
```

---

# Examine the Lineage Graph

Open the lineage view.

You should now see something similar to:

```text
mli_mapping
               \
                \
                 \
                  sales_enriched
                 /
                /
dealer_master  /
              /
sales_data
      ↓
sales_stage
      ↓
sales_gold
```

This dependency graph was created automatically from the ref() statements.

---

# Execute the Pipeline

Click:

```text
Start Execution
```

Select:

```text
sales_gold
```

Dataform will automatically determine that it depends on:

```text
sales_enriched
```

and execute the required dependency chain.

Wait until execution completes successfully.

---

# Verify the Table

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_gold.sales_gold
```

Preview the data.

You should see aggregated results.

Example:

| Market | Basket | Total_Qty | Total_Revenue |
|----------|----------|----------|----------|
| HU | Engine | 12500 | 1250000 |
| HU | Parts | 11800 | 1180000 |

---

# Validate the Aggregation

How many rows exist?

Run:

```sql
SELECT COUNT(*)
FROM `<your_name>_gold.sales_gold`;
```

Expected:

A relatively small number of rows.

Why?

Because:

```text
10,000 transactions
        ↓
Aggregation
        ↓
20 reporting rows
```

(approximately)

---

# Check Revenue by Market

Run:

```sql
SELECT
    Market,
    SUM(Total_Revenue) AS Revenue
FROM `<your_name>_gold.sales_gold`
GROUP BY Market
ORDER BY Revenue DESC;
```

---

# Check Revenue by Basket

Run:

```sql
SELECT
    Basket,
    SUM(Total_Revenue) AS Revenue
FROM `<your_name>_gold.sales_gold`
GROUP BY Basket
ORDER BY Revenue DESC;
```

---

# Manual Validation

Let's manually validate the same rules that Dataform is checking.

---

## Check for NULL Markets

```sql
SELECT
    COUNT(*) AS null_markets
FROM `<your_name>_gold.sales_gold`
WHERE Market IS NULL;
```

Expected:

```text
0
```

---

## Check for NULL Baskets

```sql
SELECT
    COUNT(*) AS null_baskets
FROM `<your_name>_gold.sales_gold`
WHERE Basket IS NULL;
```

Expected:

```text
0
```

---

## Check Uniqueness

```sql
SELECT
    Market,
    Basket,
    COUNT(*) AS cnt
FROM `<your_name>_gold.sales_gold`
GROUP BY
    Market,
    Basket
HAVING COUNT(*) > 1;
```

Expected:

```text
0 rows returned
```

---

# How Dataform Executes Assertions

Behind the scenes Dataform generates additional validation queries.

Conceptually it creates checks similar to:

```sql
SELECT *
FROM sales_gold
WHERE Market IS NULL
```

and

```sql
SELECT
    Market,
    Basket,
    COUNT(*)
FROM sales_gold
GROUP BY
    Market,
    Basket
HAVING COUNT(*) > 1
```

If any rows are returned:

```text
Assertion FAIL
```

and the pipeline is marked as unsuccessful.

---

# Why is this Important?

Imagine that tomorrow:

- a source file changes
- a mapping table is corrupted
- a join introduces duplicates

Without validation:

```text
Bad data reaches Power BI
```

With assertions:

```text
Pipeline fails
↓
Problem detected immediately
```

This is one of the key differences between ad-hoc reporting and production-grade data engineering.

---

# Production Thinking

In real projects we commonly implement:

```text
✓ not null
✓ unique
✓ referential integrity
✓ accepted values
✓ freshness checks
```

Dataform provides mechanisms for all of these.

The assertions we created today are the first step toward automated data quality monitoring.

---

# Checkpoint

You should now have:

✓ sales_gold

inside:

```text
<your_name>_gold
```

✓ Automatic non-null validation

✓ Automatic uniqueness validation

✓ Reporting-ready aggregated data

✓ A complete warehouse pipeline

```text
RAW
 ↓
STAGE
 ↓
INTERMEDIATE
 ↓
GOLD
```

---

# What comes next?

In the final exercise we will run the complete pipeline end-to-end and review:

- dependencies
- lineage
- assertions
- execution order

to understand how Dataform manages a complete warehouse workflow.