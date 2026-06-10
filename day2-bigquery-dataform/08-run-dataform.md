# 08 - Execute the Complete Dataform Pipeline

## Objective

In this final exercise we will execute the entire warehouse pipeline from end to end.

The goal is to understand:

- execution order
- dependencies
- lineage
- assertions
- monitoring

At the end of this exercise you will have a fully functioning Dataform pipeline that transforms RAW data into a reporting-ready GOLD table.

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
├── mapping_stage
└── sales_enriched

        ↓

GOLD
└── sales_gold
```

This is already a simplified version of a real-world cloud data warehouse.

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
- data quality validation
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

and select your:

```text
development
```

workspace.

---

# Review the Repository

Verify that the following files exist:

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

# Review workflow_settings.yaml

Open:

```text
workflow_settings.yaml
```

Verify that your username is configured correctly.

Example:

```yaml
vars:
  username: "janos"
```

or:

```yaml
vars:
  username: "barni"
```

This setting determines which datasets Dataform will use.

---

# Review Generated Datasets

Remember that the username automatically generates:

```text
<username>_raw
<username>_stage
<username>_gold
```

For example:

```text
janos_raw
janos_stage
janos_gold
```

These names are created through:

```text
workflow_settings.yaml
```

and

```text
includes/config.js
```

---

# Compile the Repository

Click:

```text
Compile
```

The repository should compile successfully.

If compilation fails:

- verify workflow_settings.yaml
- verify the username
- verify all SQLX files are present
- verify includes/config.js exists

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

You should see something similar to:

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

# Understanding the Dependency Graph

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

These dependencies were created automatically through:

```sql
${ref("...")}
```

statements.

No manual dependency configuration was required.

---

# Why Is This Important?

Imagine a warehouse containing:

```text
50 tables
100 tables
500 tables
```

Manually tracking dependencies becomes impossible.

Dataform manages this automatically.

---

# Start a Pipeline Execution

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

This tells Dataform to execute the complete transformation pipeline.

---

# Start Execution

Click:

```text
Start Execution
```

Dataform will now:

1. Build STAGE models
2. Build sales_enriched
3. Build sales_gold
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

Notice that Dataform automatically determines the correct execution order.

---

# Review Execution Details

Open the execution details page.

Observe:

- execution duration
- execution order
- model status
- assertion status

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

# Verify the STAGE Dataset

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_stage
```

Verify the following tables exist:

```text
sales_stage
dealer_stage
mapping_stage
sales_enriched
```

---

# Verify the GOLD Dataset

Open:

```text
<your_name>_gold
```

Verify:

```text
sales_gold
```

exists.

---

# Review the Final Results

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

These are business-facing metrics.

---

# Review the Assertions

Open:

```text
definitions/sales_gold.sqlx
```

Review:

```sql
assertions: {
  nonNull: ["Market", "Basket"],
  uniqueKey: ["Market", "Basket"]
}
```

Remember:

These validations are executed automatically whenever the model runs.

---

# What Happens If an Assertion Fails?

Imagine that tomorrow:

```text
Basket = NULL
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

The issue is detected before bad data reaches reporting tools.

---

# Why Is This Important?

Without validation:

```text
Broken Data
      ↓
Power BI
      ↓
Incorrect Reports
      ↓
Incorrect Decisions
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

# Compare With Alteryx

Think about the workflows we reviewed at the beginning of the training.

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

implemented through:

```text
BigQuery
+
Dataform
```

The business logic is almost identical.

The implementation approach is different.

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

sales_enriched
      ↓

sales_gold
      ↓

Power BI / Excel
```

This is the same architectural pattern used by many modern cloud data platforms.

---

# Looking Ahead

Today we loaded the source files manually.

Tomorrow we will automate the ingestion process.

Instead of manually uploading CSV files into BigQuery:

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

The Dataform pipeline we built today will remain unchanged.

Only the ingestion process becomes automated.

This separation of responsibilities is one of the key advantages of a layered architecture.