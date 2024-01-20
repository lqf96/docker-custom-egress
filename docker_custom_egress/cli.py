from __future__ import annotations

from typing import TYPE_CHECKING

import click

from .network import OPTION_BRIDGE_ICC, create_network, list_networks
from .utils import DEFAULT_DOCKER_HOST

__all__ = [
    "cli"
]

if TYPE_CHECKING:
    from .utils import KVPair

@click.group()
@click.pass_context
@click.option("--host", "-H", envvar="DOCKER_HOST", default=DEFAULT_DOCKER_HOST, help="daemon socket to connect to")
def cli(ctx: click.Context, host: str):
    """ enable and manage custom egress policies for built-in Docker network drivers """
    ctx.obj["docker_host"] = host

@cli.group("daemon")
@click.pass_context
def cli_daemon(ctx: click.Context):
    """ run daemon that applies custom egress policies to networks """
    pass

@cli.group("network")
def cli_network():
    """ manage networks with custom egress policies """
    pass

@cli_network.command("create")
@click.pass_context
@click.option("--inbound", help="inbound routing strategy")
@click.option("--inbound-opt", "inbound_options", type="kv_pair", multiple=True, help="inbound routing strategy options")
@click.option("--ipam-driver", default="default", help="IP Address Management (IPAM) driver")
@click.option("--ipam-opt", "ipam_options", type="kv_pair", multiple=True, help="IPAM driver options")
@click.option("--isolate", is_flag=True, help="isolate communications between containers")
@click.option("--label", "-l", "labels", type="kv_pair", multiple=True, help="metadata on bridge network")
@click.option("--opt", "-o", "options", type="kv_pair", multiple=True, help="bridge network driver options")
@click.option("--outbound", help="outbound routing strategy")
@click.option("--outbound-opt", "outbound_options", type="kv_pair", multiple=True, help="outbound routing strategy options")
@click.option("--subnet", "-s", multiple=True, help="network segment in CIDR format")
@click.argument("name")
def cli_network_create(ctx: click.Context, name: str, inbound: str, inbound_opts: list[KVPair], outbound: str,
    outbound_opts: list[KVPair], ipam_driver: str, ipam_options: list[str], isolate: bool, labels: list[KVPair],
    options: list[KVPair], subnets: list[str]):
    """ create network with custom egress policies """
    options = dict(options)
    # Disable ICC between containers
    if isolate:
        options[OPTION_BRIDGE_ICC] = "false"
    
    # Subnet configurations
    subnets_config = [{"Subnet": subnet} for subnet in subnets]
    # Docker network configuration
    net_config = {
        "Name": name,
        "CheckDuplicate": True,
        "IPAM": {
            "Driver": ipam_driver,
            "Options": dict(ipam_options),
            "Config": subnets_config
        },
        "Options": options,
        "Labels": dict(labels)
    }

    # Create custom egress network
    create_network(
        net_config, inbound, outbound, dict(inbound_opts), dict(outbound_opts), docker_host=ctx.obj["docker_host"]
    )

@cli_network.command("ls")
@click.pass_context
def cli_network_ls(ctx: click.Context):
    """ list all networks with custom egress policies """
    configs = list_networks(docker_host=ctx.obj["docker_host"])

    outputs = f"{'NETWORK ID':<16}NAME\n"
    for config in configs:
        outputs += f"{config['Id'][:12]:<16}{config['Name']}\n"
    
    print(outputs)
