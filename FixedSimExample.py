from simModel.fixedScene.model import Model
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


carlaNetFile = 'networkFiles/CarlaTown05/Town05.net.xml'
carlaRouFile = 'networkFiles/CarlaTown05/Town05.rou.xml'
carlaVtypeFile = 'networkFiles/CarlaTown05/carlavtypes.rou.xml'
carlaRouFile = carlaVtypeFile + ',' + carlaRouFile

if __name__ == '__main__':
    fmodel = Model(
        (300, 198),
        50,
        carlaNetFile,
        carlaRouFile,
        dataBase='fixedSceneTest.db',
        SUMOGUI=0,
        simNote='local model first testing.',
    )

    fmodel.start()
    planner = TrafficManager(fmodel)

    while not fmodel.simEnd:
        fmodel.moveStep()
        if fmodel.timeStep % 5 == 0:
            roadgraph, vehicles = fmodel.exportSce()
            if roadgraph:
                trajectories = planner.plan(
                    fmodel.timeStep * 0.1, roadgraph, vehicles)
                fmodel.setTrajectories(trajectories)

        fmodel.updateVeh()

    fmodel.destroy()
