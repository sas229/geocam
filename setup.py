from setuptools import setup, find_packages

setup(
    packages = ["geocam", "geocam.dependencies"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"geocam.dependencies":['*'],},
    entry_points={
        "console_scripts": [
            "run-server=backend.server:main",
        ],
    },
)
