#!/opt/homebrew/bin/python3
#!/bin/python3
# from operator import mul
import openstack
import json
import etcd3
import threading
import yaml
import random
from datetime import datetime, timezone
import os.path



DB_SIZE_MAX = 500*1024*1024
# fill it if you have regions in you want to avoid clouds.yaml 
govno_clusters = []

etcd = etcd3.client()

def get_all_disks(cloud=None,lease=3, ts=None):
    print(cloud)
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()
    cinder_volumes = [v for v in conn.volume.volumes(details=True, all_projects=True)]
    projects = {p.id: p.name for p in conn.identity.projects()}
    for v in cinder_volumes:
        prefix = "/volumes/"+v.location["region_name"]+"/"+v.id+"/"
        # print(prefix)
        obj = v.to_dict()
        obj["gcore_tv_updated"] = ts
        obj["project_name"] = projects[v.project_id] if v.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)
        # etcd.delete(prefix)

def get_all_baremetals(cloud=None,lease=3,ts=None):
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()
    baremetal_nodes = [v for v in conn.baremetal.nodes(details=True)]
    # projects = {p.id: p.name for p in conn.identity.projects()}
    for b in baremetal_nodes:
        prefix = "/baremetals/"+b.location["region_name"]+"/"+b.id+"/"
        # print(prefix)
        obj = b.to_dict()
        obj["gcore_tv_updated"] = ts
        # obj["project_name"] = projects[b.project_id] if b.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)

def get_all_routers(cloud=None,lease=3,ts=None):
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()
    routers = [v for v in conn.network.routers()]
    projects = {p.id: p.name for p in conn.identity.projects()}
    for r in routers:
        prefix = "/routers/"+r.location["region_name"]+"/"+r.id+"/"
        # print(prefix)
        obj = r.to_dict()
        obj["gcore_tv_updated"] = ts
        obj["project_name"] = projects[r.project_id] if r.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)

def get_all_servers_and_baremetals(cloud=None,lease=3,ts=None):
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()
    servers = [s for s in conn.compute.servers(all_projects=True,details=True)]
    projects = {p.id: p.name for p in conn.identity.projects()}
    #print(servers)
    for s in servers:
        prefix = "/servers/"+s.location["region_name"]+"/"+s.id+"/"
        # print(prefix)
        obj = s.to_dict()
        # print(ts)
        obj["gcore_tv_updated"] = ts
        obj["project_name"] = projects[s.project_id] if s.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)
    baremetal_nodes = [v for v in conn.baremetal.nodes(details=True)]
    for b in baremetal_nodes:
        prefix = "/baremetals/"+b.location["region_name"]+"/"+b.id+"/"
        # print(prefix)
        obj = b.to_dict()
        obj["gcore_tv_updated"] = ts
        # obj["project_name"] = projects[b.project_id] if b.project_id in projects else "NA"
        if b["instance_id"]: 
            srv = list(filter(lambda server: server["id"] == b["instance_id"], servers))
            # print(srv)
            # print(projects[srv[0].to_dict()["project_id"]])
            # print(srv[0].to_dict()["name"])
            obj["instance_owner"] = projects[srv[0].to_dict()["project_id"]]
            obj["instance_name"] = srv[0].to_dict()["name"]
            # print(obj,srv[0].to_dict()["name"])
        else:
            obj["instance_owner"] = None
            obj["instance_name"] = None
        etcd.put(prefix,json.dumps(obj),lease=lease)

def get_all_ports(cloud=None,lease=3,ts=None):
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()

    ports = [n for n in conn.network.ports()]
    projects = {p.id: p.name for p in conn.identity.projects()}
    #print(servers)
    for p in ports:
        prefix = "/ports/"+p.location["region_name"]+"/"+p.id+"/"
        # print(prefix)
        obj = p.to_dict()
        # print(ts)
        obj["gcore_tv_updated"] = ts
        obj["project_name"] = projects[p.project_id] if p.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)

def get_all_networks(cloud=None,lease=3,ts=None):
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()
    networks = [n for n in conn.network.networks()]
    projects = {p.id: p.name for p in conn.identity.projects()}
    #print(servers)
    for n in networks:
        prefix = "/networks/"+n.location["region_name"]+"/"+n.id+"/"
        # print(prefix)
        obj = n.to_dict()
        # print(ts)
        obj["gcore_tv_updated"] = ts
        obj["project_name"] = projects[n.project_id] if n.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)

def get_all_lbaas(cloud=None,lease=3,ts=None):
    conn = openstack.connect(cloud=cloud)
    etcd = etcd3.client()
    lbs = [l for l in conn.load_balancer.load_balancers()]
    projects = {p.id: p.name for p in conn.identity.projects()}
    for l in lbs:
        prefix = "/lbaas/"+l.location["region_name"]+"/"+l.id+"/"
        obj = l.to_dict()
        obj["gcore_tv_updated"] = ts
        obj["project_name"] = projects[l.project_id] if l.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)
       
def get_all_hypervisors(cloud=None,lease=3,ts=None):
    etcd = etcd3.client()
    conn = openstack.connect(cloud=cloud,compute_api_version='2.73')
    aggregates = conn.compute.aggregates()
    agg_dict = {}
    for a in aggregates:
    #     print(json.dumps(a.to_dict(), indent=4))
        for i in a["hosts"]:
            # print(a["name"],i,a["availability_zone"])
            if i in agg_dict: 
                agg_dict[i].append(a["name"])
            else:
                agg_dict[i] = []
                agg_dict[i].append(a["name"])
    hypers = [h for h in conn.compute.hypervisors(details=True)]
    for h in hypers:
        prefix = "/hypervisors/"+h.location["region_name"]+"/"+h.id+"/"
        # print(prefix)
        obj = h.to_dict()
        if h.name in agg_dict:
            obj["aggs"] = agg_dict[h.name]
        else:
            obj["aggs"] = None
        # print(ts)
        obj["gcore_tv_updated"] = ts
        # obj["project_name"] = projects[h.project_id] if h.project_id in projects else "NA"
        etcd.put(prefix,json.dumps(obj),lease=lease)

if __name__ == '__main__':
    if os.path.exists("clouds.yaml"):
        with open("clouds.yaml", 'r') as f:
            clouds = yaml.safe_load(f)
            # print(clouds)
            f.close()
        clouds = [c for c in clouds["clouds"].keys()]
    else: 
        exit(255)
    lease_id = random.randint(3, 2147483647)
    try:
        etcd.lease(7200,lease_id=lease_id)
    except:
        print("lease id is used: ",lease_id," omg")
        exit(255)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%T")
    print(lease_id,ts)
    DB_SIZE = etcd.status().db_size
    print(DB_SIZE,DB_SIZE_MAX)
    if DB_SIZE > DB_SIZE_MAX:
        print("DEFRAGING DB")
        etcd.defragment()
    for i in clouds:
        if (i in govno_clusters):
            continue
        print(i)
        disk_thread = threading.Thread(target=get_all_disks,args=(i,lease_id,ts))
        disk_thread.start()
        router_thread = threading.Thread(target=get_all_routers,args=(i,lease_id,ts))
        router_thread.start()
        servers_thread = threading.Thread(target=get_all_servers_and_baremetals,args=(i,lease_id,ts))
        servers_thread.start()
        hypers_thread = threading.Thread(target=get_all_hypervisors,args=(i,lease_id,ts))
        hypers_thread.start()
        ports_thread = threading.Thread(target=get_all_ports,args=(i,lease_id,ts))
        ports_thread.start()
        networks_thread = threading.Thread(target=get_all_networks,args=(i,lease_id,ts))
        networks_thread.start()
        lbs_thread = threading.Thread(target=get_all_lbaas,args=(i,lease_id,ts))
        lbs_thread.start()
        
