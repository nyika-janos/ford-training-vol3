import json
import os
import re
import tempfile
import traceback
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from google.cloud import bigquery
from google.cloud import storage


app = Flask(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
GOLD_DATASET = os.environ.get("GOLD_DATASET", "janos_gold")
GOLD_TABLE = os.environ.get("GOLD_TABLE", "sales_gold")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
EXPORT_PREFIX = os.environ.get("EXPORT_PREFIX", "export/")
CONFIG_DATASET = os.environ.get("CONFIG_DATASET", "training_config")
RUN_LOG_TABLE = os.environ.get("RUN_LOG_TABLE", "data_export_run_log")

bq_client = bigquery.Client(project=PROJECT_ID)
PROJECT_ID = PROJECT_ID or bq_client.project
storage_client = storage.Client(project=PROJECT_ID)


def utc_now():
    return datetime.now(timezone.utc)


def normalize_prefix(prefix):
    return prefix if prefix.endswith("/") else f"{prefix}/"


def clean_bq_identifier(value, field_name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""):
        raise ValueError(f"Invalid BigQuery {field_name}: {value}")
    return value


def source_table_id(dataset=None, table=None):
    dataset = clean_bq_identifier(dataset or GOLD_DATASET, "dataset")
    table = clean_bq_identifier(table or GOLD_TABLE, "table")
    return f"{PROJECT_ID}.{dataset}.{table}"


def source_table_ref(dataset=None, table=None):
    return f"`{source_table_id(dataset, table)}`"


def run_log_table_id():
    return f"{PROJECT_ID}.{CONFIG_DATASET}.{RUN_LOG_TABLE}"


def clean_export_name(value):
    value = value or f"{GOLD_TABLE}_{utc_now().strftime('%Y%m%dT%H%M%SZ')}.xlsx"
    value = Path(value).name
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    if not value.lower().endswith(".xlsx"):
        value = f"{value}.xlsx"
    return value


def list_filter(name, payload):
    value = payload.get(name)
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def build_export_query(payload):
    dataset = payload.get("gold_dataset") or GOLD_DATASET
    table = payload.get("gold_table") or GOLD_TABLE

    where_clauses = []
    parameters = []

    for field in ("market", "segment", "model"):
        values = list_filter(field, payload)
        if values:
            parameter_name = f"{field}_values"
            where_clauses.append(f"{field} IN UNNEST(@{parameter_name})")
            parameters.append(
                bigquery.ArrayQueryParameter(parameter_name, "STRING", values)
            )

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT
          market,
          segment,
          model,
          dealer_count,
          total_units,
          total_revenue,
          average_unit_revenue,
          transaction_count,
          first_sales_date,
          last_sales_date
        FROM {source_table_ref(dataset, table)}
        {where_sql}
        ORDER BY market, segment, model
    """

    job_config = bigquery.QueryJobConfig(query_parameters=parameters)
    return query, job_config, source_table_id(dataset, table)


def normalize_cell(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def query_to_dataframe(query, job_config):
    rows_iter = bq_client.query(query, job_config=job_config).result()
    rows = list(rows_iter)
    columns = [field.name for field in rows_iter.schema]
    normalized_rows = [
        {column: normalize_cell(row[column]) for column in columns}
        for row in rows
    ]
    return pd.DataFrame(normalized_rows, columns=columns)


def write_excel(df, run_id, source_table, filters):
    fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)

    with pd.ExcelWriter(tmp_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="sales_gold", index=False)

        export_info = pd.DataFrame(
            [
                {"key": "run_id", "value": run_id},
                {"key": "source_table", "value": source_table},
                {"key": "exported_at_utc", "value": utc_now().isoformat()},
                {"key": "row_count", "value": len(df.index)},
                {"key": "filters", "value": json.dumps(filters, ensure_ascii=False)},
            ]
        )
        export_info.to_excel(writer, sheet_name="export_info", index=False)

        workbook = writer.book
        for worksheet in workbook.worksheets:
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                values = [str(cell.value) for cell in column_cells if cell.value is not None]
                width = min(max([len(value) for value in values] + [10]) + 2, 36)
                worksheet.column_dimensions[column_cells[0].column_letter].width = width

    return tmp_path


def upload_export(tmp_path, bucket_name, object_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_filename(
        tmp_path,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def insert_run_log(
    run_id,
    status,
    message,
    source_table,
    bucket_name,
    object_name,
    row_count,
    filters,
    requested_by,
    started_at,
    finished_at,
):
    row = {
        "run_id": run_id,
        "status": status,
        "message": message,
        "source_table": source_table,
        "bucket_name": bucket_name,
        "object_name": object_name,
        "row_count": row_count,
        "filters": filters or {},
        "requested_by": requested_by,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
    }
    errors = bq_client.insert_rows_json(run_log_table_id(), [row])
    if errors:
        app.logger.error("Failed to insert export run log: %s", errors)


@app.route("/", methods=["POST"])
def export_gold():
    run_id = str(uuid.uuid4())
    started_at = utc_now()
    payload = request.get_json(silent=True) or {}

    bucket_name = payload.get("bucket_name") or BUCKET_NAME
    if not bucket_name:
        return jsonify({"status": "failed", "message": "BUCKET_NAME is required."}), 400

    requested_by = payload.get("requested_by")
    filters = {
        "market": list_filter("market", payload),
        "segment": list_filter("segment", payload),
        "model": list_filter("model", payload),
    }
    filters = {key: value for key, value in filters.items() if value}

    export_name = clean_export_name(payload.get("export_name"))
    object_name = f"{normalize_prefix(payload.get('export_prefix') or EXPORT_PREFIX)}{export_name}"
    tmp_path = None
    source_table = source_table_id(payload.get("gold_dataset"), payload.get("gold_table"))

    try:
        query, job_config, source_table = build_export_query(payload)
        df = query_to_dataframe(query, job_config)
        tmp_path = write_excel(df, run_id, source_table, filters)
        upload_export(tmp_path, bucket_name, object_name)

        message = "Gold export created successfully."
        insert_run_log(
            run_id,
            "SUCCESS",
            message,
            source_table,
            bucket_name,
            object_name,
            len(df.index),
            filters,
            requested_by,
            started_at,
            utc_now(),
        )
        return jsonify(
            {
                "status": "success",
                "run_id": run_id,
                "source_table": source_table,
                "row_count": len(df.index),
                "export_uri": f"gs://{bucket_name}/{object_name}",
            }
        ), 200

    except Exception as exc:
        app.logger.error("Exporter failed: %s", traceback.format_exc())
        try:
            insert_run_log(
                run_id,
                "FAILED",
                str(exc),
                source_table,
                bucket_name,
                object_name,
                None,
                filters,
                requested_by,
                started_at,
                utc_now(),
            )
        except Exception:
            app.logger.error("Failed to write failure log: %s", traceback.format_exc())

        return jsonify({"status": "failed", "run_id": run_id, "message": str(exc)}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
