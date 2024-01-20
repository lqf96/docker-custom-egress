from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from abc import abstractmethod

from .utils import ip, sysctl

if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Sequence

class InboundStrategy(Protocol):
    @classmethod
    def from_config(cls, **kwargs):
        return cls(**kwargs)

    @abstractmethod
    def setup(self):
        raise NotImplementedError

    def teardown(self):
        pass

class OutboundStrategy(Protocol):
    @classmethod
    def from_config(cls, **kwargs):
        return cls(**kwargs)

    @abstractmethod
    def setup(self):
        pass

    def teardown(self):
        pass

class ProxyARPInbound(InboundStrategy):
    def __init__(self, net_iface: str, subnets: list[str]):
        self.net_iface = net_iface
        self.subnets = subnets

    def setup(self):
        # Enable proxy ARP on bridge interface
        sysctl(f"net.ipv4.conf.{self.net_iface}.proxy_arp", "1")

class PolicyRoutingOutbound(OutboundStrategy):
    def __init__(self, net_iface: str, subnets: list[str], routing_table: str):
        self.net_iface = net_iface
        self.subnets = subnets
        self.routing_table = routing_table

    def setup(self, ip_commands: Sequence[str] = ()):
        subnets = self.subnets
        routing_table = self.routing_table

        ip_commands = list(ip_commands)
        # Add local routes for IP ranges
        ip_commands += (
            f"route add {subnet} dev {self.net_iface} scope link table {self.routing_table}" \
            for subnet in subnets
        )
        # Enable policy routing rules for IP ranges
        ip_commands += (f"rule add from {subnet} lookup {routing_table}" for subnet in subnets)
        
        ip(ip_commands)

    def teardown(self, ip_commands: Sequence[str] = ()):
        ip_commands = list(ip_commands)
        # Disable policy routing rules for IP ranges
        ip_commands += (
            f"rule del from {subnet} lookup {self.routing_table}" for subnet in self.subnets
        )
        
        ip(ip_commands)

class SimpleGatewayOutbound(PolicyRoutingOutbound):
    def __init__(self, gateway_iface: str, gateway_ip: str, **kwargs: Any):
        super().__init__(**kwargs)
        
        self.gateway_iface = gateway_iface
        self.gateway_ip = gateway_ip

    def setup(self):
        super().setup((
            # Add route to gateway
            f"route add {self.gateway_ip} dev {self.gateway_iface} table {self.routing_table}",
        ))

    def teardown(self):
        super().teardown((
            # Remove route to gateway
            f"route remove {self.gateway_ip} dev {self.gateway_iface} table {self.routing_table}",
        ))
