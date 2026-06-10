# 06 - Create the INTERMEDIATE Layer

## Objective

In this exercise we will build the first business transformation layer of the warehouse.

The STAGE layer prepared and standardized our source data.

Now we will combine those datasets into a business-friendly structure that contains all information required for reporting and analysis.

At the end of this exercise we will have:

```text
<your_name>_stage.sales_enriched
```

This table will contain:

- sales transactions
- dealer information
- product classification information

all in a single dataset.

---

# What is an INTERMEDIATE Layer?

The INTERMEDIATE layer is where business logic begins.

The purpose of this layer is to:

- join datasets
- enrich transactions
- calculate derived fields
- prepare reusable datasets

Think of it as:

```text
RAW
↓
STAGE
↓
INTERMEDIATE
↓
GOLD
```

The INTERMEDIATE layer should be reusable by multiple GOLD models.

---

# Why Not Join Everything in the GOLD Layer?

A common beginner mistake is:

```text
RAW
↓
GOLD
```

with a huge SQL statement.

That works initially, but becomes difficult to maintain.

Instead we separate concerns:

```text
STAGE
= clean data

INTERMEDIATE
= business enrichment

GOLD
= reporting
```

This makes troubleshooting and maintenance much easier.

---

# Open sales_enrich.sqlx

Navigate to:

```text
definitions/sales_enrich.sqlx
```

This is our INTERMEDIATE model.

---

# Review the Configuration Block

At the top of the file you should see:

```sql
config {
  type: "table",
  schema: require("../includes/config").stage_dataset,
  name: "sales_enriched"
}
```

Notice:

```text
sales_enriched
```

is still stored in the STAGE dataset.

For training purposes this is perfectly acceptable.

In larger environments many teams create a dedicated:

```text
intermediate
```

dataset.

---

# Review the Purpose of This Model

The objective of this model is to combine:

```text
sales_stage
```

with:

```text
dealer_stage
```

and:

```text
mapping_stage
```

to create a richer dataset.

---

# Understanding the Business Logic

Before enrichment:

```text
DealerCode = D001
MLI = 1001
```

Those values are technically correct, but not particularly useful for reporting.

Business users usually need:

```text
Dealer Name
Basket
PCT
MPL Code
```

alongside the transaction data.

This model provides that context.

---

# Review the First Dataform Dependency

Locate:

```sql
FROM ${ref("sales_stage")} s
```

This is our first use of:

```text
ref()
```

---

# What Does ref() Do?

Instead of writing:

```sql
FROM janos_stage.sales_stage
```

we use:

```sql
${ref("sales_stage")}
```

Dataform automatically:

- resolves the table name
- resolves the dataset
- creates dependencies
- builds lineage

This is one of the biggest advantages of Dataform.

---

# Review the Dealer Join

Locate:

```sql
LEFT JOIN ${ref("dealer_stage")} d
```

with:

```sql
ON s.DealerCode = d.DealerCode
```

This enriches the sales records with:

```text
DealerName
```

---

# Review the Mapping Join

Locate:

```sql
LEFT JOIN ${ref("mapping_stage")} m
```

with:

```sql
ON s.MLI = m.MLI
```

This enriches transactions with:

```text
Basket
PCT
MPL_Code
```

---

# Why Did We Convert MLI to STRING Earlier?

Remember:

```text
sales_data.MLI
```

and

```text
mli_mapping.MLI
```

originally arrived as INTEGER values.

In the STAGE layer we standardized both sides:

```text
STRING
```

Now this join works reliably.

This is a perfect example of why the STAGE layer exists.

---

# Review the Output Columns

The final result contains:

```text
Sales Data
+
Dealer Information
+
Classification Information
```

Examples:

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

This dataset is already much closer to a business reporting table.

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
```

---

# Why Is Lineage Important?

Lineage helps answer questions such as:

```text
Where did this column come from?
```

or:

```text
Which models will be affected if I change a source table?
```

In larger projects this becomes extremely valuable.

---

# Execute sales_enriched

Run:

```text
sales_enriched
```

Wait for the execution to complete.

---

# Verify the Output Table

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_stage.sales_enriched
```

Preview the data.

---

# Validate the Join Results

Run:

```sql
SELECT *
FROM `<your_name>_stage.sales_enriched`
LIMIT 20;
```

Review the results.

You should now see:

```text
DealerName
Basket
PCT
MPL_Code
```

alongside the sales transaction information.

---

# Check Record Counts

Compare:

```sql
SELECT COUNT(*)
FROM `<your_name>_stage.sales_stage`;
```

and:

```sql
SELECT COUNT(*)
FROM `<your_name>_stage.sales_enriched`;
```

The counts should be identical.

Why?

Because both joins are:

```sql
LEFT JOIN
```

and should not remove records.

---

# Investigate Missing Mappings

Run:

```sql
SELECT *
FROM `<your_name>_stage.sales_enriched`
WHERE Basket IS NULL
LIMIT 20;
```

If rows appear, this means:

```text
MLI exists in sales
but not in mapping
```

This is a common data quality issue in real projects.

---

# Compare to Alteryx

The logic we just implemented is equivalent to:

```text
Input
↓
Join
↓
Join
↓
Output
```

in an Alteryx workflow.

The difference is that Dataform stores the transformation as version-controlled SQL.

---

# Checkpoint

You should now have:

✓ sales_enriched

✓ Working Dataform dependencies

✓ First use of ref()

✓ Verified lineage

✓ Successful joins

✓ Business-enriched dataset

---

# What Comes Next?

In the next exercise we will build the GOLD layer.

We will aggregate and summarize the enriched data into a reporting-ready table that could be consumed directly by Power BI, Excel or downstream reporting tools.