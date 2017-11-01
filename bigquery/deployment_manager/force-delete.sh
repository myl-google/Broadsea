gcloud deployment-manager deployments update ${1?} --config empty-deployment.yaml --delete-policy=ABANDON
gcloud deployment-manager deployments delete ${1?} -q
