import os
import re
import sys


def increment_scene_path(scene_path):

    if not os.path.isfile(scene_path):
        return False

    current_folder = os.path.dirname(scene_path)
    scene_fullname = os.path.basename(scene_path)
    scene_name, scene_extension = scene_fullname.split(".")

    pattern = r"^.+v([0-9]+)$"

    match_version = re.match(pattern, scene_name)

    if match_version:
        scene_version = match_version.group(1)
        scene_version_up = str(int(scene_version) + 1).zfill(len(scene_version))
        new_scene_name = re.sub(r"v[0-9]+$", "v" + scene_version_up, scene_name)        
        
        incremented_path = os.path.join(
            current_folder, new_scene_name + "." + scene_extension).replace("\\", "/")
        return incremented_path
    else:
        return False
