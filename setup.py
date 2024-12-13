from setuptools import setup, find_packages

setup(
    name="geocam",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"geocam.dependencies":['*'],},
    entry_points={
        "console_scripts": [
            "geocam-server=backend.server:main",
        ],
    },
)
