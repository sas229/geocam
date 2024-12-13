from setuptools import setup, find_packages

setup(
    packages=find_packages(where="src", include=["geocam*", "geocam.dependencies*"]),
    package_dir={"": "src"},
    package_data={"geocam.dependencies":['*'],},
    entry_points={
        "console_scripts": [
            "run-server=backend.server:main",
        ],
    },
)
