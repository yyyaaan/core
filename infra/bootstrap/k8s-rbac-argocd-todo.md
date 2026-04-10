# Configure Headlamp (K3s API Integration)
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