"""
功能：车辆通信模块
作者：Wu Hao
创建日期：2025-07-15
"""

# 目标：7.17，写入每辆车的存储库，存储车辆的交流消息
from __future__ import annotations
import glob
import logging
import os
import time
import uuid
from typing import Dict, List, Optional
import logger
from logger import Logger
from enum import Enum
from add.display import NonBlockingInferenceWindow, NonBlockingVehicleDisplayWindow

class Performative(str, Enum):
    Inform = "Inform" # 告知
    Query = "Query" # 询问
    Request = "Request" # 请求
    Request_whenever = "Request-whenever" # 每次……即请求
    Accept = "Accept" # 接收
    Refuse = "Refuse" # 拒绝
    Failure = "Failure" # 失败
    Confuse = "Confuse" # 疑惑
    Other = 'None' # 其他


# 9.16 定义语义信息类
class Message:
    """消息类，封装语义交互信息体内容
    
    根据FIPA ACL消息标准，消息包含以下参数：
    a) Message-Identifier：消息体标识符，用于唯一地表示消息帧中的消息体
    b) Performative：述行词，表示消息交互的行为类型
    c) Sender：发送者，表示消息发送者的身份
    d) Sender-Category：发送者类别，表示发送者的角色或分类
    e) Receiver：接收者，表示消息的预期接收者的身份
    f) Receiver-Category：接收者类别，表示接收者的角色或分类
    g) Reply-To：消息回复对象，指示此对话线程中的后续消息将定向到的主体
    h) Content：消息内容，表示消息的内容，为交互语句
    i) Language：消息语言，表示表达参数Content消息内容所使用的语言
    j) Ontology：本体，表示用于赋予参数Content消息内容中的符号含义的本体
    k) Protocol：通信协议，表示发送代理在消息中采用的底层通信协议
    l) Conversation-Identifier：会话标识符，表示正在进行的消息序列所属哪个会话
    m) Reply-With：响应标识符，表示响应主体将使用该表达式来识别此消息
    n) In-Reply-To：回复标识符，表示该消息为此前较早消息的回复消息
    o) Reply-By：答复最晚时间，表示发送者希望接收者答复的最晚时间
    """
    
    def __init__(
        self,
        sender_id: str,# 发送者
        sender_category: Communicator,# 发送者类别
        receiver_id: str,# 接收者
        receiver_category: Communicator,# 接收者类别
        content: str, # 消息内容
        performative: Performative,# 述行词
        message_id: Optional[str] = None, # 消息体标识符
        reply_to: Optional[str] = None,# 消息回复对象
        language: Optional[str] = None,# 消息语言
        ontology: Optional[str] = None,# 本体，用于赋予参数Content消息内容中的符号含义的本体
        protocol: Optional[str] = None,# 通信协议，表示发送代理在消息中采用的底层通信协议
        conversation_id: Optional[str] = None,# 会话标识符，表示正在进行的消息序列所属哪个会话
        reply_with: Optional[str] = None,# 响应标识符，表示响应主体将使用该表达式来识别此消息
        in_reply_to: Optional[str] = None,# 回复标识符，表示该消息为此前较早消息的回复消息
        reply_by: Optional[float] = None,# 答复最晚时间，表示发送者希望接收者答复的最晚时间
        timestamp: Optional[float] = None# 时间戳
    ):
        # 必需参数
        self.message_id = message_id or str(uuid.uuid4())  # 消息体标识符
        self.sender_id = sender_id  # 发送者
        self.sender_category = sender_category  # 发送者类别
        self.receiver_id = receiver_id  # 接收者
        self.receiver_category = receiver_category  # 接收者类别
        self.content = content  # 消息内容
        self.performative = performative  # 述行词
        self.timestamp = timestamp or time.time()  # 时间戳
        
        # 可选参数
        self.reply_to = reply_to  # 消息回复对象
        self.language = language  # 消息语言
        self.ontology = ontology  # 本体
        self.protocol = protocol  # 通信协议
        self.conversation_id = conversation_id or str(uuid.uuid4())  # 会话标识符
        self.reply_with = reply_with  # 响应标识符
        self.in_reply_to = in_reply_to  # 回复标识符
        self.reply_by = reply_by  # 答复最晚时间

    def __str__(self) -> str:
        """返回消息的字符串表示"""
        return f"Message(id={self.message_id}, sender={self.sender_id}, receiver={self.receiver_id}, performative={self.performative}, content={self.content})"

    def __repr__(self) -> str:
        """返回消息的详细表示"""
        return self.__str__()
        
# 定义消息列表
class MessageList:
    def __init__(self):
        self.message_list: List[Message] = []
    
    # 定义方法：将消息添加到列表
    def append_message(self, message: Message):
        """将消息添加到列表"""
        self.message_list.append(message)
    
    # 定义方法：打印消息列表
    def print_message_list(self):
        """打印消息列表"""
        for msg in self.message_list:
            print(f"{msg.sender_id} -> {msg.receiver_id}: {msg.content}\n")
    
    # 定义方法：将当前车辆的消息列表保存到当前文件夹的文本文档中
    def save_message_list(self, vehicle_id: str, loc: str):
        """将消息列表保存到当前文件夹的文本文档中"""
        # 确保路径存在
        os.makedirs(loc, exist_ok=True)
        file_path = os.path.join(loc, f"message_{vehicle_id}_history.txt")
        with open(file_path, "a") as file:
            # 9.18 先将当前文件中的消息列表清空
            file.truncate(0)
            for msg in self.message_list:
                # file.write(f"{msg.sender_id} -> {msg.receiver_id}: {msg.content}\n")
                file.write(f"{msg.content}\n")

class Communicator:
    """基础通信器，作为其他通信器的基类"""
    def __init__(self, id: str, communication_manager: CommunicationManager):
        self.id = id  # 交通主体ID
        self.communication_manager = communication_manager  # 通信管理器
        self.message_history: MessageList = MessageList()  # 消息历史列表
        self.logger = logger.get_logger(__name__)  # 日志记录器
        self.Scenario_Name = self.communication_manager.Scenario_Name
        communication_manager.register(self)

    def _save_display_text(self, content: str):
        """保存显示文本到文件"""
        # 确保目录存在
        os.makedirs(f"message_history/{self.Scenario_Name}", exist_ok=True)
        # 将内容保存至当前文件夹的display_text.txt文件中，并换行
        with open(f"message_history/{self.Scenario_Name}/display_text.txt", "a", encoding="utf-8") as file:
            file.write(content + "\n")

    def _save_message_history(self):
        """保存消息历史到文件"""
        # 将消息列表在message_history文件夹中的文本文件中打印出来
        self.message_history.save_message_list(self.id, loc=f"message_history/{self.Scenario_Name}")
    
class CommunicationManager:
    """通信管理器，负责消息路由和分发"""
    def __init__(self, Scenario_Name: str):
        self.subscribers: Dict[str, Communicator] = {} # 订阅者列表
        self.logger = logger.get_logger(__name__)# 日志记录器
        self.message_history: List[Message] = [] # 全局消息历史记录列表
        self.Scenario_Name = Scenario_Name

    def register(self, communicator: Communicator):
        """将通信器注册在通信管理器"""
        self.subscribers[communicator.id] = communicator
    
    # def register_vehicle(self, vehicle: VehicleCommunicator):
    #     """将车辆注册在通信管理器"""
    #     self.subscribers[vehicle.vehicle_id] = vehicle
    
    # def register_rsu(self, rsu: RSUCommunicator):
    #     """将RSU注册在通信管理器"""
    #     self.subscribers[rsu.rsu_id] = rsu

    def send_message(self, message: Message):
        """发送消息并路由到接收者"""
        # 记录消息到日志
        self.logger.info(f"Message sent: {message.sender_category}{message.sender_id} -> {message.receiver_category}{message.receiver_id}: {message.content}")
        # 直接发送给目标接收者
        target_found = False
        for subscriber_id, subscriber in self.subscribers.items():
            # 检查接收者ID和类别是否匹配
            if subscriber_id == message.receiver_id:
                # 如果消息指定了接收者类别，则需要匹配类别
                if message.receiver_category is None or hasattr(subscriber, 'category') and subscriber.category == message.receiver_category:
                    subscriber.receive_message(message)
                    target_found = True
                    break
        # 如果没有找到特定接收者，广播给所有通信器（除了发送者本身）
        if not target_found:
            for communicator_id, communicator in self.subscribers.items():
                if communicator_id != message.sender_id:
                    communicator.receive_message(message)
    
    # 8.19 新增方法：删除所有消息历史文件
    def cleanup_message_files(self):
        """删除所有消息历史文件"""
        try:
            # 获取当前目录下所有message_*.txt文件
            pattern = "message_*_history.txt"
            files_to_remove = glob.glob(pattern)
            
            for file_path in files_to_remove:  # 修复：将原来的"path"改为"file_path"
                try:
                    os.remove(file_path)
                    self.logger.info(f"Message_history file: {file_path} deleted")
                except Exception as e:
                    self.logger.error(f"Deleting {file_path} Error: {e}")
                    
            self.logger.info(f"{len(files_to_remove)} message_history files deleted")
        except Exception as e:
            self.logger.error(f"Error deleting message_history files: {e}")

    # 8.19 新增方法：清空所有消息历史文件内容，而不删除文件
    def clear_message_files_content(self):
        """清空所有消息历史文件的内容（保留文件）"""
        try:
            # 获取当前目录下message_history文件夹下所有message_*.txt文件
            loc = "message_history"
            pattern = os.path.join(loc, "message_*_history.txt")
            files_to_clear = glob.glob(pattern)
            
            for file_path in files_to_clear:
                try:
                    # 以写入模式打开文件，清空内容
                    with open(file_path, 'w') as file:
                        file.truncate(0)  # 清空文件内容
                    self.logger.info(f"Message_history file content cleared: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error clearing content of {file_path}: {e}")
                    
            self.logger.info(f"{len(files_to_clear)} message_history files content cleared")
        except Exception as e:
            self.logger.error(f"Error clearing message_history files content: {e}")
    
    # 8.27 删除display_text文件
    def cleanup_display_text(self,loc: str):
        """删除display_text文件"""
        try:
            # 获取特定目录下所有display_text文件
            file_path = os.path.join(loc, "display_text.txt")
            # 检查文件是否存在再删除
            if os.path.exists(file_path):
                # 删除文件
                os.remove(file_path)
                self.logger.info(f"已删除文件: {file_path}")
            else:
                self.logger.info(f"文件不存在，无需删除: {file_path}")
        except Exception as e:
            self.logger.error(f"删除文件时出错: {e}")

# 展示 display_text.txt 文件内容
    def show_display_text(self, Scenario_Name: str):
        try:
            display_filepath = os.path.join('message_history', Scenario_Name , 'display_text.txt')
            # 检查文件是否存在
            if os.path.exists(display_filepath):
                with open(display_filepath, 'r', encoding='utf-8') as file:
                    display_content = file.read()
                self._create_display_window("交通场景互操作语言交互展示", display_content)
            else:
                # 如果文件不存在，创建一个空文件
                os.makedirs(os.path.dirname(display_filepath), exist_ok=True)
                with open(display_filepath, 'w', encoding='utf-8') as file:
                    pass  # 创建空文件
                self._create_display_window("交通场景互操作语言交互展示", "暂无内容")
        except Exception as e:
            self.logger.error(f"Error showing display text: {e}")
    
    def _create_display_window(self, title: str, content: str):
        """创建弹窗展示 display_text.txt 文件内容（非阻塞）"""
        try:
            # 获取非阻塞弹窗实例
            window = NonBlockingVehicleDisplayWindow.get_instance()
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
            logging.error(f"Error creating vehicle display window: {e}")

    def _get_current_time(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 8.27 清除display_text文件里的内容，而不删除文件
    def clear_display_text_content(self,loc:str):
        """清空display_text.txt文件的内容（保留文件）"""
        try:
            # 获取特定目录下display_text.txt文件
            file_path = os.path.join(loc, "display_text.txt")
            # 检查文件是否存在
            if os.path.exists(file_path):
                try:
                    # 以写入模式打开文件，清空内容
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.truncate(0)  # 清空文件内容
                    self.logger.info(f"已清空display_text文件内容: {file_path}")
                except Exception as e:
                    self.logger.error(f"清空文件 {file_path} 内容时出错: {e}")
            else:
                self.logger.info(f"文件不存在，无需清空: {file_path}")
        except Exception as e:
            self.logger.error(f"清空display_text文件内容时出错: {e}")


class VehicleCommunicator(Communicator):
    """车辆通信器，负责车辆间通信"""
    def __init__(self, vehicle_id, vehicle: 'control_Vehicle', communication_manager: CommunicationManager, if_egoCar: bool = False):
        super().__init__(vehicle_id, communication_manager)
        self.if_egoCar = if_egoCar
        self.vehicle = vehicle
        self.id = vehicle_id
        # 注册到通信管理器
        communication_manager.register(self)
    
    # 定义方法：主动发送消息
    def send(self, content: str, target_id: str = None, target_category: Communicator = None, performative: Performative = Performative.Other):
        """主动发送消息"""
        # 文本前缀，取决于是否为egoCar
        prefix = f"Send by HV {self.id}:" if self.if_egoCar else f"Send by RV {self.id}:"
        # 完整文本
        full_content = f"{prefix}{content}"
        # 发送消息
        message = Message(
            sender_id=self.id,
            sender_category=self,
            receiver_id=target_id or "broadcast",
            receiver_category=target_category,
            content=content,
            performative=performative
        )
        # 在终端输出
        print(full_content)
        # 保存显示文本
        self._save_display_text(full_content)
        # 存储消息到本地消息历史列表
        self.message_history.append_message(message)
        # 将消息真正发送出去
        self.communication_manager.send_message(message)
        # 保存消息历史
        self._save_message_history()

    def receive_message(self, message: Message):
        """接收消息并处理"""
        if message.sender_id == self.id:
            return  # 忽略自己发送的消息
        # 生成回复内容
        if self.if_egoCar:
            reply_prefix = f"Received by HV {self.id}:"
        else:
            reply_prefix = f"Received by RV {self.id}:"
        # 提取原始内容（去除发送者前缀）
        content = message.content
        reply_content = f"{reply_prefix}{content}"
        # 存储消息到本地列表
        reply_message = Message(
            sender_id=message.receiver_id,
            sender_category=self,
            receiver_id=message.sender_id,
            receiver_category=message.sender_category,
            content=content,
            performative=Performative.Inform
        )
        # 添加消息
        self.message_history.append_message(reply_message)
        # 保存显示文本
        self._save_display_text(reply_content)
        # 保存消息历史
        self._save_message_history()
        # 在终端输出接收信息
        print(reply_content)
        # 根据接收到的内容执行相应操作
        self.process_received_content(message)

    def process_received_content(self, messages):
        """处理接收到的消息内容"""
        # 判断messages是否为列表，分别处理
        if isinstance(messages, list):
            for message in messages:
                self.Message_process(message)
        else:
            self.Message_process(messages)

    def Message_process(self, message: Message):
        """处理消息内容，返回处理后的字符串"""
        content = message.content
        # # 1. 同车道相对关系
        # if "VehicleInLane" in content:
        #     # 检查VehicleInLane()中通过,相隔的第三个字符串是否为Front
        #     # 提取VehicleInLane括号中的内容
        #     import re
        #     match = re.search(r'VehicleInLane\(([^)]+)\)', content)
        #     if match:
        #         # 按逗号分割参数
        #         params = match.group(1).split(',')
        #         # 检查是否有至少3个参数，且第3个参数（索引为2）是否为Front——同车道前方有其它车
        #         if len(params) >= 3 and params[2].strip() == "Front":
                    

class RSUCommunicator(Communicator):
    """路侧单元通信器，负责路侧单元的通信"""
    def __init__(self, rsu_id: str, rsu: 'control_RSU', communication_manager: CommunicationManager):
        super().__init__(rsu_id, communication_manager)
        self.id=rsu_id
        self.rsu = rsu
        self.category = self
        # 添加vehicles和roadgraph参数的存储
        self.vehicles = None
        self.roadgraph = None
        # 注册到通信管理器
        communication_manager.register(self)
    
    # 添加设置vehicles和roadgraph的方法
    def set_context(self, vehicles: Dict[str, 'control_Vehicle'], roadgraph):
        """设置上下文参数"""
        self.vehicles = vehicles
        self.roadgraph = roadgraph
    
    # 定义方法：主动发送消息
    def send(self, content: str, target_id: str = None, performative: Performative = Performative.Other):
        """主动发送消息"""
        # 文本前缀
        prefix = f"Send by RSU {self.id}:"
        # 完整文本
        full_content = f"{prefix}{content}"
        # 发送消息
        message = Message(
            sender_id=self.id,
            sender_category=self,
            receiver_id=target_id or "broadcast",
            receiver_category=None,  # RSU发送消息时可能没有指定接收者类别
            content=content,  # 发送原始内容，不带前缀
            performative=performative
        )
        # 在终端输出
        print(full_content)
        # 保存显示文本
        self._save_display_text(full_content)
        # 存储消息到本地消息历史列表
        self.message_history.append_message(message)
        # 将消息发送出去
        self.communication_manager.send_message(message)
        # 保存消息历史
        self._save_message_history()

    def receive_message(self, message: Message):
        """接收消息并处理"""
        if message.sender_id == self.id:
            return  # 忽略自己发送的消息
        # 生成回复内容
        reply_prefix = f"Received by RSU {self.id}:"
        # 提取原始内容（去除发送者前缀）
        # 添加对消息内容格式的检查，防止索引越界
        if ":" in message.content:
            content = message.content.split(":", 1)[1].strip()
        else:
            # 如果消息内容中没有冒号，使用完整内容
            content = message.content
        reply_content = f"{reply_prefix}{content}"
        # 存储消息到本地列表
        reply_message = Message(
            sender_id=message.receiver_id,
            sender_category=self,
            receiver_id=message.sender_id,
            receiver_category=message.sender_category,
            content=content,  # 存储原始内容，不带前缀
            performative=Performative.Other
        )
        # 添加消息
        self.message_history.append_message(reply_message)
        # 保存显示文本
        self._save_display_text(reply_content)
        # 保存消息历史
        self._save_message_history()
        # 在终端输出接收信息
        print(reply_content)
        # 根据接收到的内容执行相应操作
        self.process_received_content(message)

    def process_received_content(self, message):
        """处理接收到的消息内容"""
        # 判断message是否为列表，分别处理
        if isinstance(message, list):
            for msg in message:
                self.Message_process(msg)
        else:
            self.Message_process(message)
        

    def Message_process(self, message: Message):
        # 处理对于RSU探测范围内的车辆信息请求消息
        if message.content.startswith("InformationRequest2RSU"):
            # 检查是否已设置上下文参数
            if self.vehicles is None or self.roadgraph is None:
                self.logger.error("Context parameters (vehicles or roadgraph) not set for RSUCommunicator")
                return
            # RSU使用detect_vehicles_in_range方法获取范围内车辆信息并回复message发出者
            # 获取在RSU探测范围内的车辆信息
            detected_messages = self.rsu.detect_vehicles_in_range(self.vehicles, self.roadgraph, message)
            # 将检测到的车辆信息打包并发送给Ego车辆
            if detected_messages:  
                # 将列表中的字典转换为多行字符串，每个键值对占一行
                formatted_messages = []
                for msg in detected_messages:
                    if isinstance(msg, dict):
                        # 将字典中的每个键值对转换为字符串，并用换行符连接
                        dict_lines = [f"{key}: {value}" for key, value in msg.items()]
                        formatted_messages.append("\n".join(dict_lines))
                    else:
                        # 如果不是字典，直接转换为字符串
                        formatted_messages.append(str(msg))
                # 用换行符连接所有消息
                detected_messages_str = "\n".join(formatted_messages)
                # RSU发送回复消息给Ego车辆
                self.send(detected_messages_str, message.sender_id, performative=Performative.Inform)
            else:
                # 如果没有检测到车辆，发送空结果消息
                self.send("No vehicles detected in range", message.sender_id, performative=Performative.Inform)

