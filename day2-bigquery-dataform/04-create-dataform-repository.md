# 04 - Create Dataform Repository

## Objective

In this exercise we will create a Dataform repository and prepare it for development.

We will not write SQL from scratch.

Instead, we will use a pre-built repository structure that already contains the Dataform models we will use throughout the training.

At the end of this exercise you will have:

```text
<your_name>_training_dataform
```

connected to BigQuery and ready for development.

---

# Why are we doing this?

So far we have created the RAW layer:

```text
CSV Files
    ↓
BigQuery RAW Tables
```

The next step is to transform the data into a reporting-ready warehouse.

In Alteryx this would be implemented using:

- Select
- Formula
- Filter
- Join
- Summarize

tools connected together in a workflow.

In GCP we will implement the same logic using:

```text
BigQuery
+
Dataform
```

---

# What is Dataform?

Dataform is a GCP-native transformation framework.

It helps us:

- organize SQL code
- create reusable transformation pipelines
- manage dependencies
- create data quality checks
- build warehouse layers

The actual processing is still performed by BigQuery.

Dataform orchestrates and manages the transformations.

---

# Open Dataform

Navigate to:

```text
Dataform
```

in the Google Cloud Console.

---

# Create Repository

Click:

```text
Create Repository
```

Repository name:

```text
<your_name>_training_dataform
```

Example:

```text
janos_training_dataform
```

Region:

```text
europe-west4
```

---

# Git Integration

For this exercise select:

```text
Create without a remote repository
```

We will manually import the training files.

Later, in real projects, Dataform repositories are usually connected to GitHub or GitLab.

---

# Create Workspace

After the repository has been created:

Click:

```text
Create Workspace
```

Workspace name:

```text
development
```

Open the workspace.

---

# Review the Repository Structure

You should see something similar to:

```text
definitions/
includes/
workflow_settings.yaml
```

---

# Configure workflow_settings.yaml

Open:

```text
workflow_settings.yaml
```

Replace the contents with:

```yaml
defaultProject: ford-training-430008
defaultLocation: europe-west4
defaultAssertionDataset: assertions

vars:
  username: "janos"
```

Replace:

```text
janos
```

with your own first name.

Examples:

```yaml
vars:
  username: "barni"
```

```yaml
vars:
  username: "tianze"
```

```yaml
vars:
  username: "adam"
```

---

# Why are we storing the username here?

Throughout the training every participant will have their own datasets:

```text
janos_raw
janos_stage
janos_gold
```

or:

```text
barni_raw
barni_stage
barni_gold
```

Instead of hardcoding these names throughout the project, we store the username once and generate everything else automatically.

---

# Download the Training Repository

Open:

[ford-training-vol3-day2-dataform-repo](https://github.com/nyika-janos/ford-training-vol3-day2-dataform-repo?utm_source=chatgpt.com)

Download:

```text
Code
↓
Download ZIP
```

Extract the archive locally.

---

# Review the Repository Structure

Inside the downloaded repository you will find:

```text
definitions/
includes/
```

The files have already been prepared for this training.

---

# Upload the Training Files

Copy the contents of:

```text
definitions/
```

from the downloaded repository into your Dataform repository.

Copy the contents of:

```text
includes/
```

into your Dataform repository.

Your structure should now look like:

```text
definitions/
├── dealer_stage.sqlx
├── mapping_stage.sqlx
├── sales_stage.sqlx
├── sales_enrich.sqlx
└── sales_gold.sqlx

includes/
└── config.js
```

---

# Review includes/config.js

Open:

```text
includes/config.js
```

This file automatically generates dataset names based on the username stored in:

```yaml
workflow_settings.yaml
```

For example:

```yaml
username: "janos"
```

automatically becomes:

```text
janos_raw
janos_stage
janos_gold
```

This approach prevents hardcoding dataset names throughout the project.

---

# Review the Model Structure

Open:

```text
sales_stage.sqlx
```

Notice:

```sql
schema: require("../includes/config").stage_dataset
```

The dataset name is generated dynamically.

The same pattern is used throughout the repository.

---

# Compile the Repository

Click:

```text
Compile
```

The compilation should complete successfully.

If compilation fails:

- verify the username
- verify workflow_settings.yaml
- verify that all files were copied correctly

---

# Checkpoint

You should now have:

✓ Dataform repository

✓ Development workspace

✓ workflow_settings.yaml configured

✓ definitions imported

✓ includes imported

✓ Successful compilation

---

# What comes next?

In the next exercise we will review the STAGE models and execute the first transformations.

We will clean and standardize the RAW data before applying business logic.