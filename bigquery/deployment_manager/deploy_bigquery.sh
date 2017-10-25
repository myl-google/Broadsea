gcloud deployment-manager deployments delete bigquery-deployment -q
gcloud deployment-manager deployments create bigquery-deployment --config bigquery_deployment.yaml
