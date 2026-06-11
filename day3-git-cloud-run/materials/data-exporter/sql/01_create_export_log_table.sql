CREATE SCHEMA IF NOT EXISTS `ford-training-430008.training_config`
OPTIONS (
  location = "europe-west4"
);

CREATE TABLE IF NOT EXISTS `ford-training-430008.training_config.data_export_run_log`
(
  run_id STRING NOT NULL OPTIONS(description="Az exporter futásának egyedi technikai azonosítója."),
  status STRING NOT NULL OPTIONS(description="A feldolgozás eredményállapota, például SUCCESS vagy FAILED."),
  message STRING OPTIONS(description="Rövid szöveges üzenet a futás eredményéről vagy hibájáról."),
  source_table STRING OPTIONS(description="A BigQuery forrás tábla teljes azonosítója."),
  bucket_name STRING OPTIONS(description="A Cloud Storage bucket neve, ahová az Excel export került."),
  object_name STRING OPTIONS(description="Az exportált Excel fájl objektumneve a bucketen belül."),
  row_count INT64 OPTIONS(description="Az exportált rekordok száma."),
  filters JSON OPTIONS(description="A futáskor használt opcionális szűrők JSON formában."),
  requested_by STRING OPTIONS(description="Opcionális kézi vagy orchestration azonosító, például a tréningező neve vagy Airflow DAG run id."),
  started_at TIMESTAMP NOT NULL OPTIONS(description="Az export kezdete."),
  finished_at TIMESTAMP NOT NULL OPTIONS(description="Az export vége.")
);
