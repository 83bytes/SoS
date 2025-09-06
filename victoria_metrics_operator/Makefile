repo-add:
	helm repo add vm https://victoriametrics.github.io/helm-charts/
	
repo-update:
	helm repo update

show-values:
	helm show values vm/victoria-metrics-operator > values.yaml

install: repo-update show-values
	kubectl create ns victoriametrics
	helm install vmo vm/victoria-metrics-operator -f values.yaml -n victoriametrics
