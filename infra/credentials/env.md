# Environment variables are directly delivered to Kubernetes

This folder shall put `theme.env` by the nature of secrets; __Taskfile.yaml `infra:secrets:` task loads them__.

```
# from consolidated file
for f in *.env; do echo "### File: $f ###"; cat "$f"; echo -e "\n"; done > .env.combined

# concatenate envs
awk '/^### File: / { out=$3; next } { if (out) print > out }' .env.combined
```