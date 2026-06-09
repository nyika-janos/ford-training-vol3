# 05 - Create STAGE Models

## Objective

In this exercise we will create our first Dataform models.

The purpose of the STAGE layer is to perform technical data cleaning before applying any business logic.

At the end of this exercise you will have:

```text
sales_stage
dealer_stage
mapping_stage
```

tables created by Dataform.

---

# Why do we need a STAGE layer?

A common mistake in data projects is mixing:

- technical cleaning
- business logic
- reporting logic

inside the same SQL query.

Instead, we separate responsibilities.

The STAGE layer is responsible for:

- standardizing text
- fixing data types
- renaming columns
- removing technical inconsistencies

The STAGE layer should **not** contain business logic.

No joins.

No aggregations.

No KPIs.

No reporting calculations.

Only technical cleanup.

---

# What will we build?

Today our architecture looks like:

```text
RAW
├── sales_data
├── dealer_master
└── mli_mapping
```

After this exercise:

```text
RAW
 ↓
STAGE
├── sales_stage
├── dealer_stage
└── mapping_stage
```

---

# Dataform Model Basics

Each transformation in Dataform is stored in a file:

```text
.sqlx
```

Example:

```text
sales_stage.sqlx
```

Each file generates a table or view in BigQuery.

Think of a Dataform model as:

```text
One SQL file
=
One transformation step
```

---

# Create sales_stage.sqlx

Navigate to:

```text
definitions
```

Click:

```text
Create File
```

Name:

```text
sales_stage.sqlx
```

---

# Configure the Model

Paste the following code:

```sql
config {
  type: "table",
  schema: "<your_name>_stage",
  name: "sales_stage"
}

SELECT
    UPPER(Market) AS Market,
    TRIM(DealerCode) AS DealerCode,
    CAST(Month AS INT64) AS Month,
    CAST(Qty AS INT64) AS Qty,
    CAST(Revenue AS NUMERIC) AS Revenue,
    TRIM(MLI) AS MLI
FROM `${dataform.projectConfig.defaultDatabase}.<your_name>_raw.sales_data`
```

Replace:

```text
<your_name>
```

with your own name.

Example:

```text
janos_stage
janos_raw
```

---

# What are we doing?

Let's review the transformations:

## UPPER

```sql
UPPER(Market)
```

Standardizes text values.

Example:

```text
hu
Hu
HU
```

becomes:

```text
HU
```

---

## TRIM

```sql
TRIM(DealerCode)
```

Removes leading and trailing spaces.

Example:

```text
" D001 "
```

becomes:

```text
"D001"
```

---

## CAST

```sql
CAST(Month AS INT64)
```

Ensures the correct data type.

This is important for:

- calculations
- filtering
- aggregations

---

# Create dealer_stage.sqlx

Create another file:

```text
dealer_stage.sqlx
```

Paste:

```sql
config {
  type: "table",
  schema: "<your_name>_stage",
  name: "dealer_stage"
}

SELECT
    UPPER(Market) AS Market,
    TRIM(DealerCode) AS DealerCode,
    TRIM(DealerName) AS DealerName
FROM `${dataform.projectConfig.defaultDatabase}.<your_name>_raw.dealer_master`
```

---

# Create mapping_stage.sqlx

Create:

```text
mapping_stage.sqlx
```

Paste:

```sql
config {
  type: "table",
  schema: "<your_name>_stage",
  name: "mapping_stage"
}

SELECT
    TRIM(MLI) AS MLI,
    TRIM(Basket) AS Basket,
    TRIM(PCT) AS PCT,
    TRIM(MPL_Code) AS MPL_Code
FROM `${dataform.projectConfig.defaultDatabase}.<your_name>_raw.mli_mapping`
```

---

# Understanding Dataform Dependencies

At this point we have:

```text
sales_stage
    ↑
sales_data
```

```text
dealer_stage
    ↑
dealer_master
```

```text
mapping_stage
    ↑
mli_mapping
```

These are simple one-to-one transformations.

The interesting dependencies will appear in the next exercise when we start joining tables.

---

# Compile the Repository

Click:

```text
Compile
```

Dataform should successfully compile.

If compilation fails:

- verify dataset names
- verify spelling
- verify SQL syntax

---

# Run the STAGE Models

Click:

```text
Start Execution
```

Select:

```text
sales_stage
dealer_stage
mapping_stage
```

Execute the models.

Wait for successful completion.

---

# Verify in BigQuery

Navigate to:

```text
BigQuery Studio
```

Open:

```text
<your_name>_stage
```

You should see:

```text
sales_stage
dealer_stage
mapping_stage
```

---

# Validate Record Counts

Run:

```sql
SELECT COUNT(*) FROM `<your_name>_stage.sales_stage`;
```

Expected:

```text
10000
```

---

Run:

```sql
SELECT COUNT(*) FROM `<your_name>_stage.dealer_stage`;
```

Expected:

```text
10000
```

---

Run:

```sql
SELECT COUNT(*) FROM `<your_name>_stage.mapping_stage`;
```

Expected:

```text
10000
```

---

# Data Quality Validation

Now let's perform the same checks we used on the RAW layer.

---

## Check MLI Uniqueness

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT MLI) AS distinct_mli
FROM `<your_name>_stage.mapping_stage`;
```

Expected:

```text
total_rows = distinct_mli
```

---

## Check DealerCode Uniqueness

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT DealerCode) AS distinct_dealers
FROM `<your_name>_stage.dealer_stage`;
```

Expected:

```text
total_rows = distinct_dealers
```

---

# Why is this important?

The STAGE layer is where we establish trust in the data.

Every later layer assumes:

- values are standardized
- data types are correct
- keys are clean
- records are usable

If the STAGE layer is unreliable, every downstream layer becomes unreliable.

---

# Checkpoint

You should now have:

✓ sales_stage

✓ dealer_stage

✓ mapping_stage

inside:

```text
<your_name>_stage
```

and successfully created your first Dataform models.

---

# What comes next?

In the next exercise we will create our first real business transformation.

We will:

- JOIN the tables
- enrich sales records
- add dealer names
- add product classifications

and build our first INTERMEDIATE layer model.