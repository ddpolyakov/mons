MONS is a basic openstack tool, creating list of resources via datatables. Requires etcd as a backend and clouds.yaml formatted cloud config (https://docs.openstack.org/python-openstackclient/pike/configuration/index.html)
Docker runs: 
```
# etcd
docker run -d --platform linux/amd64 --name etcd-server  --net host   --publish 2379:2379 --publish 2380:2380          --env ALLOW_NONE_AUTHENTICATION=yes   --env ETCD_AUTO_COMPACTION_MODE=periodic --env ETCD_AUTO_COMPACTION_RETENTION=30m  --env ETCD_ADVERTISE_CLIENT_URLS=http://127.0.0.1:2379  docker-repo-kolla.cloud.gc.onl/mons/etcd:v3.5.4

# backend
docker  run --platform linux/amd64   -d  --cpus 4  --name  mons-back --net host mons-back:latest
docker cp clouds.yaml mons-back:/

# front 
docker  run  --platform linux/amd64  -d  --net host --name  mons-front --env MONS_HOST=127.0.0.1 -p 9999:9999  mons-front:latest
```
