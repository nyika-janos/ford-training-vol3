# 02 - Load RAW Tables

## Objective

In this exercise you will load the source files into the RAW layer of the data warehouse.

At the end of this exercise you will have the following tables:

```text
<your_name>_raw.mli_mapping
<your_name>_raw.dealer_master
<your_name>_raw.sales_data
```

These tables will be the starting point of our Dataform pipeline.

---

## Why are we doing this?

Yesterday we learned how files arrive in Cloud Storage.

Today we will focus on the warehouse side.

In a real-world solution the files would be loaded automatically by Cloud Run.

For today's exercise we will perform the loading manually so we can focus on:

- BigQuery
- Warehouse layers
- Dataform

without introducing additional components.

Our goal is to simulate the state where the ingestion process has already completed successfully.

---

# Source Files

You should have received the following files:

```text
mli_mapping.csv
dealer_master.csv
sales_data.csv
```

These files represent:

| File | Description |
|--------|--------|
| mli_mapping.csv | Product classification mapping |
| dealer_master.csv | Dealer master data |
| sales_data.csv | Sales transactions |

---

# Load mli_mapping.csv

## Step 1

Open:

```text
BigQuery Studio
```

---

## Step 2

Expand your RAW dataset.

Example:

```text
janos_raw
```

---

## Step 3

Click:

```text
Create Table
```

---

## Step 4

Configure the source.

### Create table from

Select:

```text
Upload
```

### Select file

Choose:

```text
mli_mapping.csv
```

---

## Step 5

Configure destination.

### Dataset

Select:

```text
<your_name>_raw
```

### Table Name

```text
mli_mapping
```

---

## Step 6

Configure schema.

Select:

```text
Auto detect
```

BigQuery will automatically determine:

- column names
- column types

---

## Step 7

Click:

```text
Create Table
```

Wait until the table creation finishes.

---

## Verify

Open the table.

Select:

```text
Preview
```

You should see data similar to:

| MLI | Basket | PCT | MPL_Code |
|------|------|------|------|
| 1000 | Engine | A | MPL_000 |
| 1001 | Parts | B | MPL_001 |

---

# Load dealer_master.csv

Repeat the same process.

### File

```text
dealer_master.csv
```

### Table Name

```text
dealer_master
```

---

## Verify

Preview the table.

Example data:

| Market | DealerCode | DealerName |
|---------|---------|---------|
| HU | D00001 | Dealer_1 |
| NL | D00002 | Dealer_2 |

---

# Load sales_data.csv

Repeat the same process.

### File

```text
sales_data.csv
```

### Table Name

```text
sales_data
```

---

## Verify

Preview the table.

Example data:

| Market | DealerCode | MLI | Month | Qty | Revenue |
|---------|---------|---------|---------|---------|---------|
| HU | D00001 | 1000 | 1 | 10 | 1000 |

---

# Verify All Tables

Your RAW dataset should now contain:

```text
<your_name>_raw
│
├── mli_mapping
├── dealer_master
└── sales_data
```

Example:

```text
janos_raw
│
├── mli_mapping
├── dealer_master
└── sales_data
```

---

# Why RAW?

Notice that we have not:

- renamed columns
- cleaned data
- joined tables
- applied business logic

The RAW layer should remain as close as possible to the original source.

This gives us:

- reproducibility
- auditability
- easier troubleshooting
- simpler reprocessing

The next layers will contain the actual transformations.

---

# Checkpoint

You should now have:

✓ mli_mapping table

✓ dealer_master table

✓ sales_data table

inside your RAW dataset.

---

# What comes next?

In the next exercise we will explore the data using SQL and become familiar with the contents of these tables before building our Dataform models.