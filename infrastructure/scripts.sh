# OrbStack only, needs traefik | https://docs.orbstack.dev/kubernetes/
# helm repo add traefik https://traefik.github.io/charts
# helm repo update
# helm install traefik traefik/traefik

# install cert manager | https://cert-manager.io/docs/installation/
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.20.0/cert-manager.yaml
kubectl create secret generic cloudflare-api-token --namespace cert-manager --from-env-file=./credentials/cloudflare.env
kubectl apply -f infrastructure/bootstrap/k8s-cloudflare-cert-issuer.yaml

# cloudflare tunnel
kubectl create namespace cloudflared
kubectl apply -f infrastructure/bootstrap/k8s-cloudflared-tunnel-deployment.yaml

# create namespace and secrets
kubectl create namespace home-internal
kubectl create namespace web
kubectl create secret generic email-credentials -n web --from-env-file=./credentials/active/email.env
kubectl create secret generic tz-config -n web --from-env-file=./credentials/active/tz.env
kubectl create secret generic frigate-credentials -n home-internal --from-env-file=./credentials/active/frigate.env

###
###
### build images | 
docker build -t play:local ./services/playwright # docker run --rm -p 7999:7999 play:local 

# scaling down pdf
kubectl scale deployment pdf --replicas=0
kubectl scale deployment frigate -n home-internal --replicas=0

# all the rest managed with helm
helm upgrade --install omop-fi ./infrastructure/helm-chart


## rule to allow MQTT access if necessary