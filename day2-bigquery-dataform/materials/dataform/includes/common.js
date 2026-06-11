function clean_string(column_name) {
  return `UPPER(TRIM(${column_name}))`;
}

module.exports = { clean_string };