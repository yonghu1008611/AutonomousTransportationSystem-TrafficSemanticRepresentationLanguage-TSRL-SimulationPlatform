import logger
import os
# config a logger, set use_stdout=True to output log to terminal
# 将日志文件保存到DEBUG_TSRL目录
log_dir = "DEBUG_TSRL"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file_path = os.path.join(log_dir, "app_debug_InterReplay.log")
log = logger.setup_app_level_logger(file_name=log_file_path,
                                    level="DEBUG",
                                    use_stdout=False)

from trafficManager.traffic_manager import TrafficManager
from simModel.egoTracking import interReplay

irmodel = interReplay.InterReplayModel(
    dataBase='Vehicle_RSU_Interacting.db', startFrame=5000,communication=True)
planner = TrafficManager(irmodel)

while not irmodel.tpEnd:
    irmodel.moveStep()
    if irmodel.timeStep % 5 == 0:
        roadgraph, vehicles = irmodel.exportSce()
        if roadgraph:
            trajectories = planner.plan(
                irmodel.timeStep * 0.1, roadgraph, vehicles)
        else:
            trajectories = {}
        irmodel.setTrajectories(trajectories)
    else:
        irmodel.setTrajectories({})
irmodel.gui.destroy()