from __future__ import annotations

from typing import TYPE_CHECKING

import shutil, subprocess
from importlib import import_module
from tempfile import NamedTemporaryFile
from urllib.parse import quote

import click

__all__ = [
    "DEFAULT_DOCKER_URL",
    "KVPair",
    "get_obj_path",
    "http_request",
    "import_obj",
    "ip",
    "run",
    "sysctl"
]

if TYPE_CHECKING:
    from typing import Any, Optional
    from collections.abc import Sequence

    KVPair = tuple[str, str]

# Default Docker daemon host
DEFAULT_DOCKER_HOST = "unix:///var/run/docker.sock"

UNIX_SOCK_PREFIX = "unix://"
TCP_SOCK_PREFIX = "tcp://"

class KVPairParam(click.ParamType):
    name = "kv_pair"

    def convert(self, value: str, param, ctx) -> KVPair:
        split_value = value.split("=", 1)

        # Set empty value if value is not present
        if len(split_value)==1:
            split_value.append("")
        
        return tuple(split_value)

def convert_docker_host(host: str) -> str:
    # Unix socket
    if host.startswith(UNIX_SOCK_PREFIX):
        return "http+unix://"+quote(host.removeprefix(UNIX_SOCK_PREFIX), safe="")
    # TCP socket
    elif host.startswith(TCP_SOCK_PREFIX):
        return "http://"+host.removeprefix(TCP_SOCK_PREFIX)

def sysctl(key: str, new_value: Optional[str] = None, delimiter: str = "."):
    sysctl_path = "/proc/sys/"+key.replace(delimiter, "/")

    # Read kernel parameter
    if new_value is None:
        with open(sysctl_path) as f_sysctl:
            return f_sysctl.read().strip()
    # Write kernel parameter
    else:
        with open(sysctl_path, "w") as f_sysctl:
            f_sysctl.write(new_value)

def run(program: str, *args: str):
    # Resolve program path
    program = shutil.which(program) or program
    # Run program
    proc = subprocess.run((program,)+args, stdout=sys.stdout, stderr=sys.stderr)
    # Print error and exit early if command fails
    if proc.returncode!=0:
        prompt(f"Error: Command {proc.args} returned with code {proc.returncode}", color_seq=PROMPT_COLOR_RED)
        exit(1)

def ip(commands: Sequence[str]):
    with NamedTemporaryFile("w") as f_ip_cmds:
        # Write network commands into temporary file
        f_ip_cmds.writelines(commands)
        # Execute network commands
        run("ip", "-b", f_ip_cmds.name)

def get_obj_path(obj: Any) -> str:
    return obj.__module__+":"+obj.__qualname__

def import_obj(obj_path: str, default_ns: Any = __builtins__) -> Any:
    split_path = obj_path.split(":")

    # Use default namespace
    if len(split_path)==1:
        obj = default_ns
    # Get module the object belongs to
    elif len(split_path)==2:
        obj = import_module(split_path[0])
    else:
        raise ValueError(f"invalid object path: '{obj_path}'")

    # Get object by local path
    for fragment in split_path[-1].split("."):
        obj = getattr(obj, fragment)
    
    return obj
