gcloud deployment-manager deployments delete postgres-deployment -q
gcloud deployment-manager deployments create postgres-deployment --config postgres_deployment.yaml
