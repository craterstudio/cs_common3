from cs_devutils import unload_packages
unload_packages(packages=["cr_scene_data_transfer", "cr_scene_data_transfer.maya_dt"])

try:
 del maya_dt
except:
 print "sljivotres"
import cr_scene_data_transfer.maya_dt as maya_dt
sys.modules["cr_scene_data_transfer.maya_dt"]
maya_dt.cr_dt_export_alembic.export_scene()

