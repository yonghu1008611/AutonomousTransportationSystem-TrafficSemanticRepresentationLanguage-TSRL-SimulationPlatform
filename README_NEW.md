# ATSISP项目概览 (IFLOW上下文)

## 项目简介

本项目是基于LimSim的自主交通语义交互仿真平台(Autonomous Transportation Semantic Interaction Simulation Platform, ATSISP)。它扩展了LimSim的功能，加入了车辆间以及车辆与路侧单元(RSU)的语义通信交互能力，并集成了基于时空间逻辑(TSRL)的推理引擎，以模拟和分析交通场景下的复杂交互行为。

项目主要使用Python编写，依赖SUMO (Simulation of Urban MObility)进行底层交通仿真。

## 核心组件与功能

1.  **交通仿真核心 (simModel)**: 基于SUMO，负责构建和管理交通仿真环境，包括路网、车辆、轨迹等。支持实时仿真和回放模式 (`ModelExample.py`, `ReplayExample.py`)。

2.  **交通管理与规划 (trafficManager)**: 负责仿真中车辆的行为更新、决策和轨迹规划。核心是 `TrafficManager` 类，它整合了感知、预测、决策和规划模块。

3.  **语义交互层 (TSRL_interaction)**:
    *   实现了基于FIPA ACL标准的通信模型，定义了 `Message` 类和 `Performative` 枚举来表示交互消息体和行为类型（如Inform, Query, Request, Accept等）。
    *   `VehicleCommunicator` 和 `RSUCommunicator` 类负责处理车辆和RSU的通信逻辑，包括消息的发送、接收和处理。它们通过 `CommunicationManager` 进行消息路由和管理。

4.  **时空间推理引擎 (TSRL_representation)**:
    *   实现了一阶逻辑的知识库 (`FolKB`) 和推理算法（前向链接 `fol_fc_ask` 和反向链接 `fol_bc_ask`）。
    *   包含词法分析器(`Scanner`)、语法分析器(`Parser`)和解释器(`Interpreter`)，共同构成了TSIL (Temporal Spatial Interaction Language) 语言的处理流程，用于定义和执行语义交互规则。

5.  **应用场景示例**:
    *   `ForwardCollisionWarning.py`: 实现了前向碰撞预警场景，展示了如何在特定交通场景下应用语义交互和推理能力。该示例会在仿真开始时向TSRL推理引擎写入预定义的规则和查询。
    *   `Vehicle_RSU_Interacting.py`: 实现了车辆-RSU交互场景。
    *   `Human_Vehicle_Interacting.py`: 实现了人车加速交互场景。
    *   `Vehicle_Vehicle_Interacting.py`: 实现了车辆交互场景。

6.  **场景选择器 (`tkinter_scenario_selector.py`)**:
    *   提供了图形用户界面（GUI），方便用户快速选择和启动不同的仿真场景。
    *   包含典型交通场景和自定义交通场景的选项。

## 项目结构

*   `simModel/`: 交通仿真模型核心代码
*   `trafficManager/`: 交通管理与车辆规划逻辑
*   `TSRL_interaction/`: 语义交互通信模块
*   `TSRL_representation/`: 时空间推理引擎与TSIL语言实现
*   `networkFiles/`: 存放各种仿真场景的路网文件 (`.net.xml`) 和路由文件 (`.rou.xml`)
*   `message_history/`: 存放仿真过程中生成的车辆通信消息历史记录
*   `assets/`: 存放项目相关的图片资源
*   `evaluation/`, `logger/`, `utils/`: 辅助功能模块

## 开发与运行

### 环境要求

*   Python 3.9 - 3.11
*   SUMO >= 1.15.0
*   依赖库: `dearpygui`, `matplotlib`, `numpy`, `pandas`, `pynput`, `PyYAML`, `rich`, `sumolib`, `traci` (详见 `requirements.txt`)

### 安装与配置

1.  安装Python和SUMO环境
2.  克隆项目代码
3.  安装依赖: `pip install -r requirements.txt`

### 运行示例

*   **基础实时仿真**: `python ModelExample.py`
*   **前向碰撞预警场景**: `python ForwardCollisionWarning.py`
*   **车辆-RSU交互场景**: `python Vehicle_RSU_Interacting.py`
*   **人车加速交互场景**: `python Human_Vehicle_Interacting.py`
*   **车辆交互场景**: `python Vehicle_Vehicle_Interacting.py`
*   **仿真回放**: `python ReplayExample.py`
*   **场景选择器 (推荐)**: `python tkinter_scenario_selector.py` (使用Tkinter GUI)

### 自定义场景创建

通过场景选择器的"自定义交通场景"选项，用户可以创建新的仿真场景：

1.  创建路网文件（使用Netedit工具）
2.  创建路由文件
3.  添加其他必要的配置文件

## 开发约定与实践

*   **代码风格**: 遵循Python通用编码规范，部分文件包含中文注释以解释功能和逻辑。核心模块如 `trafficManager` 和 `TSRL_interaction` 有较详细的英文文档字符串 (docstring) 描述类和方法的功能。
*   **模块化**: 项目结构清晰，将仿真、规划、交互、推理等功能分离到不同模块和目录下，便于维护和扩展。
*   **通信机制**: 车辆和RSU通过 `CommunicationManager` 进行消息传递，消息内容遵循FIPA ACL标准，增强了交互的规范性和可扩展性。消息历史记录被保存到 `message_history/` 目录下，便于调试和分析。