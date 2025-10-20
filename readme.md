![logo-full.svg](assets/limsimLOGO.png)

[![Custom badge](https://img.shields.io/badge/paper-Arxiv-b31b1b?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2307.06648)
[![Custom badge](https://img.shields.io/badge/Docs-page-green?logo=document)](https://pjlab-adg.github.io/LimSim)
[![Custom badge](https://img.shields.io/badge/video-Bilibili-74b9ff?logo=bilibili&logoColor=white)](https://www.bilibili.com/video/BV1rT411x7VF)
[![Custom badge](https://img.shields.io/badge/video-YouTube-FF0000?logo=youtube&logoColor=white)](https://youtu.be/YR2A25v0hj4)

## 🚀News: 
- **2024/09/25** [LimSimLight](https://github.com/PJLab-ADG/LimSim/tree/LimSimLight) can parse OpenDrive map files and simulate by the new self-developed engine！
- **2024/03/05** [LimSim++](https://github.com/PJLab-ADG/LimSim/tree/LimSim_plus) is now released for the applications of Multimodal LLMs!
- **2023/07/26** Add [the docs](https://pjlab-adg.github.io/LimSim/zh/GettingStarted/carla_cosim/) about co-sim with CARLA.
- **2023/07/13** The code is now released!
  
# LimSim

LimSim is a Long-term Interactive Multi-scenario traffic Simulator, which aims to provide a continuous simulation capability under the complex urban road network.

## Quick Start

- **3.9.0** <= [Python](https://www.python.org/) <= 3.11.0
- [SUMO](https://www.eclipse.org/sumo/) >= 1.15.0 

After configuring the runtime environment, download the LimSim source code to your local machine:

```powershell
git clone https://github.com/PJLab-ADG/LimSim.git
```

Finally, you need to install the required Python extensions:

```powershell
cd LimSim
pip install -r requirements.txt
```

Now, the local installation and deployment of LimSim are complete.

### 1. Real-time Sim
Real-time simulation following the Ego vehicle is the fundamental feature of LimSim. To experience it, run the following command:

```bash
python ModelExample.py
```

### 2. Simulation replay
In the root directory, running the following command will invoke LimSim's replay feature:

```powershell
python ReplayExample.py
```

**For more information on our code, please see our [Online Documentation](https://pjlab-adg.github.io/LimSim/)**.

If you have any problem when installing and deploying, feel free to [open an issue here](https://github.com/PJLab-ADG/LimSim/issues)!


## 🎁 Main Features

- [x] **Long-term**: Traffic flow can be generated over long periods under demand and route planning guidance.

- [x] **Diversity**: The built-in behavioral models take heterogeneous driving styles of vehicles into account.

- [x] **Interactivity**: Vehicles in the scenario area are controlled to address sophisticated interactions among vehicles.

- [x] **Multi-scenario**: The universal road components support a variety of road structures in the real world.

## 🖥️ GUI

LimSim has a cross-platform user-friendly GUI, including a beautiful simulation interface, information on road networks, and ego-vehicle status.
<p align="center">
  <img src="assets/limsim_gui.png" title="" alt="limsim_gui.png">
</p>

## 🎛️ 场景选择器

为了方便用户快速启动不同的仿真场景，我们提供了两个版本的场景选择器界面。

### 启动场景选择器

#### DearPyGUI版本（需要安装dearpygui）
```bash
python scenario_selector.py
```

#### Tkinter版本（系统自带，推荐）
```bash
python tkinter_scenario_selector.py
```

### 场景选择器功能

场景选择器提供了以下5个场景的快速启动功能：

1. 前向碰撞预警场景
2. 车辆-RSU交互场景
3. 人车加速交互场景
4. 车辆交互场景
5. 添加其他场景

推荐使用Tkinter版本的场景选择器，因为它不需要额外安装依赖库，兼容性更好。



<details><summary><h2>🛣️ Multi-scenarios support</h2></summary>
<p>
  

LimSim supports road scenarios not limited to freeways, signalized intersections, roundabouts, and overpasses.

<p align="center">
 <img src="assets/scenarios.gif" title="" alt="scenarios.gif" data-align="center" width="700">
</p>


</p>
</details>


<details><summary><h2>📊 Scenario Evaluation</h2></summary>
<p>
  

After running a long-term simulation with all kinds of scenarios contained in it, LimSim generates a log report and extracts the key scenarios via the evaluation results.

<p align="center">
 <img src="assets/evaluation.gif" title="" alt="evaluation.gif" data-align="center" width="700">
</p>


</p>
</details>



<details><summary><h2>💡Co-sim with SUMO & CARLA</h2></summary>
<p>

LimSim supports co-simulation with CARLA and SUMO, guaranteeing that all three softwares show identical vehicle status.  Please see [the docs](https://pjlab-adg.github.io/LimSim/zh/GettingStarted/carla_cosim/) for more information.

<p align="center">
 <img src="assets/cosim.gif" title="" alt="cosim.gif" data-align="center" width="700">
</p>


</p>
</details>



## ➕Additional Maps

LimSim supports the `freewayB` and `Expressway_A` maps from the CitySim datasets. However, we have not included these two road network files in this library due to copyright.

To run these two maps, you need to:
1. Go to [CitySim Repo](https://github.com/ozheng1993/UCF-SST-CitySim-Dataset#Full%20Data%20Access) and submit the data access form.
2. Get access to the dataset and download the **`.net.xml` files** in both the `freewayB` and `Expressway_A` data folders.
3. Copy the road network files (.net.xml) to the relevant `networkFiles/CitySim` folder and ensure that your file paths are as follows:
   ```
   networkFiles/CitySim/freewayB/freewayB.net.xml
   networkFiles/CitySim/Expressway_A/Expressway_A.net.xml
   ```

## Acknowledgments

We would like to thank the authors and developers of the following projects, this project is built upon these great projects.
- [SUMO (Simulation of Urban MObility)](https://sumo.dlr.de/)
- [CitySim](https://github.com/ozheng1993/UCF-SST-CitySim-Dataset)
- [DearPyGUI](https://dearpygui.readthedocs.io/en/latest/?badge=latest)


## Contact

If you have any suggestions or collaboration about this repo, feel free to create issues/PR or send emails to us (<a href="mailto:wenlicheng@pjlab.org.cn">wenlicheng@pjlab.org.cn</a>).


## Citation
If you use LimSim in your research, please use the following BibTeX entry.
```
@inproceedings{wen2023limsim,
  title={LimSim: A long-term interactive multi-scenario traffic simulator},
  author={Wen, Licheng and Fu, Daocheng and Mao, Song and Cai, Pinlong and Dou, Min and Li, Yikang and Qiao, Yu},
  booktitle={IEEE 26th International Conference on Intelligent Transportation Systems (ITSC)},
  pages={1255--1262},
  year={2023}
}
```

## License

LimSim is released under the [GNU GPL v3.0 license](https://github.com/PJLab-ADG/limsim/blob/master/LICENSE).
