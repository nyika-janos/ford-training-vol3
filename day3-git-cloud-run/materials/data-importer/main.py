import base64
import json
import os
import tempfile
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from google.cloud import bigquery
from google.cloud import storage


app = Flask(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID")
CONFIG_DATASET = os.environ.get("CONFIG_DATASET", "training_config")
CONFIG_TABLE = os.environ.get("CONFIG_TABLE", "file_ingestion_config")
RUN_LOG_TABLE = os.environ.get("RUN_LOG_TABLE", "file_ingestion_run_log")

LANDING_PREFIX = os.environ.get("LANDING_PREFIX", "landing/")
PROCESSED_PREFIX = os.environ.get("PROCESSED_PREFIX", "processed/")
ARCHIVE_PREFIX = os.environ.get("ARCHIVE_PREFIX", "archive/")
ERROR_PREFIX = os.environ.get("ERROR_PREFIX", "error/")
ARCHIVE_SUCCESS_COPY = os.environ.get("ARCHIVE_SUCCESS_COPY", "true").lower() == "true"

bq_client = bigquery.Client(project=PROJECT_ID)
PROJECT_ID = PROJECT_ID or bq_client.project
storage_client = storage.Client(project=PROJECT_ID)


def utc_now():
    return datetime.now(timezone.utc)


def decode_pubsub_request(payload):
    """Decode a Pub/Sub push envelope and return the original GCS event."""
    if not payload or "message" not in payload:
        raise ValueError("Request is not a Pub/Sub push message.")

    message = payload["message"]
    attributes = message.get("attributes", {})
    event_id = message.get("messageId") or message.get("message_id") or str(uuid.uuid4())

    data = message.get("data")
    if data:
        decoded = base64.b64decode(data).decode("utf-8")
        try:
            event = json.loads(decoded)
        except json.JSONDecodeError:
            event = {}
    else:
        event = {}

    bucket_name = (
        event.get("bucket")
        or event.get("bucketId")
        or attributes.get("bucketId")
        or attributes.get("bucket")
    )
    object_name = (
        event.get("name")
        or event.get("objectId")
        or attributes.get("objectId")
        or attributes.get("name")
    )
    object_generation = (
        event.get("generation")
        or attributes.get("objectGeneration")
        or attributes.get("generation")
    )

    if not object_generation and event.get("id"):
        object_generation = str(event["id"]).rsplit("/", 1)[-1]

    if not bucket_name or not object_name:
        raise ValueError("Could not find bucket or object name in Pub/Sub message.")

    return {
        "event_id": event_id,
        "bucket_name": bucket_name,
        "object_name": object_name,
        "object_generation": str(object_generation) if object_generation else None,
        "raw_event": event,
        "attributes": attributes,
    }


def config_table_ref():
    return f"`{PROJECT_ID}.{CONFIG_DATASET}.{CONFIG_TABLE}`"


def run_log_table_ref():
    return f"{PROJECT_ID}.{CONFIG_DATASET}.{RUN_LOG_TABLE}"


def already_processed(event):
    query = f"""
        SELECT 1
        FROM `{run_log_table_ref()}`
        WHERE bucket_name = @bucket_name
          AND object_name = @object_name
          AND COALESCE(object_generation, "") = COALESCE(@object_generation, "")
          AND status IN ("SUCCESS", "SUCCESS_MOVE_FAILED")
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("bucket_name", "STRING", event["bucket_name"]),
            bigquery.ScalarQueryParameter("object_name", "STRING", event["object_name"]),
            bigquery.ScalarQueryParameter(
                "object_generation", "STRING", event.get("object_generation")
            ),
        ]
    )
    rows = list(bq_client.query(query, job_config=job_config).result())
    return bool(rows)


def find_matching_configs(object_name):
    query = f"""
        SELECT *
        FROM {config_table_ref()}
        WHERE enabled = TRUE
          AND REGEXP_CONTAINS(@object_name, file_pattern)
        ORDER BY priority, config_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("object_name", "STRING", object_name)
        ]
    )
    rows = bq_client.query(query, job_config=job_config).result()
    return [dict(row.items()) for row in rows]


def normalize_prefix(prefix):
    return prefix if prefix.endswith("/") else f"{prefix}/"


def object_target_name(source_name, target_prefix):
    source_path = Path(source_name)
    target_prefix = normalize_prefix(target_prefix)
    return f"{target_prefix}{source_path.name}"


def timestamped_object_target_name(source_name, target_prefix):
    source_path = Path(source_name)
    target_prefix = normalize_prefix(target_prefix)
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    target_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
    return f"{target_prefix}{target_name}"


def copy_blob(bucket_name, source_name, target_name):
    bucket = storage_client.bucket(bucket_name)
    source_blob = bucket.blob(source_name)
    bucket.copy_blob(source_blob, bucket, target_name)


def move_blob(bucket_name, source_name, target_name):
    copy_blob(bucket_name, source_name, target_name)
    storage_client.bucket(bucket_name).blob(source_name).delete()


def move_to_error(bucket_name, object_name):
    move_blob(bucket_name, object_name, object_target_name(object_name, ERROR_PREFIX))


def move_to_processed(bucket_name, object_name):
    if ARCHIVE_SUCCESS_COPY:
        copy_blob(
            bucket_name,
            object_name,
            timestamped_object_target_name(object_name, ARCHIVE_PREFIX),
        )
    move_blob(
        bucket_name,
        object_name,
        timestamped_object_target_name(object_name, PROCESSED_PREFIX),
    )


def download_to_tmp(bucket_name, object_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    suffix = Path(object_name).suffix
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    blob.download_to_filename(tmp_path)
    return tmp_path


def target_table_id(config):
    project = config.get("target_project") or PROJECT_ID
    dataset = config["target_dataset"]
    table = config["target_table"]
    return f"{project}.{dataset}.{table}"


def configured_schema_fields(config):
    target_schema = config.get("target_schema") or []
    if not target_schema:
        return []

    fields = []

    for column in target_schema:
        column_name = column.get("column_name")
        data_type = column.get("data_type") or "STRING"
        mode = column.get("mode") or "NULLABLE"

        if not column_name:
            raise ValueError(f"target_schema contains a column without name: {config['config_id']}")

        fields.append(bigquery.SchemaField(column_name, data_type, mode=mode))

    if config.get("add_metadata_columns", True):
        fields.extend(
            [
                bigquery.SchemaField("_source_bucket", "STRING"),
                bigquery.SchemaField("_source_object", "STRING"),
                bigquery.SchemaField("_ingestion_config_id", "STRING"),
                bigquery.SchemaField("_ingested_at_utc", "TIMESTAMP"),
            ]
        )

    return fields


def ensure_target_table(config):
    schema = configured_schema_fields(config)
    if not schema:
        return

    table_id = target_table_id(config)
    table = bigquery.Table(table_id, schema=schema)
    bq_client.create_table(table, exists_ok=True)


def validate_expected_columns(df, config):
    expected_columns = config.get("expected_columns") or []
    if not expected_columns:
        return

    missing_columns = [column for column in expected_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing expected columns for config {config['config_id']}: "
            f"{', '.join(missing_columns)}"
        )


def add_metadata_columns(df, bucket_name, object_name, config_id):
    df["_source_bucket"] = bucket_name
    df["_source_object"] = object_name
    df["_ingestion_config_id"] = config_id
    df["_ingested_at_utc"] = utc_now()
    return df


def read_excel_sheet(file_path, config):
    header_row = int(config.get("header_row") or 1)
    skip_rows = int(config.get("skip_rows") or 0)
    sheet_name = config.get("sheet_name")

    if not sheet_name:
        raise ValueError(f"sheet_name is required for Excel config {config['config_id']}.")

    return pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=header_row - 1,
        skiprows=skip_rows,
        dtype=str,
        engine="openpyxl",
    )


def read_csv_file(file_path, config):
    header_row = int(config.get("header_row") or 1)
    skip_rows = int(config.get("skip_rows") or 0)
    delimiter = config.get("field_delimiter") or ","
    encoding = config.get("encoding") or "utf-8"

    return pd.read_csv(
        file_path,
        header=header_row - 1,
        skiprows=skip_rows,
        delimiter=delimiter,
        encoding=encoding,
        dtype=str,
    )


def load_dataframe_to_bigquery(df, config):
    table_id = target_table_id(config)
    write_disposition = config.get("write_disposition") or "WRITE_APPEND"
    schema = configured_schema_fields(config)

    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
        autodetect=not bool(schema),
        schema=schema or None,
    )
    load_job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load_job.result()
    return table_id, len(df.index)


def process_file(bucket_name, object_name, configs):
    tmp_path = download_to_tmp(bucket_name, object_name)
    loaded_tables = []

    try:
        for config in configs:
            source_format = (config.get("source_format") or "").upper()

            if source_format in ("XLSX", "EXCEL"):
                df = read_excel_sheet(tmp_path, config)
            elif source_format == "CSV":
                df = read_csv_file(tmp_path, config)
            else:
                raise ValueError(
                    f"Unsupported source_format '{source_format}' "
                    f"for config {config['config_id']}."
                )

            validate_expected_columns(df, config)
            ensure_target_table(config)

            if config.get("add_metadata_columns", True):
                df = add_metadata_columns(df, bucket_name, object_name, config["config_id"])

            table_id, row_count = load_dataframe_to_bigquery(df, config)
            loaded_tables.append(f"{table_id} ({row_count} rows)")

        return loaded_tables
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def insert_run_log(
    run_id,
    event,
    status,
    message,
    started_at,
    finished_at,
    configs=None,
    target_tables=None,
):
    row = {
        "run_id": run_id,
        "event_id": event["event_id"],
        "bucket_name": event["bucket_name"],
        "object_name": event["object_name"],
        "object_generation": event.get("object_generation"),
        "status": status,
        "message": message,
        "config_ids": [config["config_id"] for config in configs or []],
        "target_tables": target_tables or [],
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
    }
    errors = bq_client.insert_rows_json(run_log_table_ref(), [row])
    if errors:
        app.logger.error("Failed to insert run log: %s", errors)


@app.route("/", methods=["POST"])
def import_file():
    run_id = str(uuid.uuid4())
    started_at = utc_now()
    event = None
    configs = []

    try:
        event = decode_pubsub_request(request.get_json(silent=True))
        bucket_name = event["bucket_name"]
        object_name = event["object_name"]

        if not object_name.startswith(LANDING_PREFIX):
            return jsonify({"status": "ignored", "reason": "object is not in landing"}), 200

        if Path(object_name).name == ".keep":
            return jsonify({"status": "ignored", "reason": "placeholder object"}), 200

        if already_processed(event):
            return jsonify({"status": "duplicate_ignored", "object": object_name}), 200

        configs = find_matching_configs(object_name)
        if not configs:
            message = f"No enabled ingestion config matched object: {object_name}"
            move_to_error(bucket_name, object_name)
            insert_run_log(
                run_id,
                event,
                "UNKNOWN_CONFIG",
                message,
                started_at,
                utc_now(),
            )
            return jsonify({"status": "unknown_config", "message": message}), 200

        loaded_tables = process_file(bucket_name, object_name, configs)

        try:
            move_to_processed(bucket_name, object_name)
        except Exception as exc:
            message = (
                "File was loaded into BigQuery, but moving the original object failed: "
                f"{exc}"
            )
            insert_run_log(
                run_id,
                event,
                "SUCCESS_MOVE_FAILED",
                message,
                started_at,
                utc_now(),
                configs=configs,
                target_tables=loaded_tables,
            )
            app.logger.error(message)
            return jsonify(
                {
                    "status": "success_move_failed",
                    "message": message,
                    "loaded_tables": loaded_tables,
                }
            ), 200

        message = "File processed successfully."
        insert_run_log(
            run_id,
            event,
            "SUCCESS",
            message,
            started_at,
            utc_now(),
            configs=configs,
            target_tables=loaded_tables,
        )
        return jsonify({"status": "success", "loaded_tables": loaded_tables}), 200

    except Exception as exc:
        app.logger.error("Importer failed: %s", traceback.format_exc())

        if event:
            try:
                move_to_error(event["bucket_name"], event["object_name"])
            except Exception:
                app.logger.error("Failed to move object to error: %s", traceback.format_exc())

            try:
                insert_run_log(
                    run_id,
                    event,
                    "FAILED",
                    str(exc),
                    started_at,
                    utc_now(),
                    configs=configs,
                )
            except Exception:
                app.logger.error("Failed to write failure log: %s", traceback.format_exc())

        return jsonify({"status": "failed", "message": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
