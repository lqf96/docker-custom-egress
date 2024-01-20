from setuptools import setup

setup(
    name="docker_custom_egress",
    version="0.1.0",
    author="Qifan Lu",
    author_email="lqf.1996121@gmail.com",
    description="Apply custom egress policies to built-in Docker networks.",
    packages=[
        "docker_custom_egress"
    ],
    install_requires=[
        "click",
        "requests",
        "requests-unixsocket"
    ],
    entry_points = {
        "console_scripts": [
            "docker-custom-egress = docker_custom_egress.cli:cli"
        ]
    }
)
