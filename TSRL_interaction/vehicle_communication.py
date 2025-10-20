"""
功能：车辆通信模块
作者：Wu Hao
创建日期：2025-07-15
"""

# 目标：7.17，写入每辆车的存储库，存储车辆的交流消息
from __future__ import annotations
import glob
import os
import time
import uuid
from typing import Dict, List, Optional
import logger
from logger import Logger
from enum import Enum


class Performative(str, Enum):
    Inform = "Inform"
    Query = "Query"
    Request = "Request"
    Request_whenever = "Request-whenever"
    Accept = "Accept"
    Refuse = "Refuse"
    Failure = "Failure"
    Confuse = "Confuse"
    Other = 'None'


# 9.16 定义语义信息类
class Message:
    """消息类，封装语义交互信息体内容
    
    根据FIPA ACL消息标准，消息包含以下参数：
    a) Message-Identifier：消息体标识符，用于唯一地表示消息帧中的消息体
    b) Performative：述行词，表示消息交互的行为类型
    c) Sender：发送者，表示消息发送者的身份
    d) Receiver：接收者，表示消息的预期接收者的身份
    e) Reply-To：消息回复对象，指示此对话线程中的后续消息将定向到的主体
    f) Content：消息内容，表示消息的内容，为交互语句
    g) Language：消息语言，表示表达参数Content消息内容所使用的语言
    h) Ontology：本体，表示用于赋予参数Content消息内容中的符号含义的本体
    i) Protocol：通信协议，表示发送代理在消息中采用的底层通信协议
    j) Conversation-Identifier：会话标识符，表示正在进行的消息序列所属哪个会话
    k) Reply-With：响应标识符，表示响应主体将使用该表达式来识别此消息
    l) In-Reply-To：回复标识符，表示该消息为此前较早消息的回复消息
    m) Reply-By：答复最晚时间，表示发送者希望接收者答复的最晚时间
    """
    
    def __init__(
        self,
        sender_id: str,# 发送者
        receiver_id: str,# 接收者
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
        self.receiver_id = receiver_id  # 接收者
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

class CommunicationManager:
    """通信管理器，负责消息路由和分发"""
    def __init__(self):
        self.subscribers: Dict[str, VehicleCommunicator] = {} # 订阅者列表
        self.logger = logger.get_logger(__name__)# 日志记录器
        self.message_history: List[Message] = [] # 全局消息历史记录列表

    def register_vehicle(self, vehicle: VehicleCommunicator):
        """将车辆注册在通信管理器"""
        self.subscribers[vehicle.vehicle_id] = vehicle
    
    def register_rsu(self, rsu: RSUCommunicator):
        """将RSU注册在通信管理器"""
        self.subscribers[rsu.rsu_id] = rsu

    def send_message(self, message: Message):
        """发送消息并路由到接收者"""
        # 记录消息到日志
        self.logger.info(f"Message sent: {message.sender_id} -> {message.receiver_id}: {message.content}")
        # 直接发送给目标车辆
        if message.receiver_id in self.subscribers:
            self.subscribers[message.receiver_id].receive_message(message)
        else:
            # 如果接收者不存在，广播给所有车辆
            for vehicle_id, vehicle in self.subscribers.items():
                if vehicle_id != message.sender_id:
                    vehicle.receive_message(message)
    
    # 8.19 新增方法：删除所有消息历史文件
    def cleanup_message_files(self):
        """删除所有消息历史文件"""
        try:
            # 获取当前目录下所有message_*.txt文件
            pattern = "message_*_history.txt"
            files_to_remove = glob.glob(pattern)
            
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    self.logger.info(f"已删除消息历史文件: {file_path}")
                except Exception as e:
                    self.logger.error(f"删除文件 {file_path} 时出错: {e}")
                    
            self.logger.info(f"共清理了 {len(files_to_remove)} 个消息历史文件")
        except Exception as e:
            self.logger.error(f"清理消息历史文件时出错: {e}")

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
                    self.logger.info(f"已清空消息历史文件内容: {file_path}")
                except Exception as e:
                    self.logger.error(f"清空文件 {file_path} 内容时出错: {e}")
                    
            self.logger.info(f"共清空了 {len(files_to_clear)} 个消息历史文件的内容")
        except Exception as e:
            self.logger.error(f"清空消息历史文件内容时出错: {e}")
    
    # 8.27 删除display_text文件
    def cleanup_display_text(self,loc: str):
        """删除display_text文件"""
        # 获取特定目录下所有display_text文件
        file_path = os.path.join(loc, "display_text.txt")
        try:
            # 删除文件
            os.remove(file_path)
            self.logger.info(f"已删除文件: {file_path}")
        except Exception as e:
            self.logger.error(f"删除文件{file_path}时出错: {e}")


    # 8.27 清除display_text文件里的内容，而不删除文件
    def clear_display_text_content(self,loc:str):
        """清空display_text.txt文件的内容（保留文件）"""
        try:
            # 获取特定目录下display_text.txt文件
            file_path = os.path.join(loc, "display_text.txt")
            try:
                # 以写入模式打开文件，清空内容
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.truncate(0)  # 清空文件内容
                self.logger.info(f"已清空display_text文件内容: {file_path}")
            except Exception as e:
                self.logger.error(f"清空文件 {file_path} 内容时出错: {e}")
                
        except Exception as e:
            self.logger.error(f"清空display_text文件内容时出错: {e}")


class VehicleCommunicator:
    """车辆通信器，负责车辆间通信"""
    def __init__(self, vehicle_id: str, communication_manager: CommunicationManager,if_egoCar: bool = False):
        self.if_egoCar = if_egoCar
        self.vehicle_id = vehicle_id
        self.communication_manager = communication_manager
        self.logger = logger.get_logger(__name__)
        # 初始化存储信息的列表
        self.message_history: MessageList = MessageList()
        # 注册到通信管理器
        communication_manager.register_vehicle(self)
    
    # 定义方法：主动发送消息
    def send(self, content: str, target_id: str = None, performative: Performative = Performative.Other):
        """主动发送消息"""
        # # 文本前缀，取决于是否为egoCar
        prefix = f"Send by HV {self.vehicle_id}:" if self.if_egoCar else f"Send by RV {self.vehicle_id}:"
        # 完整文本
        full_content = f"{prefix}{content}"
        # 发送消息
        message = Message(
            sender_id=self.vehicle_id,
            receiver_id=target_id or "broadcast",
            # content=full_content,
            content=content,
            performative=performative
        )
        # 在终端输出
        print(full_content)

        # 将full_content保存至当前文件夹的display_text.txt文件中，并换行
        with open("message_history/display_text.txt", "a", encoding="utf-8") as file:
            file.write(full_content + "\n")
        # with open("message_history/display_text.txt", "a", encoding="utf-8") as file:
        #     file.write(content + "\n")
        # 存储消息到本地消息历史列表
        self.message_history.append_message(message)
        # 将消息真正发送出去
        self.communication_manager.send_message(message)
        # 将车辆消息列表在message_history文件夹中的文本文件中打印出来
        self.message_history.save_message_list(self.vehicle_id,loc='message_history')

    def receive_message(self, message: Message):
        """接收消息并处理"""
        if message.sender_id == self.vehicle_id:
            return  # 忽略自己发送的消息
        # 生成回复内容
        if self.if_egoCar:
            reply_prefix = f"Received by HV {self.vehicle_id}:"
        else:
            reply_prefix = f"Received by RV {self.vehicle_id}:"

        # 提取原始内容（去除发送者前缀）
        content = message.content
        reply_content = f"{reply_prefix}{content}"
        # 存储消息到本地列表
        reply_message=Message(
            sender_id=message.receiver_id,
            receiver_id=message.sender_id,
            # content=reply_content,
            content=content,
            performative=Performative.Inform
        )
        # 添加消息
        self.message_history.append_message(reply_message)
        # 保存至当前文件夹的display_text.txt文件中，并换行
        with open("message_history/display_text.txt", "a", encoding="utf-8") as file:
            file.write(reply_content + "\n")
        # 将本地列表在当前文件夹中的文本文件中打印出来
        self.message_history.save_message_list(self.vehicle_id, loc='message_history')
        # 在终端输出接收信息
        print(reply_content)
        # 根据接收到的内容执行相应操作
        self.process_received_content(content)

    def process_received_content(self, content: str):
        """处理接收到的消息内容"""
        # 示例：如果接收到紧急停车消息，可以触发相应处理
        if content.startswith("EmergencyStation"):
            # 这里可以添加自车收到紧急停车消息后的逻辑
            self.logger.warning(f"HV {self.vehicle_id} received emergency message: {content}")
            # 例如：触发自车的紧急响应
            # self.vehicle.emergency_response()

class RSUCommunicator:
    """路侧单元通信器，负责路侧单元的通信"""
    def __init__(self, rsu_id: str, communication_manager: CommunicationManager):
        self.rsu_id = rsu_id
        self.communication_manager = communication_manager
        self.logger = logger.get_logger(__name__)
        # 初始化存储信息的列表
        self.message_history: MessageList = MessageList()
        # 注册到通信管理器
        communication_manager.register_rsu(self)
    
    # 定义方法：主动发送消息
    def send(self, content: str, target_id: str = None, performative: Performative = Performative.Other):
        """主动发送消息"""
        # 文本前缀
        prefix = f"Send by RSU {self.rsu_id}:"
        # 完整文本
        full_content = f"{prefix}{content}"
        # 发送消息
        message = Message(
            sender_id=self.rsu_id,
            receiver_id=target_id or "broadcast",
            content=full_content,
            performative=performative
        )
        # 在终端输出
        print(full_content)

        # 将full_content保存至当前文件夹的display_text.txt文件中，并换行
        with open("message_history/display_text.txt", "a", encoding="utf-8") as file:
            file.write(full_content + "\n")
        # 存储消息到本地消息历史列表
        self.message_history.append_message(message)
        # 将消息发送出去
        self.communication_manager.send_message(message)
        # 将本地列表在当前文件夹中的文本文件中打印出来
        self.message_history.save_message_list(self.rsu_id, loc='message_history')

    def receive_message(self, message: Message):
        """接收消息并处理"""
        if message.sender_id == self.rsu_id:
            return  # 忽略自己发送的消息
        # 生成回复内容
        reply_prefix = f"Received by RSU {self.rsu_id}:"

        # 提取原始内容（去除发送者前缀）
        # 添加对消息内容格式的检查，防止索引越界
        if ":" in message.content:
            content = message.content.split(":", 1)[1].strip()
        else:
            # 如果消息内容中没有冒号，使用完整内容
            content = message.content
        reply_content = f"{reply_prefix}{content}"
        # 存储消息到本地列表
        reply_message=Message(
            sender_id=message.receiver_id,
            receiver_id=message.sender_id,
            content=reply_content,
            performative=Performative.Other
        )
        # 添加消息
        self.message_history.append_message(reply_message)
        # 保存至当前文件夹的display_text.txt文件中，并换行
        with open("message_history/display_text.txt", "a", encoding="utf-8") as file:
            file.write(reply_content + "\n")
        # 将本地列表在当前文件夹中的文本文件中打印出来
        self.message_history.save_message_list(self.rsu_id, loc='message_history')
        # 在终端输出接收信息
        print(reply_content)
        # 根据接收到的内容执行相应操作
        self.process_received_content(content)

    def process_received_content(self, content: str):
        """处理接收到的消息内容
        根据语义信息类型的不同，执行不同的处理逻辑"""
        
            
