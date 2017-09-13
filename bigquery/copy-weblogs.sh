rm -rf supervisor/ &&
docker cp bigquery_broadsea-webtools_1:/var/log/supervisor/ . &&
less supervisor/*stderr*
