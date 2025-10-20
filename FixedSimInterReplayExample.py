from simModel.fixedScene import interReplay
from trafficManager.traffic_manager import TrafficManager

import logger
import os
# config a logger, set use_stdout=True to output log to terminal
# 将日志文件保存到DEBUG_TSRL目录
log_dir = "DEBUG_TSRL"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file_path = os.path.join(log_dir, "app_debug.log")
log = logger.setup_app_level_logger(file_name=log_file_path,
                                    level="DEBUG",
                                    use_stdout=False)


firmodel = interReplay.InterReplayModel(
    dataBase='fixedSceneTest.db'
)
planner = TrafficManager(firmodel)

while not firmodel.tpEnd:
    firmodel.moveStep()
    if firmodel.timeStep % 5 == 0:
        roadgraph, vehicles = firmodel.exportSce()
        if roadgraph:
            trajectories = planner.plan(
                firmodel.timeStep * 0.1, roadgraph, vehicles
            )
        else:
            trajectories = {}
        firmodel.setTrajectories(trajectories)
    else:
        firmodel.setTrajectories({})
firmodel.gui.destroy()
