import hou
import sys
from cs_devutils import unload_packages
unload_packages(packages=["cr_scene_data_transfer", "cr_scene_data_transfer.houdini_dt"])

try:
 del houdini_dt
except:
 print "sljivotres"
import cr_scene_data_transfer.houdini_dt as houdini_dt
sys.modules["cr_scene_data_transfer.houdini_dt"]

houdini_dt.cr_dt_shader_assigments_from_attr.shader_assigment_from_attr()

