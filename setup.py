from setuptools import setup, find_packages

setup(
    name="geocam",
    version="0.0.7",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "geocam.dependencies":['*'],
        "server": [
            "frontend/*",
            "frontend/**/*",
            "frontend/**/**/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "geocam-server=server.launcher:run",
        ],
    },
)
