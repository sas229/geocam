from setuptools import setup

setup(
    packages = ["geocam", "geocam.dependencies", "backend.server"],
    package_dir={"": "src"},
    package_data={"geocam.dependencies":['*'],},
    entry_points={
        "console_scripts": [
            "geocam-server=backend.server:main",
        ],
    },
)
