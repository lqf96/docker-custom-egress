from __future__ import annotations

from typing import TYPE_CHECKING

import json

from requests import Session

from .utils import DEFAULT_DOCKER_HOST, convert_docker_host

__all__ = [
    "OPTION_BRIDGE_ICC",
    "LABEL_CE_ENABLED",
    "LABEL_CE_INBOUND",
    "LABEL_CE_INBOUND_OPT_PREFIX",
    "LABEL_CE_OUTBOUND",
    "LABEL_CE_OUTBOUND_OPT_PREFIX",
    "create_network",
    "list_networks"
]

if TYPE_CHECKING:
    from typing import Optional, TypedDict, Union

    from .routing import InboundStrategy, OutboundStrategy

    from requests import Session

    _Inbound = Union[str, type[InboundStrategy], InboundStrategy]
    _Outbound = Union[str, type[OutboundStrategy], OutboundStrategy]

    class NetworkConfig(TypedDict, total=False):
        Name: str
        Id: str
        Options: dict[str, str]
        Labels: dict[str, str]
    
    __all__ += [
        "NetworkConfig"
    ]

# Bridge driver options
OPTION_BRIDGE_ICC = "com.docker.network.bridge.enable_icc"
OPTION_BRIDGE_SNAT = "com.docker.network.bridge.enable_ip_masquerade"
OPTION_BRIDGE_IFACE = "com.docker.network.bridge.name"
# Custom egress network labels
LABEL_CE_ENABLED = "custom_egress.enabled"
LABEL_CE_INBOUND = "custom_egress.inbound"
LABEL_CE_INBOUND_OPT_PREFIX = "custom_egress.inbound_opts."
LABEL_CE_OUTBOUND = "custom_egress.outbound"
LABEL_CE_OUTBOUND_OPT_PREFIX = "custom_egress.outbound_opts."

# Query parameters for custom egress network
CE_NETWORK_QUERY = {
    "filters": json.dumps({
        "driver": ["bridge"],
        "label": [f"{LABEL_CE_ENABLED}=true"]
    })
}

def create_network(config: NetworkConfig, inbound: _Inbound, outbound: _Outbound, inbound_opts,
    outbound_opts, session: Optional[Session] = None, docker_host: str = DEFAULT_DOCKER_HOST) -> NetworkConfig:
    driver = config.get("Driver")
    # Only bridge networks are supported
    if driver!="bridge":
        raise ValueError(f"custom egress not supported for {driver} network")
    
    options = config.get("Options", {})
    # SNAT not supported for custom egress network
    if options.get(OPTION_BRIDGE_SNAT)=="true":
        raise ValueError(f"custom egress network does not support SNAT")
    options[OPTION_BRIDGE_SNAT] = "false"
    # Derive default interface name for network
    options.setdefault(OPTION_BRIDGE_IFACE, "ce_bridge_"+config["Name"])

    labels = config.setdefault("Labels", {})
    # Add labels for custom egress
    labels.update({
        LABEL_CE_ENABLED: "true",
        LABEL_CE_INBOUND: inbound,
        LABEL_CE_OUTBOUND: outbound
    })
    labels.update((LABEL_CE_INBOUND_OPT_PREFIX+key, value) for key, value in inbound_opts)
    labels.update((LABEL_CE_OUTBOUND_OPT_PREFIX+key, value) for key, value in outbound_opts)

    # Create temporary session for Docker API call
    if session is None:
        session = Session()
    # Create Docker network
    response = session.post(convert_docker_host(docker_host)+"/latest/networks/create", json=config)
    response.raise_for_status()
    return response.json()

def list_networks(session: Optional[Session] = None, docker_host: str = DEFAULT_DOCKER_HOST) -> list[NetworkConfig]:
    # Create temporary session for Docker API call
    if session is None:
        session = Session()
    
    # Get all custom egress bridge networks
    response = session.get(convert_docker_host(docker_host)+"/latest/networks", params=CE_NETWORK_QUERY)
    response.raise_for_status()
    return response.json()
