"""
功能：创建ATPSIP仿真平台上的其他固定设施(偏向可视化)
Facilities：
    - 仿真基础 ：提供SUMO仿真环境中的基本设施功能
    - 数据存储 ：存储设施的历史轨迹数据（位置、速度、加速度等）
    - SUMO接口 ：直接与SUMO/traci交互
    - 路径管理 ：处理设施的路径规划和车道选择
    - 可视化支持 ：支持在GUI中绘制设施和轨迹
"""
from math import sqrt, pow


class RSU_detector:
    """
    功能：创建ATPSIP仿真平台上的【真实】RSU检测器，位于具体的车道上
    参数：
        id：检测器的唯一标识符
        lane：检测器所在的车道ID
        pos：检测器在车道上的位置（单位：米）
        detectlenth：检测器的检测长度（单位：米）
        detectfreq：检测器的检测频率（单位：赫兹）
        output：检测器的输出文件路径
    """
    def __init__(self, id: str) -> None:
        self.id = id
        self.lane : str = ''
        self.pos : float = 0.0
        self.detectlenth: float = 0.0
        self.detectfreq: float = 0.0
        self.output: str = ''

class RSU:
    """
    功能：创建ATPSIP仿真平台上的RSU(偏向可视化)
    """
    def __init__(self, id: str, deArea: float = 0) -> None:
        self.id = id
        self.x :float = 0.0 # 存储RSU投影中心坐标x
        self.y :float = 0.0 # 存储RSU投影中心坐标y
        self.length: float = 5.0   # SUMO默认值，RSU投影长度
        self.width: float = 1.8   # SUMO默认值，RSU投影宽度
        self.detectors: list = [] # 存储RSU的检测器
        # 检测区域半径，如果self.detectors非空则为self.detectors中检测器的最大检测长度，否则为deArea
        self.deArea: float = max([detector.detectlenth for detector in self.detectors]) if self.detectors else deArea
        
    def __str__(self) -> str:
        return f"RSU(id={self.id}, x={self.x}, y={self.y}, length={self.length}, width={self.width}, deArea={self.deArea})"

    def addDetector(self, detector: RSU_detector):
        self.detectors.append(detector)
        # 更新检测区域半径
        self.deArea = max(self.deArea, detector.detectlenth)
    
    def isInAoI(self, ego_lane: str, ego_pos: float, ego_deArea: float) -> bool:
        """
        判断RSU是否在ego车辆的AOI范围内
        通过检查Ego车辆所处车道，以及其所处车道上的位置与RSU在同一车道的检测器之间的距离是否小于AOI距离
        
        :param ego_lane: ego车辆当前所在的车道ID
        :param ego_pos: ego车辆在车道上的位置（距离车道起点的距离）
        :param netInfo: 网络信息对象
        :return: 如果RSU在AOI范围内返回True，否则返回False
        """
        ifinAOI=False
        # 遍历RSU的所有检测器
        for detector in self.detectors:
            # 检查检测器是否在与ego车辆相同的车道上
            if detector.lane == ego_lane:
                # 计算ego车辆位置与检测器位置之间的距离
                distance = abs(ego_pos - detector.pos)
                # 如果距离小于等于AOI半径，则认为RSU检测器进入车辆AOI范围内
                if distance <= ego_deArea:
                    ifinAOI=True
                    break
        # 如果没有找到在同一车道上的检测器，或者距离超出检测范围，则不在AOI内
        return ifinAOI
        
    def export2Dict(self, netInfo) -> dict:
        """
        导出RSU信息为字典格式
        :param netInfo: 网络信息对象
        :return: 包含RSU信息的字典
        """
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'deArea': self.deArea,
            'detectors': [{
            'id': detector.id,
            'lane': detector.lane,
            'pos': detector.pos,
            'detectlenth': detector.detectlenth,
            'detectfreq': detector.detectfreq,
            'output': detector.output } for detector in self.detectors]
        }

    