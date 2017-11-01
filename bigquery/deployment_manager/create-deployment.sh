gcloud deployment-manager deployments create broadsea-deployment44 --config deploy.yaml
gcloud sql users create ohdsi-postgres-user --instance=broadsea-deployment44-postgres --password=ohdsi-postgres-password 
