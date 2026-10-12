"""Topology Pydantic Schemas — Network Control Plane"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class NodeData(BaseModel):
    label: str
    sublabel: Optional[str] = None
    status: Optional[str] = None
    driver: Optional[str] = None
    scope: Optional[str] = None
    environment: Optional[str] = None
    host_id: Optional[str] = None
    ip_address: Optional[str] = None
    subnets: List[Dict[str, Any]] = []
    attributes: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class TopologyNode(BaseModel):
    id: str
    type: str  # hostGroupNode, hostNode, networkNode, containerNode
    data: NodeData
    position: Dict[str, float] = {"x": 0, "y": 0}
    parentNode: Optional[str] = None
    extent: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TopologyEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False
    style: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class TopologyResponse(BaseModel):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]
    stats: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)
