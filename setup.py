from setuptools import setup

setup(
    packages = ["geocam", "geocam.dependencies"],
    package_dir={"": "src"},
    package_data={"geocam.dependencies":['*'],},
)
