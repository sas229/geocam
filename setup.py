from setuptools import setup, find_packages

setup(
    packages = ["geocam", "geocam.dependencies"],
    package_dir={"": "src"},
    package_data={"geocam.dependencies":['*'],},
    entry_points={
        "console_scripts": [
            "run-server=geocam.backend.server:main",
        ],
    },
)
