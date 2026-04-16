# Core Infrastructure - Kubernetes

Recommended to use git ops only! That is:
- Only install ArgoCD with `kubectl` commandline, plus the known name spaces and secrets injection
- Everything else via ArgoCD


1. Check domain is correct under infra/bootstrap
2. run `task bootstrap(-test)`
3. visit argocd `task infra:argocd:login`
4. sync in order: traefik, cert-manager, cert-cloudflare-etc, headlamp ...
3. after approving envs, disable configs.cm.admin.enabled in argocd.yaml


## Memo

- Namespaces required
- Local manifest deployments: cert issuer and Cloudflare tunnel
- Helm chart with value files: headlamp, Argo CD

> Argo CD using community managed helm chart, which is arguably anti-pattern.

Callback URL: /auth/callback for `ArgoCD`, /oidc-callback for `headlamp`

## Restic Backup Repository

The backup is organized in repo on Backblaze storage bucket (S3 compatible). The backup repo must be manually setup beforehand.

```
# restic repo one time setup, providing all necessary evn vars
restic -r s3:s3.eu-central-003.backblazeb2.com/BucketNameHere init
```

## Networking with Cloudflare

Cloudflare setups:
- Enable Cloudflare tunnel
- Zero Trust - Tunnel: Published application routes, add HTTP `traefik.traefik.svc.cluster.local:8080`, note for possible different namespace
- DNS: [should be auto created by step above] CNAME * tunnel_id.cfargotunnel.com (proxied)

## Install `k3s` on Raspberry Pi and API Server with OIDC

Raspberry Pi OS Lite is recommended for resource conservation. __DISABLE k3s default traefik__ to keep 80/443 port untouched.

Official docs at https://docs.k3s.io/installation/requirements?os=pi, and at a glance:
- check: /boot/firmware/cmdline.txt to have additional `cgroup_memory=1 cgroup_enable=memory` , and it may already exists
- check: `sudo modprobe vxlan`, if only on ERROR `sudo modprobe vxlan`
- install `curl -sfL https://get.k3s.io | sh -s - --disable traefik`

### Port configured in traefik (8080 8443 in current taskfile)

### Config API Server to trust OIDC
K3s is easy to configure. You edit the server config file on your Pi:
`sudo nano /etc/rancher/k3s/config.yaml`, and add these flags:

```yaml
kube-apiserver-arg:
  - "oidc-issuer-url=https://accounts.google.com"
  - "oidc-client-id=719690536564-hrk09vm3gjkqnpr2873q7mnff0qdcv4c.apps.googleusercontent.com"
  - "oidc-username-claim=email"
  - "oidc-required-claim=hd=yan.fi" 
```

*Restart K3s: `sudo systemctl restart k3s`.*

### Connecting to K3s remotely

```
sudo cat /etc/rancher/k3s/k3s.yaml
# copy as pi-config, update IP adress
```

registered to mac profile

```
nano ~/.zshrc
export KUBECONFIG=~/.kube/config:~/.kube/pi-config

# use context!
kubectl config get-contexts
kubectl config use-context pi-cluster
```

## Additional Manual Checks for Infra Upgrade

Manual update non-git:
- storageClassName for mariadb persistent volume
- mqtt-service or mqtt-service.home-internal or mqtt-service.home-internal.svc.cluster.local (mqtt://...:1883)
- play/public/spot & water.jpg update path in HA
- start?rd=https:// for all login button
- login page customization https://oauth2-proxy.github.io/oauth2-proxy/configuration/overview#page-template-options

Gitignored
- config/ha/secrets.yaml updated mariadb address
- config/frigate/config.yaml updated mqtt address

HA tasks
- change MQTT address

## MariaDB migration with existing data

### Prepare Database Dump

```
# stop the service, double check volume name (compose may prefix with project)
# docker system df -v | sed -n '/VOLUME NAME/,/^ *$/p'
docker run --rm -v home_mariadb_data:/source -v $(pwd):/backup alpine tar -cvf /backup/mariadb-backup.tar -C /source .
```

### Migration (with helm values)

Set Helm Chart Values:
- migrationState.migrationPodEnabled (true)
- migrationState.completed (false)

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

### Ready to Start the Services

Set Helm Chart Values:
- migrationState.migrationPodEnabled (false)
- migrationState.completed (true)

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
# create dump
sudo tar --exclude "backups" -cvpzf ha_config.tar.gz -C ./config/ha .
# unzip dump
tar -xzpvf ha_config.tar.gz -C ./config/ha
```

## Database Migration: `sqlite` to `mariadb`

The following script describe the steps to migrate home assistant database, as well as a few checks.

Required python packages: `pip install pandas sqlalchemy pymysql`.

### Backup Command

Approach 1: MariaDB Dump

```bash
docker exec mariadb mariadb-dump -u root -p'YOUR_ROOT_PASSWORD' --all-databases | gzip > mariadb_dump-$(date +%Y-%m-%d).sql.gz
```

Approach 2: Filesystem Copy (permission fix needed after restoration)

```bash
docker run --rm -v home_mariadb_data:/source -v $(pwd):/backup alpine tar -cvf /backup/mariadb-backup.tar -C /source .
```


### Report

```
docker exec -it mariadb bash
mariadb -D homeassistant -u homeassistant -p
show tables;
```

See `config/scripts/ha_db_migration.py`. At the moment of migrations:

```
----------- Row Counts for sqlite -----------
  - event_types                       22 rows
  - event_data                       583 rows
  - events                       125,037 rows
  - recorder_runs                      3 rows
  - states_meta                      268 rows
  - state_attributes              20,234 rows
  - states                       873,725 rows
  - statistics_meta                   82 rows
  - statistics                   333,969 rows
  - statistics_runs                2,986 rows
  - statistics_short_term        210,695 rows
---------------------------------------------

----------- Row Counts for mysql ------------
  - event_types                       22 rows
  - event_data                       583 rows
  - events                       125,037 rows
  - recorder_runs                      3 rows
  - states_meta                      268 rows
  - state_attributes              20,234 rows
  - states                       873,725 rows
  - statistics_meta                   82 rows
  - statistics                   333,969 rows
  - statistics_runs                2,986 rows
  - statistics_short_term        210,695 rows
---------------------------------------------
```

### Configurations

```python
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import time
import sys

SQLITE_DB_PATH = 'home-assistant_v2.db'
MARIADB_CONN_STR = "mysql+pymysql://homeassistant:mariadbpassword@localhost:3306/homeassistant?charset=utf8mb4"

CHUNK_SIZE = 50000
TABLES_TO_MIGRATE = [
    'event_types',
    'event_data',
    'events',
    'recorder_runs',
    # 'schema_changes',
    'states_meta',
    'state_attributes',
    'states',
    'statistics_meta',
    'statistics',
    'statistics_runs',
    'statistics_short_term',
]
```


### Script

```python
def get_db_engines():
    """Creates and returns SQLAlchemy engines for source and destination."""
    try:
        sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
        mariadb_engine = create_engine(MARIADB_CONN_STR)
        return sqlite_engine, mariadb_engine
    except Exception as e:
        print(f"❌ Error creating database engines: {e}")
        sys.exit(1)


def migrate_table(table_name, src_engine, dest_engine):
    """Migrates a single table from source to destination in chunks, with debugging printouts."""
    print(f"\nMigrating table: '{table_name}'...")
    start_time = time.time()
    total_rows = 0
    first_chunk = True # Flag to ensure we only print debug info once per table
    
    try:
        with dest_engine.connect() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            connection.execute(text(f"DELETE FROM {table_name};"))

        query = f'SELECT * FROM {table_name}'
        for chunk_df in pd.read_sql_query(query, src_engine, chunksize=CHUNK_SIZE):
            
            if first_chunk:
                source_sample = chunk_df.head(5)

            for col in chunk_df.columns:
                if col.endswith('_ts'):
                    chunk_df[col] = pd.to_numeric(chunk_df[col], errors='coerce')
                elif col in ['created', 'last_updated', 'time_fired', 'start', 'end']:
                    chunk_df[col] = pd.to_datetime(chunk_df[col], errors='coerce')

            if table_name == 'statistics_meta':
                if 'mean_type' not in chunk_df.columns:
                    chunk_df['mean_type'] = 0

            # --- DEBUG: Capture and print the processed data ---
            if False: # first_chunk:
                processed_sample = chunk_df.head(5)
                print("\n  --- DEBUG: Comparing source vs. processed data for the first 5 rows ---")
                print("  Source Data from SQLite:")
                print(source_sample)
                print("\n  Processed Data to be Injected into MariaDB:")
                print(processed_sample)
                print("  ----------------------------------------------------------------------\n")
                first_chunk = False # Set flag to false so this only runs once

            if chunk_df.empty:
                continue

            # --- Write to MariaDB ---
            chunk_df.to_sql(
                table_name,
                dest_engine,
                if_exists='append',
                index=False,
                chunksize=CHUNK_SIZE // 10
            )
            total_rows += len(chunk_df)
            print(f"  ... migrated {total_rows:,} rows", end='\r')

        end_time = time.time()
        with dest_engine.connect() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        print(f"✅ Finished migrating table '{table_name}'. Migrated {total_rows:,} rows in {end_time - start_time:.2f} seconds.")

    except SQLAlchemyError as e:
        print(f"\n❌ An error occurred during migration of table '{table_name}': {e}")
    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")


def print_row_counts(engine, tables):
    """Connects to a database and prints the row count for each table."""
    print(f"\n--- Row Counts for {engine.name}---")
    with engine.connect() as connection:
        for table_name in tables:
            try:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
                print(f"  - {table_name:<25} {row_count:>10,} rows")
            except Exception as e:
                print(f"  - {table_name}: Error counting rows - {e}")
    print("------------------------------------")


def main():
    sqlite_engine, mariadb_engine = get_db_engines()

    # print_row_counts(sqlite_engine, TABLES_TO_MIGRATE)
    print_row_counts(mariadb_engine, TABLES_TO_MIGRATE)
    
    # with mariadb_engine.connect() as connection:
    #     try:
    #         print("  -> Disabling foreign key checks...")
    #         connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
    #         for table in TABLES_TO_MIGRATE:
    #             migrate_table(table, sqlite_engine, mariadb_engine)
    #         print("\n🎉 Migration complete!")

    #     finally:
    #         print("  -> Re-enabling foreign key checks...")
    #         connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    #         print("✅ Database integrity checks restored.")

    # print_row_counts(sqlite_engine, TABLES_TO_MIGRATE)
    # print_row_counts(mariadb_engine, TABLES_TO_MIGRATE)

if __name__ == "__main__":
    main()
```