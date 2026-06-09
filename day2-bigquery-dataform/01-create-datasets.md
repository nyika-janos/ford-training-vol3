# 01 - Create BigQuery Datasets

## Objective

In this exercise you will create the datasets that represent the different layers of a modern data warehouse.

At the end of this exercise you will have:

```text
<your_name>_raw
<your_name>_stage
<your_name>_gold
```

These datasets will be used throughout the rest of the training.

---

## Why are we doing this?

One of the most common mistakes in data projects is storing everything in a single dataset.

Modern data platforms separate data into layers:

```text
Landing
   ↓
RAW
   ↓
STAGE
   ↓
INTERMEDIATE
   ↓
GOLD
```

Each layer has a different responsibility.

| Layer | Purpose |
|---------|---------|
| RAW | Original data |
| STAGE | Technical cleaning |
| INTERMEDIATE | Business logic |
| GOLD | Reporting and dashboards |

Today we will use separate datasets to represent these layers.

---

## Open BigQuery Studio

1. Open the Google Cloud Console.

2. Navigate to:

```text
BigQuery Studio
```

3. Verify that you are working in the training project:

```text
ford-training-430008
```

---

## Create RAW Dataset

1. In the Explorer panel locate:

```text
ford-training-430008
```

2. Click the three dots next to the project name.

3. Select:

```text
Create Dataset
```

4. Fill the form:

### Dataset ID

Replace `<your_name>` with your own name.

Example:

```text
janos_raw
```

### Region

Select:

```text
europe-west4 (Netherlands)
```

or the region specified by the trainer.

### Expiration

Leave default values.

5. Click:

```text
Create Dataset
```

---

## Create STAGE Dataset

Repeat the previous steps.

Dataset ID:

```text
<your_name>_stage
```

Example:

```text
janos_stage
```

---

## Create GOLD Dataset

Repeat the previous steps.

Dataset ID:

```text
<your_name>_gold
```

Example:

```text
janos_gold
```

---

## Verify

Your Explorer panel should now contain:

```text
ford-training-430008
│
├── janos_raw
├── janos_stage
└── janos_gold
```

Your names will be different.

---

## Why not a single dataset?

Imagine a real production environment.

If all tables were stored together:

```text
sales_raw
sales_stage
sales_gold
dealer_raw
dealer_stage
dealer_gold
```

the environment quickly becomes difficult to understand.

Separating layers into datasets provides:

- Better organization
- Easier troubleshooting
- Cleaner permissions
- Easier maintenance

This approach is commonly used in enterprise data platforms.

---

## Checkpoint

You should now have:

✓ RAW dataset

✓ STAGE dataset

✓ GOLD dataset

---

## What comes next?

In the next exercise we will load our source files into the RAW layer.

The files are:

```text
mli_mapping.csv
dealer_master.csv
sales_data.csv
```

and these will become our first BigQuery tables.