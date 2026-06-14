DECLARE username STRING DEFAULT "janos";
DECLARE project_id STRING DEFAULT "ford-training-430008";

DECLARE raw_dataset STRING DEFAULT FORMAT("%s_raw", username);
DECLARE stage_dataset STRING DEFAULT FORMAT("%s_stage", username);
DECLARE gold_dataset STRING DEFAULT FORMAT("%s_gold", username);
DECLARE config_dataset STRING DEFAULT "training_config";
DECLARE assertion_dataset STRING DEFAULT "assertions";

-- The run log is kept as a table, but its rows are cleared before a clean demo.
EXECUTE IMMEDIATE FORMAT(
  "TRUNCATE TABLE `%s.%s.file_ingestion_run_log`",
  project_id,
  config_dataset
);

-- RAW tables are created by the Cloud Run importer from the config table.
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.sales`", project_id, raw_dataset);
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.dealer_master`", project_id, raw_dataset);
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.mli_mapping`", project_id, raw_dataset);

-- STAGE and intermediate tables are created by Dataform.
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.sales_stage`", project_id, stage_dataset);
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.dealer_stage`", project_id, stage_dataset);
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.mapping_stage`", project_id, stage_dataset);
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.sales_enriched`", project_id, stage_dataset);

-- GOLD tables are created by Dataform.
EXECUTE IMMEDIATE FORMAT("DROP TABLE IF EXISTS `%s.%s.sales_gold`", project_id, gold_dataset);

-- Dataform assertions are created in the default assertion dataset.
EXECUTE IMMEDIATE FORMAT("DROP VIEW IF EXISTS `%s.%s.assertion_sales_stage_required_fields`", project_id, assertion_dataset);
EXECUTE IMMEDIATE FORMAT("DROP VIEW IF EXISTS `%s.%s.assertion_sales_stage_numeric_fields`", project_id, assertion_dataset);
EXECUTE IMMEDIATE FORMAT("DROP VIEW IF EXISTS `%s.%s.assertion_sales_enriched_dealer_join`", project_id, assertion_dataset);
EXECUTE IMMEDIATE FORMAT("DROP VIEW IF EXISTS `%s.%s.assertion_sales_enriched_mapping_join`", project_id, assertion_dataset);
EXECUTE IMMEDIATE FORMAT("DROP VIEW IF EXISTS `%s.%s.assertion_sales_gold_positive_metrics`", project_id, assertion_dataset);
EXECUTE IMMEDIATE FORMAT("DROP VIEW IF EXISTS `%s.%s.assertion_sales_gold_unique_market_segment_model`", project_id, assertion_dataset);
