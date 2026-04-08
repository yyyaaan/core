
### Make the API Server Trust Google
This is the part that makes the cluster "smart" enough to read Google's tokens.

K3s is easy to configure. You edit the server config file on your Pi:
`sudo nano /etc/rancher/k3s/config.yaml`

Add these flags (Notice the new 2026 "Structured" logic if you are on K8s 1.30+):
```yaml
kube-apiserver-arg:
  - "oidc-issuer-url=https://accounts.google.com"
  - "oidc-client-id=YOUR_CLIENT_ID.apps.googleusercontent.com"
  - "oidc-username-claim=email"
  # Optional: restricts login to your specific Google Workspace domain
  # - "oidc-required-claim=hd=yourdomain.com" 
```
*Restart K3s: `sudo systemctl restart k3s`.*


---

### Map your Email to a "Manager" Role
Even if you log in, Kubernetes will say "I know who you are, but you aren't allowed to see anything." You must bind your Google identity to the **cluster-admin** role.

Create this file (`headlamp-admin-rb.yaml`):
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: google-admin-binding
subjects:
- kind: User
  name: "your-email@gmail.com" # The exact email from Google
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin # Giving yourself full power
  apiGroup: rbac.authorization.k8s.io
```
`kubectl apply -f headlamp-admin-rb.yaml`

---

### Step 4: Configure Headlamp to Use the Badge
Now update your Headlamp Helm values to show the "Login with Google" button.

```yaml
config:
  oidc:
    issuerUrl: "https://accounts.google.com"
    clientId: "YOUR_CLIENT_ID.apps.googleusercontent.com"
    clientSecret: "YOUR_CLIENT_SECRET"
    scopes: "openid,profile,email"
```



---

### Why this is the "End Game" setup
1.  **No more tokens:** You click "Login," choose your Google account, and you’re in.
2.  **True RBAC:** If you want to give a "Read-Only" view to a friend, you just add their email to a different `RoleBinding`.
3.  **Audit Logs:** In your K3s logs, you will see `user@gmail.com created a pod` instead of `system:serviceaccount:default:admin`. It’s much more professional.

**Peer Advice:** Since you are still on OrbStack, don't sweat the API server flags today. Save that battle for the day you set up the Raspberry Pi. For now, using a long-lived token (the `session-ttl` trick) is the fastest way to get your dashboard working while you finish migrating your apps.

Does the concept of **"User Identity vs. Permission (RBAC)"** feel clear now, or should we look at how to create a "Viewer" role for someone else?