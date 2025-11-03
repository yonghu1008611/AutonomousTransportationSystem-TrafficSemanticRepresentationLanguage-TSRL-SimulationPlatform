"""
人车加速交互:
测试项目：人-车交互测试：驾驶员控制驾驶车辆加速
测试目的：测试自主式交通主体间语义表达与理解方法可支持道路交通环境下人-车交互

测试步骤：
1.	仿真车辆在道路上行驶，输入互操作语句控制车辆执行加速动作；
2.	仿真车辆接收到加速指令后，自动完成语法解析后，分析周边道路环境进行判断并返回是否具备加速条件；
3.	若具备加速条件则车辆执行加速动作。
测试结果判断说明：
输入互操作语句可以控制车辆执行加速动作。
"""
from simModel.egoTracking.model import Model
from trafficManager.traffic_manager import TrafficManager
from trafficManager.common.vehicle import Behaviour
from simModel.common.carFactory import Vehicle  # 导入正确的Vehicle类
from traci import TraCIException
import traci.constants as tc

import traci
import json
import sys
import logger
import os

# 将日志文件保存到DEBUG_TSRL目录
log_dir = "DEBUG_TSRL"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file_path = os.path.join(log_dir, "app_debug_HV.log")
log = logger.setup_app_level_logger(file_name=log_file_path)
Scenario_Name = "Human_Vehicle_Interacting"

file_paths = {
    "Human_Vehicle_Interacting": (
        "networkFiles/Human_Vehicle_Interacting/Human_Vehicle_Interacting.net.xml",
        "networkFiles/Human_Vehicle_Interacting/Human_Vehicle_Interacting.rou.xml",
        "networkFiles/Human_Vehicle_Interacting/Human_Vehicle_Interacting.add.xml"
    )
}

def run_model(
    net_file,
    rou_file,
    add_file,
    ego_veh_id="AV_0",
    data_base='Human_Vehicle_Interacting.db',
    SUMOGUI="D:\\sumo-win64-1.15.0\\sumo-1.15.0\\bin\\sumo-gui.exe",
    sim_note="Human-Vehicle interaction simulation, ATSISP-v-1.0.", 
    carla_cosim=False,
    max_sim_time=200,  # 单位秒
    communication=True,  # 全局通信管理器
    if_clear_message_file=False  # 是否清理消息文件
):
    """运行人车交互模拟"""
    try:
        model = Model(
            ego_veh_id,
            net_file,
            rou_file,
            addFile=add_file,
            dataBase=data_base,
            SUMOGUI=SUMOGUI,
            simNote=sim_note,
            carla_cosim=carla_cosim,
            max_steps=int(max_sim_time * 10), # 将max_sim_time转换为步长
            communication=communication, # 全局通信管理器
        )
        model.start() # 初始化
        planner = TrafficManager(model) # 初始化车辆规划模块
        # 清理消息文件or清理消息内容：
        model.clear_message_files(planner, if_clear_message_file)

        # 主循环
        # 当自车未到达终点时，继续模拟
        while not model.tpEnd:
            try:
                model.moveStep()
                if model.timeStep % 5 == 0:
                    # 显示场景信息
                    planner.communication_manager.show_display_text(Scenario_Name)
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

                model.updateVeh()
            except TraCIException as e:
                log.error(f"TraCI error at step {model.timeStep}: {str(e)}")
                break
            except Exception as e:
                log.error(f"Unexpected error at step {model.timeStep}: {str(e)}")
                break
    except Exception as e:
        log.error(f"Error during model execution: {str(e)}")
        raise
    finally:
        traci.close()
        log.info("SUMO simulation ended")

if __name__ == "__main__":
    try:
        net_file, rou_file,add_file = file_paths['Human_Vehicle_Interacting']
        print("net_file:\n", net_file, "\nrou_file:\n", rou_file,"\nadd_file:\n", add_file)
        
        # 使用相对于当前文件的路径创建日志和相关文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(current_dir, "logs")
        hv_dir = os.path.join(current_dir, "Human_Vehicle_Interacting_output")
        
        # 确保必要的目录存在
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(hv_dir, exist_ok=True)
        
        # 运行模型
        run_model(
            net_file, 
            rou_file,
            add_file=add_file,
            ego_veh_id="AV_0",
            carla_cosim=False,
            max_sim_time=300,
            # SUMOGUI=True
        )
    except Exception as e:
        log.error(f"Main program error: {str(e)}")
        sys.exit(1)