# 08 - Execute the Complete Dataform Pipeline

## Objective

In this final exercise we will execute the entire warehouse pipeline from end to end.

The goal is to understand:

- execution order
- dependencies
- lineage
- assertions
- monitoring

At the end of this exercise you will have a complete understanding of how Dataform manages a warehouse pipeline.

---

# What Have We Built?

Over the previous exercises we created:

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

        ↓

INTERMEDIATE
└── sales_enriched

        ↓

GOLD
└── sales_gold
```

This is already a simplified version of a real enterprise warehouse.

---

# Why Run the Entire Pipeline?

Until now we executed individual models.

In production environments we typically execute:

```text
The entire pipeline
```

rather than individual tables.

This ensures:

- correct execution order
- dependency management
- automatic validation
- reproducibility

---

# Open Dataform

Navigate to:

```text
Dataform
```

Open:

```text
<your_name>_training_dataform
```

Open the:

```text
development
```

workspace.

---

# Review the Repository

Verify that you have the following files:

```text
definitions/

├── sales_stage.sqlx
├── dealer_stage.sqlx
├── mapping_stage.sqlx
├── sales_enriched.sqlx
└── sales_gold.sqlx
```

---

# Compile the Repository

Click:

```text
Compile
```

The repository should compile successfully.

If compilation fails:

- check SQL syntax
- check model names
- check ref() references
- check dataset names

---

# Review the Dependency Graph

Open:

```text
Lineage
```

or

```text
Dependency Graph
```

depending on the UI version.

You should see a graph similar to:

```text
sales_data
       ↓
sales_stage
       ↓

dealer_master
       ↓
dealer_stage
       ↓

mli_mapping
       ↓
mapping_stage
       ↓

       sales_enriched
              ↓
         sales_gold
```

---

# Understanding the Graph

Notice that:

```text
sales_gold
```

depends on:

```text
sales_enriched
```

which depends on:

```text
sales_stage
dealer_stage
mapping_stage
```

Dataform learned these dependencies automatically through:

```sql
ref()
```

statements.

No manual dependency configuration was required.

---

# Start Pipeline Execution

Click:

```text
Start Execution
```

---

# Select Execution Mode

Choose:

```text
Run all actions
```

This tells Dataform to execute the complete pipeline.

---

# Start Execution

Click:

```text
Start Execution
```

Dataform will now:

1. Build STAGE models
2. Build INTERMEDIATE model
3. Build GOLD model
4. Execute assertions

automatically.

---

# Observe the Execution Graph

Watch the execution progress.

You should see something similar to:

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

Notice that Dataform automatically executes models in the correct order.

---

# Review Execution Details

Open the execution details.

Observe:

- execution duration
- generated SQL
- execution order
- model status

This information is extremely useful during troubleshooting.

---

# Verify Successful Completion

All objects should show:

```text
SUCCESS
```

If everything completed successfully:

✓ Pipeline executed

✓ Assertions passed

✓ GOLD table refreshed

---

# Verify the GOLD Layer

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_gold.sales_gold
```

Preview the results.

---

# Validate Business Results

Run:

```sql
SELECT *
FROM `<your_name>_gold.sales_gold`
ORDER BY Total_Revenue DESC
LIMIT 20;
```

Observe:

- Markets
- Product Baskets
- Revenue
- Quantities

This is the type of data that business users typically consume.

---

# Review Assertions

Open:

```text
sales_gold.sqlx
```

Review:

```sql
assertions: {
  nonNull: ["Market", "Basket"],
  uniqueKey: ["Market", "Basket"]
}
```

Remember:

These checks are executed automatically.

No additional SQL is required.

---

# What Happens If an Assertion Fails?

Imagine that tomorrow:

```text
Market = NULL
```

appears in the GOLD table.

Dataform will:

```text
Execute Assertion
        ↓
Assertion Fails
        ↓
Execution Fails
```

This prevents bad data from reaching reports.

---

# Why Is This Important?

Without validation:

```text
Broken data
      ↓
Power BI
      ↓
Wrong business decisions
```

With validation:

```text
Broken data
      ↓
Assertion Failure
      ↓
Pipeline Stops
```

Problems are detected much earlier.

---

# Compare With Alteryx

Think about the workflow we analyzed earlier.

In Alteryx:

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

In GCP:

```text
RAW
 ↓
STAGE
 ↓
INTERMEDIATE
 ↓
GOLD
```

managed by:

```text
BigQuery
+
Dataform
```

The business logic is almost identical.

Only the implementation differs.

---

# What Did We Learn Today?

Today we learned:

✓ BigQuery warehouse structure

✓ RAW layer

✓ STAGE layer

✓ INTERMEDIATE layer

✓ GOLD layer

✓ Dataform repositories

✓ Dataform models

✓ ref() dependencies

✓ Lineage

✓ Assertions

✓ Automated data quality validation

---

# Final Architecture

You have successfully built:

```text
CSV Files
      ↓

RAW Tables
      ↓

STAGE Models
      ↓

INTERMEDIATE Model
      ↓

GOLD Table
      ↓

Power BI / Excel
```

This is the same architecture pattern used in many modern cloud data platforms.

---

# Looking Ahead

Today we loaded the source files manually.

Tomorrow we will automate the ingestion process.

Instead of manually loading CSV files:

```text
Excel File
      ↓
Cloud Storage
      ↓
Cloud Run
      ↓
BigQuery RAW
```

The warehouse pipeline we built today will remain unchanged.

Only the ingestion process will become automated.

This is one of the key benefits of a layered architecture:

each component can evolve independently without changing the rest of the pipeline.