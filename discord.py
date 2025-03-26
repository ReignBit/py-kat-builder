import json
import requests
import os

from io import StringIO



def send_start_webhook(data):
    payload = json.dumps(
{
    "content": f"{data['mention']}",
    "allowed_mentions": {
        "parse": ["users"],
    },
    "embeds": [
    {
        "title": "Kat Restart Announcement",
        "description": f"Kat will be restarting shortly for an update to the Youtube integrations.\n```\nOld Version: {data['old']}\nNew Version: {data['new']}\n```",
        "color": 16763480,
        "footer": {
            "text": ""
        },
        "author": {
            "name": ""
        },
        "fields": []
    }
    ]
})
    r = requests.post(os.getenv("DISCORD_WEBHOOK_URL") + "?wait=true", data=payload, headers={
        "Content-Type": "application/json"
    })

    if r.status_code == 200:
        return r.json()['id']
    print("ERRROROROROROROROROROR")
    print(r.status_code)
    print(r.content)


def send_end_webhook(id, data):
    payload = json.dumps({
        "embeds": [
    {
        "title": "Kat Restart Announcement",
        "description": f"Kat has successfully restarted!\n```ansi\n{''.join(data)}\n```",
        "color": 6684504,
        "footer": {
            "text": ""
        },
        "author": {
            "name": ""
        },
        "fields": []
    }
    ]
    })

    r = requests.patch(os.getenv("DISCORD_WEBHOOK_URL") + f"/messages/{id}?wait=true", data=payload, headers={
        "Content-Type": "application/json"
    })

    if r.status_code == 200:
        return r.json()['id']


def send_error_webhook(id, exception, data):
    payload = json.dumps({
        "embeds": [
    {
        "title": "Kat Restart Announcement",
        "description": f"Something went wrong during the update process.\nException:\n```\n{exception}\n```\nProcess log:\n```ansi\n{''.join(data)}\n```",
        "color": 16711680,
        "footer": {
            "text": ""
        },
        "author": {
            "name": ""
        },
        "fields": []
    }
    ]
    })

    r = None
    if id:
        r = requests.patch(os.getenv("DISCORD_WEBHOOK_URL") + f"/messages/{id}?wait=true", data=payload, headers={
            "Content-Type": "application/json"
        })
    else:
        r = requests.post(os.getenv("DISCORD_WEBHOOK_URL") + "?wait=true", data=payload, headers={
            "Content-Type": "application/json"
        })
    

    if r.status_code == 200:
        return r.json()['id']