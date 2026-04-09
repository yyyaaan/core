This is a solid "weekend project" that will transform your Raspberry Pi into a production-grade environment. Since you have your own Google Workspace domain (`yan.fi`), you're in a great position to use a single set of credentials for everything.

Here are the end-to-end steps to wire this up.

---

### Phase 1: Google Cloud Console Setup
You need one set of credentials from Google to act as the "Identity Provider."

1.  **Create/Select a Project:** Go to the [GCP Console](https://console.cloud.google.com/).
2.  **OAuth Consent Screen:**
    * Set **User Type** to **Internal** (This limits access strictly to `@yan.fi` accounts).
    * Add `openid`, `https://www.googleapis.com/auth/userinfo.email`, and `https://www.googleapis.com/auth/userinfo.profile` to scopes.
3.  **Create Credentials:**
    * Go to **Credentials** > **Create Credentials** > **OAuth client ID**.
    * Select **Web application**.
    * **Authorized Redirect URIs:**
        * `https://argocd.yan.fi/auth/callback`
        * `https://headlamp.yan.fi/oidc/callback`
4.  **Save your Client ID and Client Secret.**

---

### Phase 2: Install and Configure ArgoCD
Since you have 8GB RAM, we'll install the standard version but skip the High Availability (HA) features to stay lean.

#### 1. Installation
```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

#### 2. Configure Insecure Mode (for Traefik)
ArgoCD needs to know Traefik is handling the SSL.
```bash
kubectl patch configmap argocd-cmd-params-cm -n argocd \
  --type merge \
  -p '{"data":{"server.insecure":"true"}}'
```

#### 3. Configure OIDC & RBAC
Update your ConfigMaps to use Google.

**The Config (`argocd-cm`):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  url: https://argocd.yan.fi
  oidc.config: |
    name: Google
    issuer: https://accounts.google.com
    clientID: <YOUR_CLIENT_ID>
    clientSecret: <YOUR_CLIENT_SECRET>
    config:
      hostedDomains:
        - yan.fi
```

**The Permissions (`argocd-rbac-cm`):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    g, yourname@yan.fi, role:admin
```

#### 4. Expose via Traefik (IngressRoute)
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: argocd-server
  namespace: argocd
spec:
  entryPoints: [websecure]
  routes:
    - kind: Rule
      match: Host(`argocd.yan.fi`)
      services:
        - name: argocd-server
          port: 80
  tls:
    certResolver: cloudflare # Or whatever your resolver name is
```

---

### Phase 3: Configure Headlamp (K3s API Integration)
Headlamp doesn't "do" authentication itself; it asks the Kubernetes API if it knows who you are. We must teach K3s to recognize Google.

#### 1. Update K3s API Server Flags
On your Raspberry Pi, edit the K3s config file:
`sudo nano /etc/rancher/k3s/config.yaml`

Add these lines (merge with existing `kube-apiserver-arg` if you have any):
```yaml
kube-apiserver-arg:
  - "oidc-issuer-url=https://accounts.google.com"
  - "oidc-client-id=<YOUR_CLIENT_ID>"
  - "oidc-username-claim=email"
  - "oidc-required-claim=hd=yan.fi"
```
**Restart K3s:**
`sudo systemctl restart k3s`

#### 2. Create Cluster Admin Binding
Now tell Kubernetes that your specific email is the "Super User."
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: yan-fi-admin
subjects:
- kind: User
  name: "yourname@yan.fi"
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

#### 3. Configure Headlamp to use OIDC
Ensure your Headlamp deployment/container is running with the OIDC flags. If you used Helm to install Headlamp:
```yaml
config:
  oidc:
    clientID: <YOUR_CLIENT_ID>
    clientSecret: <YOUR_CLIENT_SECRET>
    issuerURL: https://accounts.google.com
    scopes: "openid,email,profile"
```



---

### Phase 4: Cloudflare Tunnel & "The Callback"
Because Google needs to talk back to your Pi, ensure your Cloudflare Tunnel is correctly routing these hostnames:
1.  **ArgoCD:** Point `argocd.yan.fi` to `http://traefik-service:80` (or `443` if using TLS).
2.  **Headlamp:** Point `headlamp.yan.fi` to its respective service.

**CRITICAL:** If you have **Cloudflare Access** enabled for `yan.fi`, you must go to the Zero Trust dashboard and create a **Bypass Rule** for:
* `argocd.yan.fi/auth/callback`
* `headlamp.yan.fi/oidc/callback`

This prevents Cloudflare from blocking the "Redirect" back from Google.

### Summary of your "New Reality"
* **ArgoCD:** When you hit the page, click the "Login via Google" button. It will see you are `yourname@yan.fi` and grant you `role:admin`.
* **Headlamp:** It will prompt you to "Sign in with OIDC." Once done, the K3s API will verify the token and grant you `cluster-admin` access based on your email.
* **GitOps:** Your Monorepo is now the only way you change the cluster. You push to Git $\rightarrow$ ArgoCD notices $\rightarrow$ ArgoCD deploys.

Do you have your Cloudflare Tunnel configuration in a `config.yml` file on the Pi, or are you managing it via the Cloudflare Dashboard UI? (Dashboard is usually easier for managing these specific bypass rules).