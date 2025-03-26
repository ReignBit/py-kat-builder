import sys
import os
import subprocess
import datetime
import requests
import traceback

from io import StringIO

from colorama import just_fix_windows_console, Fore
just_fix_windows_console()

import portainer
import discord

KAT_BUILD_LOCATION = "./build"
BUILD_DOT_GRADLE_LOCATION = KAT_BUILD_LOCATION + "/build.gradle"

GRADLE = "./gradlew"

USE_GIT_IF_NO_BUILD_PRESENT = True
GIT_PULL_LATEST = True

PROD_FILEPATH = "/srv/the-port/kat-bot/data"
PROD_JAR_FILEPATH = "latest.jar"
PROD_BACKUP_FILEPATH = "yt-source-{}.jar"



output = StringIO(newline="\n")

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self) :
        for f in self.files:
            f.flush()

original = sys.stdout
sys.stdout = Tee(sys.stdout, output)


def log(*args, **kwargs):
    print(f"\u001b[0;30m[{datetime.datetime.now().strftime('%H:%M:%S')}]\u001b[0;0m", *args, **kwargs)

def get_latest_yt_sources_version() -> str:
    try:
        data = requests.get("https://api.github.com/repos/lavalink-devs/youtube-source/releases").json()
        latest = data[0]['name']
        return latest
    except Exception as e:
        log(f"Failed to fetch version info for youtube-source, reason: {e}")


def get_current_yt_sources_version(build_gradle_filepath) -> str:
    try:
        with open(build_gradle_filepath, "r") as f:
            d = f.read()
            cur_version = d.split('dev.lavalink.youtube:common:')[1].split("\"")[0].split("'")[0] # try to split via " and ' just in case it changes in the future
            return cur_version
    except Exception as e:
        log(f"Failed to fetch current version info, reason: {e}")


def check_java_version():
    v = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT)
    v = v.decode("utf-8").split("\"")[1].split("\"")[0]
    log("Java Ver.   :", v)
    log("Needed Ver. : 17+")

    if not v.startswith("17"):
        log("Incorrect Java version, 17+ needed!")
        exit(100)

def update_version_to(build_gradle_filepath, new_version: str, old_version: str) -> bool:
    try:
        d = []
        o = ""
        m = ""

        with open(build_gradle_filepath, "r+") as f:
            d = f.read().splitlines(keepends=True)
            for i, line in enumerate(d):
                if 'dev.lavalink.youtube:common:' in line:
                    log("found dependency at line ", i)
                    o = line
                    d[i] = line.replace(old_version, new_version)
                    m = d[i]
                    break
            
            log(o.strip(), "->", m.strip())
            
            f.seek(0)
            f.writelines(d)
            f.truncate()
    except:
        return False
    return True


def commit():
    # This needs work TODO
    # oldcwd = os.getcwd()
    # os.chdir(KAT_BUILD_LOCATION)
    # log("Commiting changes to master...")
    # os.system("git add . & git commit -m \"Automated bump youtube-source version\" & git push")
    # os.chdir(oldcwd)
    pass

def build_kat(build_location):
    oldcwd = os.getcwd()
    os.chdir(build_location)

    log("Clearing any previous build runs...")
    ret = os.system(f"{GRADLE} clean")
    if ret != 0:
        log("Something went wrong whilst cleaning.. proceed with caution.")


    log("!!! BUILD STARTED !!!")
    ret = os.system(f"{GRADLE} build")
    log("Build Status:", ret)
    if ret == 0:
        log("Build success, jar located at: ", build_location + "/build/libs")
        os.chdir(oldcwd)
        return True
    os.chdir(oldcwd)
    return False

def production_activity(current_yt_version):
    oldcwd = os.getcwd()
    j = os.path.abspath(KAT_BUILD_LOCATION + "/build/libs/" + os.listdir(KAT_BUILD_LOCATION + "/build/libs/")[0])
    
    os.chdir(PROD_FILEPATH)

    log(PROD_FILEPATH + "/" + PROD_JAR_FILEPATH, "->", PROD_FILEPATH + "/" + PROD_BACKUP_FILEPATH.format(current_yt_version))
    os.rename("latest.jar", PROD_BACKUP_FILEPATH.format(current_yt_version))

    log(j, "->", PROD_FILEPATH + "/" + PROD_JAR_FILEPATH)
    os.rename(j, PROD_FILEPATH + "/" + PROD_JAR_FILEPATH)
    os.chdir(oldcwd)


def restart_docker_container():
    container_id = portainer.get_container_id_by_name("kat-bot")

    log(f"Stopping container ({container_id})")
    err =portainer.stop_container(container_id)
    log("OK" if err == 204 else f"NON-OK ({err})")

    log(f"Starting container ({container_id})")
    err = portainer.start_container(container_id)
    log("OK" if err == 204 else f"NON-OK ({err})")


if __name__ == "__main__":
    print("Process started at", datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S'))
    msg_id = None
    try:
        if not os.path.exists(KAT_BUILD_LOCATION) or len(os.listdir(KAT_BUILD_LOCATION)) < 2:
            os.mkdir(KAT_BUILD_LOCATION)
            # kat not here
            log("Kat directory not present or empty.")
            if USE_GIT_IF_NO_BUILD_PRESENT:
                log("Retrieving Kat via git...")
                oldcwd = os.getcwd()
                os.chdir(KAT_BUILD_LOCATION)
                os.system("git clone https://github.com/ReignBit/java-discord-kat.git .")
                os.chdir(oldcwd)
        else:
            log("Pulling any changes from remote...")
            oldcwd = os.getcwd()
            os.chdir(KAT_BUILD_LOCATION)
            os.system("git fetch & git pull")
            os.chdir(oldcwd)
            log("Got master branch!")

        l = get_latest_yt_sources_version()
        c = get_current_yt_sources_version(BUILD_DOT_GRADLE_LOCATION)

        log("Current Ver. : ", c)
        log("Latest  Ver. : ", l)

        if l == c:
            log("youtube-source is up-to-date!")
            exit(0)

        # verison not up-to-date
        msg_id = discord.send_start_webhook({'old': c, 'new': l, 'mention': "<@172408031060033537>", 'mention_id': '172408031060033537'})

        check_java_version()
        update_version_to(BUILD_DOT_GRADLE_LOCATION, l, c)
        if build_kat(KAT_BUILD_LOCATION):
            log("!!! PRODUCTION ACTIVITY !!!")
            production_activity(c)
            restart_docker_container()
            
            if not os.getenv("DRY_RUN", False):
                commit()

        output.seek(0)
        a = [x for x in output.readlines()]
        discord.send_end_webhook(msg_id, a)
    except Exception as e:
        output.seek(0)
        a = [x for x in output.readlines()]
        discord.send_error_webhook(msg_id, traceback.format_exc(), a)
