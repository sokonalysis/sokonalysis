# setup.py
import sys
import os
from setuptools import setup

APP_NAME = "sokonalysis"
VERSION = "3.5.0"
DESCRIPTION = "The Cipher Toolkit Built For All Skill Levels"

if sys.platform == "darwin":
    ICON = "assets/logo.icns"
elif sys.platform == "win32":
    ICON = "assets/logo.ico"
else:
    ICON = "assets/logo.png"

setup(
    name=APP_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Soko James",
    url="https://github.com/sokonalysis/sokonalysis",
    packages=["gui"],
    package_data={
        "gui": ["../assets/*"],
    },
    install_requires=[
        "PySide6>=6.5.0",
    ],
    entry_points={
        "console_scripts": [
            "sokonalysis=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
)