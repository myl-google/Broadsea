rm -rf supervisor/ &&
docker cp bigquery_broadsea-webtools_1:/var/log/supervisor/ . &&
cd supervisor &&
less supervisor/*stderr*
