import traci
import sumolib
import time
import sys

"""
2025.7.20
# 定义方法：
# 1. 提取停车信息 
# 2. 验证停车信息是否已经被sumo正确应用，如没有则进行手动应用
"""

def extract_stop_info(rou_file):
    """
    从路由文件中提取停车信息
    
    参数:
    rou_file (str): 路由文件路径
    
    返回:
    dict: 包含车辆ID和对应停车信息的字典
    """
    vehicles_with_stops = {}
    print("stop info analysing...\n正在解析停车信息...")
    # 使用sumolib解析路由文件
    for vehicle in sumolib.xml.parse(rou_file, "vehicle"):
        vehicle_id = vehicle.id
        stops = []
        
        # 检查车辆是否有停止行为
        if hasattr(vehicle, 'stop') and vehicle.stop is not None:
            for stop in vehicle.stop:
                lane = stop.getAttribute("lane")
                end_pos = float(stop.getAttribute("endPos"))
                until = float(stop.getAttribute("until"))
                
                stops.append({
                    'lane': lane,
                    'end_pos': end_pos,
                    'until': until
                })
        
        if stops:
            vehicles_with_stops[vehicle_id] = stops
            print(f"找到车辆 {vehicle_id} 的停车信息: {stops}")
    
    return vehicles_with_stops

from simModel.common.carFactory import Vehicle  # 导入Vehicle类

def assign_stops_to_vehicles(vehicles_with_stops, vehicles:list[Vehicle]):
    """将停车信息分派给对应的Vehicle实例"""
    for vehicle_id, stops in vehicles_with_stops.items():
        for vehicle in vehicles:
            if vehicle.id == vehicle_id:
                vehicle.set_stop_info(stops)
                break

def validate_and_apply_stops(vehicles):
    """
    验证停车信息是否已经被sumo正确应用，如没有则进行手动应用
    
    参数:
    vehicles (list): Vehicle实例列表
    """
    try:
        vehicle_ids = traci.vehicle.getIDList()

        for vehicle in vehicles:
            if vehicle.id in vehicle_ids and vehicle.stop_info:
                # 检查车辆是否有停车信息
                current_stops = traci.vehicle.getStops(vehicle.id)
                if not current_stops:
                    # 如果sumo没有自动应用停车信息，手动应用
                    print(f"手动应用车辆 {vehicle.id} 的停车信息")
                    vehicle.apply_stop_info()
                else:
                    # 验证停车信息
                    print(f"车辆 {vehicle.id} 的停车信息已应用")

    except Exception as e:
        print(f"仿真错误: {str(e)}")