
## Prepare Database Dump

```
# stop the service, double check volume name (compose may prefix with project)
# docker system df -v | sed -n '/VOLUME NAME/,/^ *$/p'
docker run --rm -v home_mariadb_data:/source -v $(pwd):/backup alpine tar -cvf /backup/mariadb-backup.tar -C /source .
```

## Migration (with helm values)

Set Helm Chart Values:
- mariaDB.migrationPodEnabled (true)
- mariaDB.migrationCompleted (false)

Apply upgrade the cluster

```
kubectl cp mariadb-backup.tar home-internal/migration-pod:/data/mariadb-backup.tar
kubectl exec -it migration-pod -n home-internal -- bash

# Inside the pod, run these commands:
cd /data
tar xvf mariadb-backup.tar
rm mariadb-backup.tar
chown -R 999:999 /data
exit

kubectl delete pod migration-pod -n home-internal 
```

## Ready to Start the Services

Set Helm Chart Values:
- mariaDB.migrationPodEnabled (false)
- mariaDB.migrationCompleted (true)

Apply upgrade the cluster


```
# to verify user & data
kubectl exec -it -n home-internal deployment/mariadb -- mariadb -u homeassistant -p
SHOW DATABASES;
USE homeassistant;
SHOW TABLES;
SELECT COUNT(*) FROM statistics;
SELECT COUNT(*) FROM statistics_runs;
```


## Note on Home Assistant user files

copying must preserve permissions

```
sudo tar --exclude "backups" -cvpzf ha_config.tar.gz -C ./config/ha .
```