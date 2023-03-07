#!/bin/python3
from datetime import datetime
import os, copy, logging, logging.handlers, sys
from flask import Flask, render_template,request
import json, re, time
import etcd3
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


global prefixes

data = {}
prefixes = {
        "volumes": ("location.region_name","project_id","project_name","id","status","volume_type","size",\
             "created_at","name","gcore_tv_updated"),
        "baremetals": ("location.region_name","instance_owner","id","name","instance_id","instance_name","resource_class"\
                      ,"boot_interface","provision_state","is_maintenance","maintenance_reason","gcore_tv_updated"),
        "routers": ("location.region_name","project_id","project_name","id","name","is_admin_state_up",
        "external_gateway_info", "gcore_tv_updated"),
        "servers": ("location.region_name","project_id","project_name","id","status","name","flavor.original_name","flavor.vcpus","flavor.ram","compute_host",\
                    "created_at","updated_at","attached_volumes","addresses","metadata","gcore_tv_updated"),
        "hypervisors": ("location.region_name","service_details.id","service_details.host",\
            "service_details.disabled_reason","hypervisor_type","hypervisor_version","status",\
                "aggs","vcpus","running_vms","cpu_info","gcore_tv_updated"),
        "ports": ("location.region_name","project_id","project_name","id","name","network_id","fixed_ips",\
            "status","mac_address","device_owner","binding_host_id","allowed_address_pairs",\
            "created_at","updated_at","gcore_tv_updated"),
        "networks": ("location.region_name","project_id","project_name","id","name","mtu","subnet_ids","provider_network_type","status","provider_physical_network",\
            "provider_segmentation_id",\
            "created_at","updated_at","gcore_tv_updated"),
        "lbaas": ("location.region_name","project_id","project_name","id","operating_status","provisioning_status",\
            "vip_address","vip_network_id","vip_subnet_id","description",
            "created_at","updated_at","gcore_tv_updated")
    }


def generate_cloud_new_data_loop():
    data_temp = {}
    print(datetime.now(),"hello")
    regex = r"^/(.*)/(.*)/(.*)/$"
    e = etcd3.client(grpc_options=[('grpc.max_receive_message_length',-1),('grpc.max_send_message_length', -1)])
    cl = []
    for p in e.get_prefix("/", keys_only=True):
        key = p[1].key.decode("utf-8")
        cloud_name = re.sub(regex,r"\1",key)
        cl.append(cloud_name)
    for c in set(cl):
        print(c)
        data_temp = generate_cloud_new_data(res=c)
        global data
        data[c] = copy.deepcopy(data_temp[c])
    return data

def generate_cloud_header_row():
    data_temp = {}
    for prefix in prefixes.keys():
        columns=prefixes[prefix]
        data_temp[prefix] = {}
        data_temp[prefix]["columns"] = columns
        data_temp[prefix]["rows"] = []
    return data_temp

def generate_cloud_new_data(res=None):
    data_temp = {}
    rows = []
    columns=prefixes[res]
    data_temp[res] = {}
    e = etcd3.client(grpc_options=[('grpc.max_receive_message_length',-1),('grpc.max_send_message_length', -1)])
    for p in e.get_prefix("/"+res+"/",keys_only=False):
        obj=json.loads(p[0].decode("utf-8"))
#         print(obj)
#         ot = tuple([obj[i] if (i != "" and '.' not in i)\
#                     else i if "." not in i \
#                     else "NA" if not obj[i]\
#                     else obj[i.split(".")[0]][i.split(".")[1]]\
#                     for i in columns])
        ot = []
        for i in columns:
            if (i == "location.region_name" or "flavor." in i):
                try:
                    ot.append(obj[i.split(".")[0]][i.split(".")[1]])
                except:
                    ot.append(None)
            elif (res == "routers" and i == "external_gateway_info"):
                try:
                    ot.append(json.dumps(obj[i],indent=4))
                except:
                    ot.append("Not parsed")
            elif (res == "servers" and ( i== "metadata" or i =="addresses" or i == "attached_volumes")):
                try:
                    ot.append(json.dumps(obj[i],indent=4))
                except:
                    ot.append("Not parsed")
            elif (res == "hypervisors" and (i == "cpu_info" or i == "aggs")):
                try:
                    ot.append(json.dumps(obj[i],indent=4))
                except:
                    ot.append("Not parsed")
            elif (res == "hypervisors" and "service_details." in i):
                try:
                    ot.append(obj[i.split(".")[0]][i.split(".")[1]])
                except:
                    ot.append(None)
            elif (res == "ports" and ("fixed_ips" in i or "allowed_address_pairs" in i)):
                try:
                    ot.append(json.dumps(obj[i],indent=4))
                except:
                    ot.append("Not parsed")
            else:
                ot.append(obj[i])

        ot = tuple(ot)
        rows.append(ot)

    
    data_temp[res]["rows"] = rows
    data_temp[res]["columns"] = columns
    return data_temp 



@app.route("/")
def r_index():
    global data
    data_columns = generate_cloud_header_row()
    return render_template('index.html', data=data_columns)


@app.route("/ajax1/")
def get_index1():
    res = request.args.get('res')
    data = generate_cloud_new_data(res=res)
    return data[res]

@app.route("/ajax/")
def get_index():
    res = request.args.get('res')
    # data = generate_cloud_new_data(res=res)
    # global data
    # print(data[res].keys())
    return data[res]

if os.getenv('MONS_HOST'):
    host = os.getenv('MONS_HOST')
else:
    host = "127.0.0.1"

sched = BackgroundScheduler(daemon=True)
sched.add_job(generate_cloud_new_data_loop, 'interval', seconds=60 , next_run_time=datetime.now())
sched.start()
data = generate_cloud_header_row()

@app.after_request
def logAfterRequest(response):
    timestamp = time.strftime('[%d/%b/%Y %H:%M:%S]')
    logger.error('%s - - %s "%s %s %s %s" size: %s', request.remote_addr, timestamp, request.method, request.scheme, request.full_path, response.status, response.content_length)
    return response

handler = logging.StreamHandler(sys.stdout)
logger = logging.getLogger("http")
logger.setLevel(logging.WARNING)
logger.addHandler(handler)

app.run(host=host,port=9999)