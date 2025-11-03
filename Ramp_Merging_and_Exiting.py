"""
匝道汇入汇出:
应用定义:
    1. 协作式车辆汇入
        应用定义：协作式车辆汇入是指，在高速公路或快速道路入口匝道处，路侧单元获取周围车辆运行信息和行驶意图，
        通过发送车辆引导信息，协调匝道和主路汇入车道车辆，辅助匝道车辆安全、高效的汇入主路。
    2. 协作式变道
        
    3. 协作式车辆分流
"""
from simModel.egoTracking.model import Model
from trafficManager.traffic_manager import TrafficManager
from trafficManager.common.vehicle import Behaviour
from simModel.common.carFactory import Vehicle  # 导入正确的Vehicle类
import logger
import traci
from traci import TraCIException
import traci.constants as tc
import logger
import os

# 将日志文件保存到DEBUG_TSRL目录
log_dir = "DEBUG_TSRL"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file_path = os.path.join(log_dir, "app_debug_RME.log")
log = logger.setup_app_level_logger(file_name=log_file_path)

file_paths = {
    "Ramp_Merging_and_Exiting": (
        "networkFiles/Ramp_Merging_and_Exiting/Ramp_Merging_and_Exiting.net.xml",
        "networkFiles/Ramp_Merging_and_Exiting/Ramp_Merging_and_Exiting.rou.xml"
    )
}

def run_model(
    net_file,
    rou_file,
    ego_veh_id="2",
    data_base=None,
    SUMOGUI="D:\sumo-win64-1.15.0\sumo-1.15.0\bin\sumo-gui.exe",
    sim_note="example simulation, ATSISP-v-1.0.",
    carla_cosim=False,
    max_sim_time=200, # 新增参数，单位秒
    communication = True,# 新增参数，全局通信管理器
    if_clear_message_file=False # 8.27 新增参数，是否清理消息文件
):
    try:
        model = Model(
            ego_veh_id,
            net_file,
            rou_file,
            dataBase=data_base,
            SUMOGUI=SUMOGUI,
            simNote=sim_note,
            carla_cosim=carla_cosim,
            max_steps=int(max_sim_time * 10), # 将max_sim_time转换为步长
            communication=communication, # 25.8.16 新增参数，全局通信管理器
        )
        model.start() # 初始化
        planner = TrafficManager(model) # 初始化车辆规划模块
        # 8.27 新增：清理消息文件or清理消息内容：
        model.clear_message_files(planner, if_clear_message_file)
        
        # 主循环
        # 当自车未到达终点时，继续模拟
        while not model.tpEnd:
            try:
                model.moveStep()
                if model.timeStep % 5 == 0:
                    # 导出场景 
                    #  7.27 打印exportSce()得到的vehicles中的stop_info
                    roadgraph, vehicles = model.exportSce() 
                    # 如果自车开始行驶且场景存在
                    if model.tpStart and roadgraph: 
                        trajectories = planner.plan(
                        model.timeStep * 0.1, roadgraph, vehicles
                        )# 规划轨迹
                        model.setTrajectories(trajectories) # 设置轨迹
                    else:
                        model.ego.exitControlMode() # 退出控制模式

                model.updateVeh() # 6.16 更改该函数内部结构
            except TraCIException as e:
                log.error(f"TraCI error at step {model.timeStep}: {str(e)}")
                break
            except Exception as e:
                log.error(f"Unexpected error at step {model.timeStep}: {str(e)}")
                break



    except Exception as e:
        log.error(f"Error during model initialization: {str(e)}")

if __name__ == "__main__":
    try:
        net_file, rou_file = file_paths['Ramp_Merging_and_Exiting']
        print("net_file:",net_file,",rou_file:",rou_file)
        run_model(net_file, 
                rou_file,
                ego_veh_id="2",
                carla_cosim=False,
                # SUMOGUI=True
                )
    except Exception as e:
        log.error(f"Main program error: {str(e)}")
        sys.exit(1)