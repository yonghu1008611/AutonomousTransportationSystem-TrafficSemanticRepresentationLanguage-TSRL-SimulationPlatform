"""
Author: Wu Hao
Date: 2025-9-18
Description: TSRL Decision Maker for vehicle behavior decision based on temporal spatial logic rules

Copyright (c) 2023 by PJLab, All Rights Reserved. 
"""
from __future__ import annotations

import os
import subprocess
import re
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
import threading
import queue

from decision_maker.abstract_decision_maker import (
    AbstractEgoDecisionMaker,
    AbstractMultiDecisionMaker,
    EgoDecision,
    MultiDecision,
    SingleStepDecision,
)
from common.observation import Observation
from common.vehicle import Behaviour, control_Vehicle
from predictor.abstract_predictor import Prediction
from utils.roadgraph import RoadGraph
from utils.trajectory import State

import logger

logging = logger.get_logger(__name__)

# 非阻塞弹窗类
class NonBlockingInferenceWindow:
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.root = None
        self.text_area = None
        self.window_thread = None
        self.update_queue = queue.Queue()
        self.is_running = False
        
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def _create_window(self, title: str):
        """在新线程中创建窗口"""
        try:
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title(title)
            self.root.geometry("600x400")
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 创建滚动文本框
            self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=25)
            self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            # 添加关闭按钮
            close_button = tk.Button(self.root, text="关闭", command=self._on_closing)
            close_button.pack(pady=5)
            
            # 启动更新循环
            self.root.after(100, self._process_updates)
            
            # 运行窗口
            self.is_running = True
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Error creating inference display window: {e}")
    
    def _on_closing(self):
        """窗口关闭事件处理"""
        self.is_running = False
        if self.root:
            self.root.destroy()
        self.root = None
        self.text_area = None
    
    def _process_updates(self):
        """处理更新队列"""
        try:
            while not self.update_queue.empty():
                content = self.update_queue.get_nowait()
                if self.text_area:
                    self.text_area.configure(state='normal')
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.INSERT, content)
                    self.text_area.configure(state='disabled')
                    self.text_area.see(tk.END)
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"Error processing updates: {e}")
        
        # 继续更新循环
        if self.root and self.is_running:
            self.root.after(100, self._process_updates)
    
    def show_window(self, title: str):
        """显示窗口"""
        if not self.is_running:
            self.window_thread = threading.Thread(target=self._create_window, args=(title,), daemon=True)
            self.window_thread.start()
    
    def update_content(self, content: str):
        """更新窗口内容"""
        if self.is_running:
            self.update_queue.put(content)
    
    def is_window_running(self):
        """检查窗口是否正在运行"""
        return self.is_running

# 新增的映射类，将动作名称映射到Behaviour枚举值
class action_name_to_behaviour_mapper:
    """
    将动作名称映射到Behaviour枚举值的映射类
    """
    # 定义动作名称到Behaviour的映射
    ACTION_TO_BEHAVIOUR = {
        "KeepLane": Behaviour.KL,
        "Accelerate": Behaviour.AC,
        "Decelerate": Behaviour.DC,
        "LeftChangeLane": Behaviour.LCL,  
        "RightChangeLane": Behaviour.LCR,
        "Stop": Behaviour.STOP,
        "EnterJunction": Behaviour.IN_JUNCTION,
        "Overtake": Behaviour.OVERTAKE,
        "KL": Behaviour.KL,
        "AC": Behaviour.AC,
        "DC": Behaviour.DC,
        "STOP": Behaviour.STOP,
        "IN_JUNCTION": Behaviour.IN_JUNCTION
    }
    
    @classmethod
    def get_behaviour(cls, action_name: str) -> Behaviour:
        """
        根据动作名称获取对应的Behaviour枚举值
        Args:
            action_name (str): 动作名称
        Returns:
            Behaviour: 对应的Behaviour枚举值，如果未找到则返回Behaviour.OTHER
        """
        # 先直接查找
        if action_name in cls.ACTION_TO_BEHAVIOUR:
            return cls.ACTION_TO_BEHAVIOUR[action_name]
        # 忽略大小写查找
        for key, value in cls.ACTION_TO_BEHAVIOUR.items():
            if key.lower() == action_name.lower():
                return value
        # 如果是Behaviour枚举的字符串形式
        try:
            return Behaviour[action_name.upper()]
        except KeyError:
            pass
        # 如果都没找到，返回OTHER
        return Behaviour.OTHER
    
    @classmethod
    def get_lane_change_behaviour(cls, action_name: str, vehicle: control_Vehicle, road_graph: RoadGraph) -> Behaviour:
        """
        根据动作名称和车辆信息获取对应的变道行为
        对于ChangeLane动作，根据车辆可用车道选择左变道(LCL)或右变道(LCR)
        Args:
            action_name (str): 动作名称
            vehicle (control_Vehicle): 车辆对象
            road_graph (RoadGraph): 道路图对象
        Returns:
            Behaviour: 对应的Behaviour枚举值
        """
        # 如果不是ChangeLane动作，使用常规映射
        if action_name != "ChangeLane":
            return cls.get_behaviour(action_name)
        
        # 对于ChangeLane动作，根据可用车道选择合适的变道行为
        if vehicle is None or road_graph is None:
            return Behaviour.LCL  # 默认返回左变道
        
        # 获取当前车道
        current_lane = road_graph.get_lane_by_id(vehicle.lane_id)
        if current_lane is None:
            return Behaviour.LCL  # 默认返回左变道
        
        # 查找左可用车道
        lane = current_lane
        while lane.left_lane() is not None:
            lane_id = lane.left_lane()
            if lane_id in vehicle.available_lanes:
                return Behaviour.LCL
            lane = road_graph.get_lane_by_id(lane_id)
        
        # 查找右可用车道
        lane = current_lane
        while lane.right_lane() is not None:
            lane_id = lane.right_lane()
            if lane_id in vehicle.available_lanes:
                return Behaviour.LCR
            lane = road_graph.get_lane_by_id(lane_id)
        
        # 如果找不到可用的变道车道，返回左变道作为默认行为
        return Behaviour.LCL
    
    @classmethod
    def is_lane_change(cls, behaviour: Behaviour) -> bool:
        """
        判断行为是否为变道行为
        Args:
            behaviour (Behaviour): 行为枚举值
        Returns:
            bool: 如果是变道行为返回True，否则返回False
        """
        return behaviour in [Behaviour.LCL, Behaviour.LCR, Behaviour.OVERTAKE]
    
    @classmethod
    def get_opposite_lane_change(cls, behaviour: Behaviour) -> Behaviour:
        """
        获取相反的变道行为
        Args:
            behaviour (Behaviour): 当前变道行为
        Returns:
            Behaviour: 相反的变道行为
        """
        if behaviour == Behaviour.LCL:
            return Behaviour.LCR
        elif behaviour == Behaviour.LCR:
            return Behaviour.LCL
        else:
            return behaviour

class EgoDecisionMaker(AbstractEgoDecisionMaker):
    def __init__(self):
        # 获取项目根目录
        self.project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        self.message_history_dir = os.path.join(self.project_root, 'message_history') # 消息历史文件目录
        self.rules_file = os.path.join(self.project_root, 'TSRL_inference', 'Rules', 'Roadsys_rule.txt') # 规则文件路径
        self.inference_input_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_Input') # 推理输入文件目录
        self.inference_output_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_Output') # 推理输出文件目录
        self.tsil_script = os.path.join(self.project_root, 'TSRL_representation', 'TSIL.py') # TSIL脚本路径
        
        # 确保目录存在
        os.makedirs(self.inference_input_dir, exist_ok=True)
        os.makedirs(self.inference_output_dir, exist_ok=True)

    def _read_message_history(self, vehicle_id: str, max_messages: Optional[int] = None) -> List[str]:
        """读取指定车辆的消息历史"""
        message_file = os.path.join(self.message_history_dir, f'message_{vehicle_id}_history.txt')
        if not os.path.exists(message_file):
            logging.warning(f"Message history file for vehicle {vehicle_id} not found")
            return []
        
        try:
            with open(message_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 过滤空行
                messages = [line.strip() for line in lines if line.strip()]
                # 如果指定了最大消息数量，则只返回最新的max_messages条消息
                if max_messages is not None and max_messages > 0:
                    return messages[-max_messages:] if len(messages) > max_messages else messages
                return messages
        except Exception as e:
            logging.error(f"Error reading message history for vehicle {vehicle_id}: {e}")
            return []

    def _read_rules(self) -> List[str]:
        """读取所有规则"""
        if not os.path.exists(self.rules_file):
            logging.error(f"Rules file not found: {self.rules_file}")
            return []
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 过滤空行和注释行
                return [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        except Exception as e:
            logging.error(f"Error reading rules file: {e}")
            return []

    def _parse_rule(self, rule: str) -> tuple:
        """解析规则，返回左侧和右侧部分"""
        if ":-" not in rule:
            return None, None
        head, body = rule.split(":-", 1)
        head = head.strip()
        body = body.strip().rstrip(';')  # 移除结尾的分号
        conditions = [cond.strip() for cond in body.split(',')]
        return head, conditions

    def _check_conditions(self, conditions: List[str], message_history: List[str]) -> bool:
        """检查所有条件是否都在消息历史中"""
        for condition in conditions:
            # 检查条件是否在消息历史中
            found = False
            for msg in message_history:
                # 去除消息末尾的分号
                clean_msg = msg.rstrip(';')
                # 检查如果condition和msg都包含"("，则比较括号前的部分
                if "(" in condition and "(" in clean_msg:
                    condition_prefix = condition.split("(")[0]
                    msg_prefix = clean_msg.split("(")[0]
                    if condition_prefix == msg_prefix:
                        found = True
                        break
                else:
                    # 如果没有括号，则直接比较
                    if condition == clean_msg:
                        found = True
                        break
            
            if not found:
                return False
        return True

    def _generate_inference_input(self, vehicle_id: str, message_history: List[str], rule: str, head: str) -> str:
        """生成推理输入文件"""
        input_filename = f'Inference_{vehicle_id}_input.txt'
        input_filepath = os.path.join(self.inference_input_dir, input_filename)
        
        try:
            with open(input_filepath, 'w', encoding='utf-8') as f:
                # 写入消息历史
                for msg in message_history:
                    f.write(f"{msg}\n")
                f.write("\n")
                # 写入规则
                f.write(f"{rule}\n")
                f.write("\n")
                # 写入ASK语句
                f.write(f"ASK {head}\n")
            
            return input_filepath
        except Exception as e:
            logging.error(f"Error generating inference input for vehicle {vehicle_id}: {e}")
            return ""

    def _run_tsrl_inference(self, input_filepath: str, vehicle_id: str) -> str:
        """运行TSRL推理引擎"""
        output_filename = f'Inference_{vehicle_id}_output.txt'
        output_filepath = os.path.join(self.inference_output_dir, output_filename)
        
        try:
            # 构建命令
            cmd = f'python "{self.tsrl_script}" "{input_filepath}"'
            
            # 运行推理
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(self.tsrl_script))
            
            if result.returncode != 0:
                logging.error(f"TSRL inference failed for vehicle {vehicle_id}: {result.stderr}")
                return ""
            
            # 将输出保存到文件
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            return output_filepath
        except Exception as e:
            logging.error(f"Error running TSIL inference for vehicle {vehicle_id}: {e}")
            return ""

    def _parse_inference_output(self, output_filepath: str, head: str) -> Optional[str]:
        """解析推理输出，提取变量替换后的决策"""
        if not os.path.exists(output_filepath):
            return None
            
        try:
            with open(output_filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找包含head的行
            for line in lines:
                line = line.strip()
                # 检查line是否包含冒号格式的映射关系
                if ':' in line and line.startswith('{') and line.endswith('}'):
                    # 解析line中的映射关系，例如 "{'y': '1'}"
                    try:
                        # 移除大括号
                        content = line[1:-1]  # 移除开头和结尾的大括号
                        # 解析键值对，注意处理逗号在引号内的情况
                        mapping = {}
                        # 简单处理，按逗号分割（假设格式简单）
                        pairs = content.split(',')
                        # 解析每个键值对
                        for pair in pairs:
                            # 分割键和值
                            if ':' in pair:
                                kv = pair.split(':', 1)  # 只分割第一个冒号
                                if len(kv) == 2:
                                    # 移除键值两端的空格和引号
                                    key = kv[0].strip().strip("'\"")
                                    value = kv[1].strip().strip("'\"")
                                    mapping[key] = value
                        
                        # 获取head中的变量名（括号内的内容）
                        if '(' in head and ')' in head:
                            head_prefix = head.split('(')[0]
                            head_var = head[head.find('(')+1:head.find(')')]
                            
                            # 检查head_var是否在映射中
                            if head_var in mapping:
                                # 替换head中的变量为映射值
                                replaced_head = f"{head_prefix}({mapping[head_var]})"
                                return replaced_head
                    except Exception as e:
                        logging.warning(f"Failed to parse mapping line: {line}, error: {e}")
                        continue
                elif line.startswith(head.split('(')[0]):  # 匹配谓词名称
                    return line
            
            return None
        except Exception as e:
            logging.error(f"Error parsing inference output: {e}")
            return None

    def _extract_action_from_head(self, head: str) -> str:
        """从规则头部提取行为名称"""
        if '(' in head:
            return head.split('(')[0]
        return head

    def _create_inference_display_window(self, title: str, content: str):
        """创建弹窗展示推理信息（非阻塞）"""
        try:
            # 获取非阻塞弹窗实例
            window = NonBlockingInferenceWindow.get_instance()
            
            # 显示窗口（如果尚未显示）
            window.show_window(title)
            
            # 等待窗口初始化完成
            import time
            start_time = time.time()
            while not window.is_window_running() and (time.time() - start_time) < 5:
                time.sleep(0.1)
            
            # 更新窗口内容
            window.update_content(content)
                
        except Exception as e:
            logging.error(f"Error creating inference display window: {e}")

    def _get_current_time(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_detailed_inference_display_file(self, vehicle_id: str, message_history: List[str], rule: str,
                                                 input_filepath: str, output_filepath: str, decision_result: str):
        """生成详细的推理展示文件，包含输入、输出和决策结果，并在弹窗中展示"""
        try:
            # 创建推理展示目录
            inference_display_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_display')
            os.makedirs(inference_display_dir, exist_ok=True)
            
            # 生成展示文件路径
            display_filename = f'Detailed_Inference_display_{vehicle_id}.txt'
            display_filepath = os.path.join(inference_display_dir, display_filename)
            
            # 准备展示内容
            content = f"=== TSRL详细推理展示 ===\n\n"
            content += f"车辆ID: {vehicle_id}\n"
            content += f"时间: {self._get_current_time()}\n\n"
            
            content += f"=== 匹配的规则 ===\n{rule}\n\n"
            
            content += f"=== 消息历史 ===\n"
            for i, msg in enumerate(message_history, 1):
                content += f"{i}. {msg}\n"
            content += "\n"
            
            # 读取推理输入文件内容
            content += f"=== 推理输入文件内容 ({os.path.basename(input_filepath)}) ===\n"
            if os.path.exists(input_filepath):
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输入文件不存在\n"
            content += "\n"
            
            # 读取TSIL推理输出文件内容
            content += f"=== TSIL推理输出内容 ({os.path.basename(output_filepath)}) ===\n"
            if os.path.exists(output_filepath):
                with open(output_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输出文件不存在\n"
            content += "\n"
            
            # 添加解析后的决策结果
            content += f"=== 解析后的决策结果 ===\n"
            if decision_result:
                content += f"{decision_result}\n"
            else:
                content += "无决策结果\n"
            
            # 写入展示文件
            with open(display_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 创建弹窗展示内容
            self._create_inference_display_window("TSRL详细推理展示", content)
            
            return display_filepath
        except Exception as e:
            logging.error(f"Error generating detailed inference display file: {e}")
            return None

    def _create_inference_display_window(self, title: str, content: str):
        """创建弹窗展示推理信息（非阻塞）"""
        try:
            # 获取非阻塞弹窗实例
            window = NonBlockingInferenceWindow.get_instance()
            
            # 显示窗口（如果尚未显示）
            window.show_window(title)
            
            # 等待窗口初始化完成
            import time
            start_time = time.time()
            while not window.is_window_running() and (time.time() - start_time) < 5:
                time.sleep(0.1)
            
            # 更新窗口内容
            window.update_content(content)
                
        except Exception as e:
            logging.error(f"Error creating inference display window: {e}")

    def _get_current_time(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_detailed_inference_display_file(self, vehicle_id: str, message_history: List[str], rule: str,
                                                 input_filepath: str, output_filepath: str, decision_result: str):
        """生成详细的推理展示文件，包含输入、输出和决策结果，并在弹窗中展示"""
        try:
            # 创建推理展示目录
            inference_display_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_display')
            os.makedirs(inference_display_dir, exist_ok=True)
            
            # 生成展示文件路径
            display_filename = f'Detailed_Inference_display_{vehicle_id}.txt'
            display_filepath = os.path.join(inference_display_dir, display_filename)
            
            # 准备展示内容
            content = f"=== TSRL详细推理展示 ===\n\n"
            content += f"车辆ID: {vehicle_id}\n"
            content += f"时间: {self._get_current_time()}\n\n"
            
            content += f"=== 匹配的规则 ===\n{rule}\n\n"
            
            content += f"=== 消息历史 ===\n"
            for i, msg in enumerate(message_history, 1):
                content += f"{i}. {msg}\n"
            content += "\n"
            
            # 读取推理输入文件内容
            content += f"=== 推理输入文件内容 ({os.path.basename(input_filepath)}) ===\n"
            if os.path.exists(input_filepath):
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输入文件不存在\n"
            content += "\n"
            
            # 读取TSIL推理输出文件内容
            content += f"=== TSIL推理输出内容 ({os.path.basename(output_filepath)}) ===\n"
            if os.path.exists(output_filepath):
                with open(output_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输出文件不存在\n"
            content += "\n"
            
            # 添加解析后的决策结果
            content += f"=== 解析后的决策结果 ===\n"
            if decision_result:
                content += f"{decision_result}\n"
            else:
                content += "无决策结果\n"
            
            # 写入展示文件
            with open(display_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 创建弹窗展示内容
            self._create_inference_display_window("TSRL详细推理展示", content)
            
            return display_filepath
        except Exception as e:
            logging.error(f"Error generating detailed inference display file: {e}")
            return None

    def make_decision(
        self,
        T: float,
        observation: Observation,
        road_graph: RoadGraph,
        prediction: Prediction = None,
    ) -> EgoDecision:
        """
        基于TSRL的自车决策器实现
        步骤：
        1. 读取自车消息历史文件
        2. 遍历规则文件中的每条规则
        3. 检查规则条件是否满足
        4. 生成推理输入文件
        5. 运行TSIL推理引擎
        6. 解析输出并生成决策
        """
        # 获取自车信息
        ego_vehicle = None
        for vehicle in observation.vehicles:
            if hasattr(vehicle, 'if_egoCar') and vehicle.if_egoCar:
                ego_vehicle = vehicle
                break
        
        if not ego_vehicle:
            logging.warning("No ego vehicle found in observation")
            return EgoDecision(ego_veh=None, result=[])
        
        # 初始化决策结果
        decision_result = []
        
        # 获取自车ID
        vehicle_id = str(ego_vehicle.id)
        
        # 读取该车辆的消息历史，默认读取最新的10条消息
        message_history = self._read_message_history(vehicle_id, max_messages=10)
        if not message_history:
            logging.warning(f"No message history for ego vehicle {vehicle_id}")
            return EgoDecision(ego_veh=ego_vehicle, result=decision_result)
        
        # 读取规则
        rules = self._read_rules()
        if not rules:
            logging.warning("No rules found, skipping TSRL decision making")
            return EgoDecision(ego_veh=ego_vehicle, result=decision_result)
        
        # 遍历所有规则
        for rule in rules:
            if ":-" not in rule:
                continue
                
            head, conditions = self._parse_rule(rule)
            if not head or not conditions:
                continue
            
            # 检查规则条件是否满足
            if self._check_conditions(conditions, message_history):
                logging.debug(f"Rule conditions satisfied for ego vehicle {vehicle_id}: {rule}")
                
                # 生成推理输入文件
                input_filepath = self._generate_inference_input(vehicle_id, message_history, rule, head)
                if not input_filepath:
                    continue
                
                # 运行TSRL推理
                output_filepath = self._run_tsrl_inference(input_filepath, vehicle_id)
                if not output_filepath:
                    continue
                
                # 解析推理输出
                decision_output = self._parse_inference_output(output_filepath, head)
                if decision_output:
                    # 生成详细的推理展示文件并弹窗展示
                    self._generate_detailed_inference_display_file(vehicle_id, message_history, rule, input_filepath, output_filepath, decision_output)
                    # 创建决策
                    decision_at_t = SingleStepDecision()
                    decision_at_t.action = decision_output
                    decision_at_t.expected_time = T
                    
                    # 根据规则头部确定行为类型
                    action_name = self._extract_action_from_head(head)
                    # 使用action_name_to_behaviour_mapper映射action_name到Behaviour
                    decision_at_t.behaviour = action_name_to_behaviour_mapper.get_behaviour(action_name)
                        
                    if decision_at_t.behaviour is None:
                        logging.warning(f"Unknown behaviour for action {action_name}")
                        continue
                    
                    decision_result.append(decision_at_t)
                    logging.info(f"Decision made for ego vehicle {vehicle_id}: {decision_output}")
                    break  # 找到一个适用规则就停止
            else: 
                # 消息列表和推理规则没有对应，所以返回空决策
                return EgoDecision(ego_veh=ego_vehicle, result=decision_result)
        
        return EgoDecision(ego_veh=ego_vehicle, result=decision_result)


class MultiDecisionMaker(AbstractMultiDecisionMaker):
    def __init__(self):
        # 获取项目根目录
        self.project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        self.message_history_dir = os.path.join(self.project_root, 'message_history') # 消息历史文件目录
        self.rules_file = os.path.join(self.project_root, 'TSRL_inference', 'Rules', 'Roadsys_rule.txt') # 规则文件路径
        self.inference_input_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_Input') # 推理输入文件目录
        self.inference_output_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_Output') # 推理输出文件目录
        self.tsrl_script = os.path.join(self.project_root, 'TSRL_representation', 'TSRL.py') # TSRL脚本路径
        
        # 确保目录存在
        os.makedirs(self.inference_input_dir, exist_ok=True)
        os.makedirs(self.inference_output_dir, exist_ok=True)

    def _read_message_history(self, vehicle_id: str, max_messages: Optional[int] = None) -> List[str]:
        """读取指定车辆的消息历史"""
        message_file = os.path.join(self.message_history_dir, f'message_{vehicle_id}_history.txt')
        if not os.path.exists(message_file):
            logging.warning(f"Message history file for vehicle {vehicle_id} not found")
            return []
        
        try:
            with open(message_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 过滤空行
                messages = [line.strip() for line in lines if line.strip()]
                # 如果指定了最大消息数量，则只返回最新的max_messages条消息
                if max_messages is not None and max_messages > 0:
                    return messages[-max_messages:] if len(messages) > max_messages else messages
                return messages
        except Exception as e:
            logging.error(f"Error reading message history for vehicle {vehicle_id}: {e}")
            return []

    def _read_rules(self) -> List[str]:
        """读取所有规则"""
        if not os.path.exists(self.rules_file):
            logging.error(f"Rules file not found: {self.rules_file}")
            return []
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 过滤空行和注释行
                return [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        except Exception as e:
            logging.error(f"Error reading rules file: {e}")
            return []

    def _parse_rule(self, rule: str) -> tuple:
        """解析规则，返回左侧和右侧部分"""
        if ":-" not in rule:
            return None, None
        head, body = rule.split(":-", 1)
        head = head.strip()
        body = body.strip().rstrip(';')  # 移除结尾的分号
        conditions = [cond.strip() for cond in body.split(',')]
        return head, conditions

    def _check_conditions(self, conditions: List[str], message_history: List[str]) -> bool:
        """检查所有条件是否都在消息历史中"""
        for condition in conditions:
            # 简单检查条件是否在消息历史中
            found = False  # 初始化found变量
            for msg in message_history:
                # 去除消息末尾的分号
                clean_msg = msg.rstrip(';')
                # 检查如果condition和msg都包含"("，则比较括号前的部分
                if "(" in condition and "(" in clean_msg:
                    condition_prefix = condition.split("(")[0]
                    msg_prefix = clean_msg.split("(")[0]
                    if condition_prefix == msg_prefix:
                        found = True
                        break
                else:
                    # 如果没有括号，则直接比较
                    if condition == clean_msg:
                        found = True
                        break
            
            if not found:
                return False
        return True

    def _generate_inference_input(self, vehicle_id: str, message_history: List[str], rule: str, head: str) -> str:
        """生成推理输入文件"""
        input_filename = f'Inference_{vehicle_id}_input.txt'
        input_filepath = os.path.join(self.inference_input_dir, input_filename)
        
        try:
            with open(input_filepath, 'w', encoding='utf-8') as f:
                # 写入消息历史
                for msg in message_history:
                    f.write(f"{msg}\n")
                f.write("\n")
                # 写入规则
                f.write(f"{rule}\n")
                f.write("\n")
                # 写入ASK语句
                f.write(f"ASK {head}\n")
            
            return input_filepath
        except Exception as e:
            logging.error(f"Error generating inference input for vehicle {vehicle_id}: {e}")
            return ""

    def _run_tsrl_inference(self, input_filepath: str, vehicle_id: str) -> str:
        """运行TSRL推理引擎"""
        output_filename = f'Inference_{vehicle_id}_output.txt'
        output_filepath = os.path.join(self.inference_output_dir, output_filename)
        
        try:
            # 构建命令
            cmd = f'python "{self.tsrl_script}" "{input_filepath}"'
            
            # 运行推理
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(self.tsrl_script))
            
            if result.returncode != 0:
                logging.error(f"TSRL inference failed for vehicle {vehicle_id}: {result.stderr}")
                return ""
            
            # 将输出保存到文件
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            return output_filepath
        except Exception as e:
            logging.error(f"Error running TSRL inference for vehicle {vehicle_id}: {e}")
            return ""

    def _parse_inference_output(self, output_filepath: str, head: str) -> Optional[str]:
        """解析推理输出，提取变量替换后的决策"""
        if not os.path.exists(output_filepath):
            return None
            
        try:
            with open(output_filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找包含head的行
            for line in lines:
                line = line.strip()
                # 检查line是否包含冒号格式的映射关系
                if ':' in line and line.startswith('{') and line.endswith('}'):
                    # 解析line中的映射关系，例如 "{'y': '1'}"
                    try:
                        # 移除大括号
                        content = line[1:-1]  # 移除开头和结尾的大括号
                        # 解析键值对，注意处理逗号在引号内的情况
                        mapping = {}
                        # 简单处理，按逗号分割（假设格式简单）
                        pairs = content.split(',')
                        # 解析每个键值对
                        for pair in pairs:
                            # 分割键和值
                            if ':' in pair:
                                kv = pair.split(':', 1)  # 只分割第一个冒号
                                if len(kv) == 2:
                                    # 移除键值两端的空格和引号
                                    key = kv[0].strip().strip("'\"")
                                    value = kv[1].strip().strip("'\"")
                                    mapping[key] = value
                        
                        # 获取head中的变量名（括号内的内容）
                        if '(' in head and ')' in head:
                            head_prefix = head.split('(')[0]
                            head_var = head[head.find('(')+1:head.find(')')]
                            
                            # 检查head_var是否在映射中
                            if head_var in mapping:
                                # 替换head中的变量为映射值
                                replaced_head = f"{head_prefix}({mapping[head_var]})"
                                return replaced_head
                    except Exception as e:
                        logging.warning(f"Failed to parse mapping line: {line}, error: {e}")
                        continue
                elif line.startswith(head.split('(')[0]):  # 匹配谓词名称
                    return line
            
            return None
        except Exception as e:
            logging.error(f"Error parsing inference output: {e}")
            return None

    def _extract_action_from_head(self, head: str) -> str:
        """从规则头部提取行为名称"""
        if '(' in head:
            return head.split('(')[0]
        return head

    def _get_current_time(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_detailed_inference_display_file(self, vehicle_id: str, message_history: List[str], rule: str,
                                                 input_filepath: str, output_filepath: str, decision_result: str):
        """生成详细的推理展示文件，包含输入、输出和决策结果，并在弹窗中展示"""
        try:
            # 创建推理展示目录
            inference_display_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_display')
            os.makedirs(inference_display_dir, exist_ok=True)
            
            # 生成展示文件路径
            display_filename = f'Detailed_Inference_display_{vehicle_id}.txt'
            display_filepath = os.path.join(inference_display_dir, display_filename)
            
            # 准备展示内容
            content = f"=== TSRL详细推理展示 ===\n\n"
            content += f"车辆ID: {vehicle_id}\n"
            content += f"时间: {self._get_current_time()}\n\n"
            
            content += f"=== 匹配的规则 ===\n{rule}\n\n"
            
            content += f"=== 消息历史 ===\n"
            for i, msg in enumerate(message_history, 1):
                content += f"{i}. {msg}\n"
            content += "\n"
            
            # 读取推理输入文件内容
            content += f"=== 推理输入文件内容 ({os.path.basename(input_filepath)}) ===\n"
            if os.path.exists(input_filepath):
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输入文件不存在\n"
            content += "\n"
            
            # 读取TSRL推理输出文件内容
            content += f"=== TSRL推理输出内容 ({os.path.basename(output_filepath)}) ===\n"
            if os.path.exists(output_filepath):
                with open(output_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输出文件不存在\n"
            content += "\n"
            
            # 添加解析后的决策结果
            content += f"=== 解析后的决策结果 ===\n"
            if decision_result:
                content += f"{decision_result}\n"
            else:
                content += "无决策结果\n"
            
            # 写入展示文件
            with open(display_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 创建弹窗展示内容
            self._create_inference_display_window("TSRL详细推理展示", content)
            
            return display_filepath
        except Exception as e:
            logging.error(f"Error generating detailed inference display file: {e}")
            return None

    def _create_inference_display_window(self, title: str, content: str):
        """创建弹窗展示推理信息（非阻塞）"""
        try:
            # 获取非阻塞弹窗实例
            window = NonBlockingInferenceWindow.get_instance()
            
            # 显示窗口（如果尚未显示）
            window.show_window(title)
            
            # 等待窗口初始化完成
            import time
            start_time = time.time()
            while not window.is_window_running() and (time.time() - start_time) < 5:
                time.sleep(0.1)
            
            # 更新窗口内容
            window.update_content(content)
                
        except Exception as e:
            logging.error(f"Error creating inference display window: {e}")

    def _get_current_time(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _generate_detailed_inference_display_file(self, vehicle_id: str, message_history: List[str], rule: str,
                                                 input_filepath: str, output_filepath: str, decision_result: str):
        """生成详细的推理展示文件，包含输入、输出和决策结果，并在弹窗中展示"""
        try:
            # 创建推理展示目录
            inference_display_dir = os.path.join(self.project_root, 'TSRL_inference', 'Inference_display')
            os.makedirs(inference_display_dir, exist_ok=True)
            
            # 生成展示文件路径
            display_filename = f'Detailed_Inference_display_{vehicle_id}.txt'
            display_filepath = os.path.join(inference_display_dir, display_filename)
            
            # 准备展示内容
            content = f"=== TSRL详细推理展示 ===\n\n"
            content += f"车辆ID: {vehicle_id}\n"
            content += f"时间: {self._get_current_time()}\n\n"
            
            content += f"=== 匹配的规则 ===\n{rule}\n\n"
            
            content += f"=== 消息历史 ===\n"
            for i, msg in enumerate(message_history, 1):
                content += f"{i}. {msg}\n"
            content += "\n"
            
            # 读取推理输入文件内容
            content += f"=== 推理输入文件内容 ({os.path.basename(input_filepath)}) ===\n"
            if os.path.exists(input_filepath):
                with open(input_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输入文件不存在\n"
            content += "\n"
            
            # 读取TSRL推理输出文件内容
            content += f"=== TSRL推理输出内容 ({os.path.basename(output_filepath)}) ===\n"
            if os.path.exists(output_filepath):
                with open(output_filepath, 'r', encoding='utf-8') as f:
                    content += f.read()
            else:
                content += "输出文件不存在\n"
            content += "\n"
            
            # 添加解析后的决策结果
            content += f"=== 解析后的决策结果 ===\n"
            if decision_result:
                content += f"{decision_result}\n"
            else:
                content += "无决策结果\n"
            
            # 写入展示文件
            with open(display_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            # 创建弹窗展示内容
            self._create_inference_display_window("TSRL详细推理展示", content)
            return display_filepath
        except Exception as e:
            logging.error(f"Error generating detailed inference display file: {e}")
            return None

    def make_decision(
        self,
        T: float,
        observation: Observation,
        road_graph: RoadGraph,
        prediction: Prediction = None,
        config: dict = None,
        num_readmessages: int = 10,
    ) -> MultiDecision:
        """
        基于TSRL的多车决策器实现
        步骤：
        1. 读取消息历史文件
        2. 遍历规则文件中的每条规则
        3. 检查规则条件是否满足
        4. 生成推理输入文件
        5. 运行TSRL推理引擎
        6. 解析输出并生成决策
        """
        complete_decisions = MultiDecision()
        
        # 获取所有需要决策的车辆
        decision_vehicles = [veh for veh in observation.vehicles if veh.vtype != 'OUT_OF_AOI']
        
        # 读取规则
        rules = self._read_rules()
        if not rules:
            logging.warning("No rules found, skipping TSRL decision making")
            return complete_decisions
        
        # 为每辆车做决策
        for vehicle in decision_vehicles:
            vehicle_id = str(vehicle.id)
            # 读取该车辆的消息历史，默认读取最新的num_readmessages条消息
            message_history = self._read_message_history(vehicle_id, max_messages=num_readmessages)
            if not message_history:
                logging.warning(f"No message history for vehicle {vehicle_id}")
                continue
            
            # 遍历所有规则
            for rule in rules:
                if ":-" not in rule:
                    continue
                    
                head, conditions = self._parse_rule(rule)
                if not head or not conditions:
                    continue
                
                decision_result = None
                # 检查规则条件是否满足
                if self._check_conditions(conditions, message_history):
                    logging.debug(f"Rule conditions satisfied for vehicle {vehicle_id}: {rule}")
                    
                    # 生成推理输入文件
                    input_filepath = self._generate_inference_input(vehicle_id, message_history, rule, head)
                    if not input_filepath:
                        continue
                    
                    # 运行TSRL推理
                    output_filepath = self._run_tsrl_inference(input_filepath, vehicle_id)  
                    if not output_filepath:
                        continue
                    
                    # 解析推理输出
                    decision_result = self._parse_inference_output(output_filepath, head)
                    
                    # 如果规则条件满足，生成推理展示文件并弹窗展示
                    if decision_result:
                        # 生成详细的推理展示文件并弹窗展示
                        self._generate_detailed_inference_display_file(vehicle_id, message_history, rule, input_filepath, output_filepath, decision_result)
                    
                    if decision_result:
                        # 创建决策
                        decision_at_t = SingleStepDecision()
                        decision_at_t.action = decision_result
                        decision_at_t.expected_time = T + config["DECISION_RESOLUTION"]  # 这里应该从配置中获取
                        
                        # 根据规则头部确定行为类型
                        action_name = self._extract_action_from_head(head)
                        # 使用action_name_to_behaviour_mapper映射action_name到Behaviour
                        # 对于ChangeLane行为，使用get_lane_change_behaviour方法根据可用车道选择合适的变道行为
                        if action_name == "ChangeLane":
                            decision_at_t.behaviour = action_name_to_behaviour_mapper.get_lane_change_behaviour(
                                action_name, vehicle, road_graph)
                        else:
                            decision_at_t.behaviour = action_name_to_behaviour_mapper.get_behaviour(action_name)
                            
                        if decision_at_t.behaviour is None:
                            logging.warning(f"Unknown behaviour for action {action_name}")
                            continue
                        
                        complete_decisions.results[vehicle] = [decision_at_t]
                        logging.info(f"Decision made for vehicle {vehicle_id}: {decision_result}")
                        break  # 找到一个适用规则就停止
                else:
                    # 消息列表和推理规则没有对应，所以返回空决策
                    decision_at_t = SingleStepDecision()
                    decision_at_t.action = decision_result
                    decision_at_t.expected_time = T + config["DECISION_RESOLUTION"]
                    complete_decisions.results[vehicle] = [decision_at_t]

        return complete_decisions