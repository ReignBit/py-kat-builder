
import json
import os
import requests

from dotenv import load_dotenv
load_dotenv()


for x in ['PORTAINER_ENVIRONMENT_ID', 'PORTAINER_AUTH_TOKEN', 'PORTAINER_API_URL']:
    if not os.getenv(x):
        print(f"WARN: {x} not in environment variables!")


class Api:
    Auth = "/auth"  # Shouldn't need this anymore.
    Containers = f"/endpoints/{os.getenv('PORTAINER_ENVIRONMENT_ID')}/docker/containers/json?all=true"
    ContainerStop = f"/endpoints/{os.getenv('PORTAINER_ENVIRONMENT_ID')}/docker/containers/%s/stop"
    ContainerStart = f"/endpoints/{os.getenv('PORTAINER_ENVIRONMENT_ID')}/docker/containers/%s/start"

def get(endpoint, **kwargs):
    r = requests.get(os.getenv("PORTAINER_API_URL") + endpoint,
                    headers={
                        'Content-Type': "application/json",
                        "X-Api-Key": os.getenv("PORTAINER_AUTH_TOKEN")
                    }, **kwargs).json()
    return r

def post(endpoint, data, **kwargs):
    r = requests.post(os.getenv("PORTAINER_API_URL") + endpoint,
                    data=data,
                    headers={
                        'Content-Type': "application/json",
                        "X-Api-Key": os.getenv("PORTAINER_AUTH_TOKEN")
                    }, **kwargs)
    if r.content != b'':
        return r.json()

def get_container_id_by_name(name):
    containers = get(Api.Containers)
    
    if not name.startswith("/"):
        name = "/" + name
    
    for container in containers:
        if name in container["Names"]:
            return container['Id']


def stop_container(id):
    return post(Api.ContainerStop.replace("%s", id), json.dumps({}))

def start_container(id):
    return post(Api.ContainerStart.replace("%s", id), json.dumps({}))
