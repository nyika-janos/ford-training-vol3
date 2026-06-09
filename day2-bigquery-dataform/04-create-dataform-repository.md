# 04 - Create Dataform Repository

## Objective

In this exercise we will create our first Dataform repository.

The repository will contain all transformation logic that converts our RAW data into reporting-ready GOLD tables.

At the end of this exercise you will have:

```text
<your_name>_training_dataform
```

and a development workspace connected to BigQuery.

---

# Why are we doing this?

So far we have:

```text
CSV Files
    ↓
RAW Tables
```

The next step is to transform these tables into something useful.

In Alteryx, this would typically be implemented using:

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

Think of Dataform as the orchestration layer for SQL transformations.

It helps us:

- Organize SQL code
- Build dependencies
- Create repeatable pipelines
- Manage warehouse layers
- Test data quality

---

# What is Dataform?

Dataform is a GCP-native transformation framework.

It allows us to build:

```text
RAW
 ↓
STAGE
 ↓
INTERMEDIATE
 ↓
GOLD
```

pipelines using SQL.

The actual processing is performed by BigQuery.

Dataform's job is to:

- manage models
- understand dependencies
- run objects in the correct order
- provide lineage information

---

# Dataform vs Alteryx

A simplified comparison:

| Alteryx | Dataform |
|----------|----------|
| Workflow canvas | SQL models |
| Tool dependencies | Model dependencies |
| Select Tool | SELECT |
| Filter Tool | WHERE |
| Formula Tool | SQL Expressions |
| Join Tool | JOIN |
| Summarize Tool | GROUP BY |

The logic is identical.

Only the implementation changes.

---

# Open Dataform

Navigate to:

```text
Dataform
```

from the Google Cloud Console.

---

# Create Repository

Click:

```text
Create Repository
```

---

## Repository Name

Use:

```text
<your_name>_training_dataform
```

Example:

```text
janos_training_dataform
```

---

## Region

Select:

```text
europe-west4
```

or the region specified by the trainer.

---

## Git Repository

For this exercise select:

```text
Create without a remote repository
```

We are not using Git integration yet.

Later in production environments Dataform repositories are usually connected to GitHub or GitLab.

---

## Create Repository

Click:

```text
Create
```

Wait for the repository to be provisioned.

---

# Create Workspace

After the repository is created:

Click:

```text
Create Workspace
```

Workspace name:

```text
development
```

---

# Open the Workspace

Open:

```text
development
```

You should see a structure similar to:

```text
definitions/
includes/
workflow_settings.yaml
```

---

# Understanding the Repository Structure

## definitions/

This is where most transformation models will live.

Examples:

```text
definitions/
│
├── sales_stage.sqlx
├── dealer_stage.sqlx
├── mapping_stage.sqlx
├── sales_enriched.sqlx
└── sales_gold.sqlx
```

---

## includes/

Reusable SQL logic.

Examples:

```text
common filters
shared calculations
utility functions
```

We will not use this folder today.

---

## workflow_settings.yaml

Repository configuration.

Contains:

- project id
- default dataset
- repository settings

For today's training we will mostly leave it unchanged.

---

# Connect Dataform to BigQuery

Open:

```text
workflow_settings.yaml
```

Verify that the project is:

```text
ford-training-430008
```

---

# Verify Access

Click:

```text
Start Development
```

or

```text
Compile
```

depending on the current UI version.

Dataform should successfully connect to BigQuery.

If an error appears:

- verify permissions
- verify project selection
- ask the trainer for assistance

---

# Explore the Lineage Concept

One of the biggest advantages of Dataform is dependency management.

Later we will create models like:

```text
sales_stage
```

```text
dealer_stage
```

```text
mapping_stage
```

which will feed:

```text
sales_enriched
```

which will feed:

```text
sales_gold
```

Dataform automatically understands this dependency graph.

---

# Visualizing the Future Pipeline

This is what we will build during the next exercises:

```text
mli_mapping
               \
                \
                 → sales_enriched
                /
dealer_master  /
              /
sales_data   /
                 ↓
            sales_gold
```

This should look familiar.

It is essentially the same logic we saw in the Alteryx workflows.

---

# Checkpoint

You should now have:

✓ Dataform repository

✓ Development workspace

✓ Connection to BigQuery

✓ Access to the definitions folder

---

# What comes next?

In the next exercise we will create our first Dataform models.

We will start with the STAGE layer:

```text
RAW
 ↓
STAGE
```

and perform basic cleaning operations such as:

- TRIM
- UPPER
- CAST

before moving on to joins and business logic.