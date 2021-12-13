import os
import sys
import pymongo
import traceback

from time import time
from functools import wraps

try:
    import shotgun_api3
    SHOTGUN_AVAILABLE = True
except:
    SHOTGUN_AVAILABLE = False


DEFAULT_RELOAD_PACKAGES = ["cr_guiapp_boilerplate"]


def unload_packages(silent=True, packages=None):
    if packages is None:
        packages = DEFAULT_RELOAD_PACKAGES

    # construct reload list
    reloadList = []
    for i in sys.modules.keys():
        for package in packages:
            if i.startswith(package):
                reloadList.append(i)

    # unload everything
    for i in reloadList:
        try:
            if sys.modules[i] is not None:
                del(sys.modules[i])
                if not silent:
                    print("Unloaded: %s" % i)
        except:
            print("Failed to unload: %s" % i)


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        # print(">>> func: %r args: [%r, %r] took: %2.4f sec" % (
        #     f.__name__, args, kw, te-ts))
        print(">>> func: %r took: %2.4f sec" % (
            f.__name__, te-ts))
        return result
    return wrap


def shotgun_connect():
    if not SHOTGUN_AVAILABLE:
        print("SHOTGUN API is not available.")
        return

    shotgun_server_url = os.environ["SHOTGUN_SERVER_URL"]
    shotgun_script_name = "general_admin"
    use_https_proxy = os.environ["USE_HTTPS_PROXY"]
    mongodb_url = os.environ["MONGODB_URL"]
    mongodb_port = int(os.environ["MONGODB_PORT"])
    client = pymongo.MongoClient(mongodb_url, mongodb_port)
    query = client.shotgun.api_keys.find_one(({"title": shotgun_script_name}))
    shotgun_script_key = query["api_key"]

    try:
        sg = shotgun_api3.Shotgun(shotgun_server_url, shotgun_script_name,
                                  shotgun_script_key, http_proxy=use_https_proxy)
    except Exception as error:
        print(error)
        print("ERROR: Could not connect to Shotgun!")
        traceback.print_exc()
        return

    return sg


def shotgun_get_schema(entity):
    sg = shotgun_connect()
    return sg.schema_field_read(entity)
