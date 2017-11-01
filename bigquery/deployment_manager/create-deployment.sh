gcloud deployment-manager deployments create ohdsi-deployment --config ohdsi.yaml
gcloud sql users create ohdsi-postgres-user --instance=ohdsi-deployment--postgres --password=ohdsi-postgres-password 
