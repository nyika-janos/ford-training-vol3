# 05 - Create STAGE Models

## Objective

In this exercise we will examine the STAGE layer and execute our first Dataform transformations.

The purpose of the STAGE layer is not to implement business logic.

Its purpose is to prepare the data for later processing.

Typical STAGE activities include:

- data type harmonization
- column standardization
- trimming text values
- converting keys into a consistent format
- preparing data for joins

At the end of this exercise you will have three STAGE tables:

```text
<your_name>_stage.sales_stage
<your_name>_stage.dealer_stage
<your_name>_stage.mapping_stage
```

---

# Why Do We Need a STAGE Layer?

Many people are tempted to join and aggregate data directly from the RAW tables.

This usually works at the beginning.

Over time however:

- source systems change
- data types change
- file formats change
- additional business rules appear

The STAGE layer acts as a protective boundary between source systems and business logic.

A good rule of thumb is:

```text
RAW = What we received

STAGE = What we trust
```

---

# Review the Data Warehouse Layers

Our warehouse currently looks like this:

```text
RAW
├── sales_data
├── dealer_master
└── mli_mapping
```

Today we will create:

```text
STAGE
├── sales_stage
├── dealer_stage
└── mapping_stage
```

Later we will build:

```text
INTERMEDIATE
└── sales_enriched

GOLD
└── sales_gold
```

---

# Open sales_stage.sqlx

Navigate to:

```text
definitions/sales_stage.sqlx
```

Review the model.

---

# Review the Configuration Block

At the top of the file you should see:

```sql
config {
  type: "table",
  schema: require("../includes/config").stage_dataset,
  name: "sales_stage"
}
```

This tells Dataform:

- create a table
- place it into the STAGE dataset
- name the table sales_stage

Notice that we do not hardcode:

```text
janos_stage
```

or

```text
barni_stage
```

The dataset is generated automatically from the username.

---

# Review the Source Table

Locate:

```sql
FROM `${raw_dataset}.sales_data`
```

This is our RAW source table.

Remember:

```text
RAW tables are never modified.
```

Every transformation happens in a new layer.

---

# Review the Data Type Conversion

Locate:

```sql
CAST(MLI AS STRING) AS MLI
```

Why is this needed?

Because the CSV import created:

```text
MLI = INTEGER
```

However:

```text
MLI
```

is actually a business key.

Business keys are usually treated as strings.

This avoids future problems when:

```text
0001
0010
0100
1000
```

need to be represented.

---

# Review Additional Standardization

Notice:

```sql
UPPER(Market)
```

and

```sql
TRIM(DealerCode)
```

These are simple but important transformations.

They help prevent issues such as:

```text
HU
Hu
hu
HU
```

being treated as different values.

---

# Compile sales_stage.sqlx

Click:

```text
Compile
```

The model should compile successfully.

---

# Open dealer_stage.sqlx

Navigate to:

```text
definitions/dealer_stage.sqlx
```

Review the model.

---

# Purpose of dealer_stage

This model prepares dealer master data.

The transformations are intentionally simple:

```sql
UPPER(Market)

TRIM(DealerCode)

TRIM(DealerName)
```

The goal is consistency.

Dealer information will later be joined with sales data.

---

# Compile dealer_stage.sqlx

Verify that the model compiles successfully.

---

# Open mapping_stage.sqlx

Navigate to:

```text
definitions/mapping_stage.sqlx
```

Review the model.

---

# Purpose of mapping_stage

This table contains business mappings.

In the original Alteryx workflows this mapping came from an Excel file.

Examples:

```text
MLI
Basket
PCT
MPL_Code
```

The purpose of this model is to prepare those values for later enrichment.

---

# Review the MLI Conversion

Locate:

```sql
CAST(MLI AS STRING) AS MLI
```

Again we convert MLI to STRING.

This ensures that:

```text
sales_stage.MLI
```

and

```text
mapping_stage.MLI
```

have the same data type.

This is essential for successful joins.

---

# Compile mapping_stage.sqlx

Verify successful compilation.

---

# Execute Individual Models

We will now execute the three STAGE models.

Run:

```text
sales_stage
```

Wait until execution completes.

---

Run:

```text
dealer_stage
```

Wait until execution completes.

---

Run:

```text
mapping_stage
```

Wait until execution completes.

---

# Verify the Generated Tables

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

# Inspect sales_stage

Run:

```sql
SELECT *
FROM `<your_name>_stage.sales_stage`
LIMIT 20;
```

Review:

- Market
- DealerCode
- MLI
- Month
- Qty
- Revenue

---

# Verify the MLI Data Type

Open the schema.

Confirm that:

```text
MLI
```

is now:

```text
STRING
```

This is one of the key objectives of the STAGE layer.

---

# Compare RAW vs STAGE

RAW:

```text
Original source structure
```

STAGE:

```text
Standardized structure
```

Notice that the business meaning has not changed.

We have only improved consistency and usability.

---

# Checkpoint

You should now have:

✓ sales_stage

✓ dealer_stage

✓ mapping_stage

✓ Successful execution

✓ Verified schemas

✓ Standardized business keys

---

# What Comes Next?

The STAGE layer prepares the data.

In the next exercise we will create the first business transformation layer.

We will join:

```text
sales_stage
+
dealer_stage
+
mapping_stage
```

to create an enriched dataset that contains both transactional and business context information.