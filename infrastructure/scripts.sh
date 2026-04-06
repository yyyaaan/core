# Orbstack, needs traefik | https://docs.orbstack.dev/kubernetes/
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm install traefik traefik/traefik

# install cert manager | https://cert-manager.io/docs/installation/
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.20.0/cert-manager.yaml
kubectl create secret generic cloudflare-api-token --namespace cert-manager --from-env-file=./credentials/cloudflare.env
kubectl apply -f infrastructure/bootstrap/k8s-cloudflare-cert-issuer.yaml

# cloudflare tunnel
kubectl create namespace cloudflared
kubectl apply -f infrastructure/bootstrap/k8s-cloudflared-tunnel-deployment.yaml

# build images | 
docker build -t play:local ./services/playwright # docker run --rm -p 7999:7999 play:local 

# create secrets
kubectl create secret generic frigate-credentials --from-env-file=./credentials/frigate.env


# all the rest managed with helm
helm upgrade --install v0 ./infrastructure/helm-chart


kubectl scale deployment pdf --replicas=0
