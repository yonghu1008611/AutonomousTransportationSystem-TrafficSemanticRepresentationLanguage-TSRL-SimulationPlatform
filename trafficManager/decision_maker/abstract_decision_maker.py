"""
Author: Licheng Wen
Date: 2022-11-17 15:27:23
Description: 
Copyright (c) 2022 by PJLab, All Rights Reserved. 
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from common.observation import Observation
from common.vehicle import Behaviour, control_Vehicle
from predictor.abstract_predictor import Prediction

from trafficManager.decision_maker import TSRL_decision_maker
from utils.roadgraph import RoadGraph
from utils.trajectory import State


@dataclass
class SingleStepDecision:
    behaviour: Behaviour = None
    expected_time: float = 0
    expected_state: Optional[State] = None
    action: Optional[str] = None


@dataclass
class EgoDecision:
    ego_veh: control_Vehicle
    result: List[SingleStepDecision] = field(default_factory=list)


@dataclass
class MultiDecision:
    results: Dict[control_Vehicle, List[SingleStepDecision]] = field(default_factory=dict)


class AbstractEgoDecisionMaker(ABC):
    @abstractmethod
    def make_decision(
        self,
        observation: Observation,
        road_graph: RoadGraph,
        prediction: Prediction = None,
    ) -> EgoDecision:
        pass


class AbstractMultiDecisionMaker(ABC):
    @abstractmethod
    def make_decision(
        self,
        observation: Observation,
        road_graph: RoadGraph,
        prediction: Prediction = None,
    ) -> MultiDecision:
        pass
