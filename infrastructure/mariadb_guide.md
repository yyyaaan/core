
```bash
docker stop mariadb-container-name

# extract: mounts your Docker volume, mounts your current folder, zips the data up, and drops `mariadb-backup.tar` right on your machine
docker run --rm -v your_docker_volume_name:/var/lib/mysql -v $(pwd):/backup ubuntu tar cvf /backup/mariadb-backup.tar -C /var/lib/mysql .
```

**`mariadb-pvc.yaml`**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mariadb-data
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```
Apply it: `kubectl apply -f mariadb-pvc.yaml`

**`migration-pod.yaml`**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: migration-pod
  namespace: default
spec:
  containers:
  - name: migration-container
    image: ubuntu
    command: ["sleep", "infinity"] # Just stay awake and do nothing
    volumeMounts:
    - name: target-volume
      mountPath: /data
  volumes:
  - name: target-volume
    persistentVolumeClaim:
      claimName: mariadb-data # Must match your PVC name!
```
Apply it: `kubectl apply -f migration-pod.yaml`
Wait for it to be ready: `kubectl get pods`

Migration Maria DB data starts

1. **Copy the tar file into the pod:**
   ```bash
   kubectl cp mariadb-backup.tar migration-pod:/data/mariadb-backup.tar
   ```
2. **Execute into the pod to extract it:**
   ```bash
   kubectl exec -it migration-pod -- bash
   ```
3. **Inside the pod, run these commands:**
   ```bash
   cd /data
   tar xvf mariadb-backup.tar
   rm mariadb-backup.tar
   
   # CRITICAL FIX: MariaDB expects the files to be owned by the 'mysql' user (usually ID 999). 
   # If you skip this, MariaDB will crash saying "Permission Denied".
   chown -R 999:999 /data
   exit
   ```

Clean up and ready for deployment

1. **Delete the migration pod:**
   ```bash
   kubectl delete pod migration-pod
   ```
2. **Deploy your real MariaDB deployment:**
   Make sure your `deployment.yaml` mounts the `mariadb-data` PVC to `/var/lib/mysql`.

When your new MariaDB pod starts, it will look at the folder, see the existing databases, and boot up exactly where your Docker container left off.

This `tar` -> `kubectl cp` -> `chown` workflow is an essential skill for a cluster administrator. It completely bypasses the complexities of trying to figure out where OrbStack or K3s hides its files on the host OS. 

Are you ready to give this migration a try, or do you want to review the `deployment.yaml` for MariaDB to make sure the volume mounts are set up correctly first?