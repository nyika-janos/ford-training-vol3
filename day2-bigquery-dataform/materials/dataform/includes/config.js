const username = dataform.projectConfig.vars.username;

module.exports = {
    username,
    raw_dataset: `${username}_raw`,
    stage_dataset: `${username}_stage`,
    gold_dataset: `${username}_gold`
};
