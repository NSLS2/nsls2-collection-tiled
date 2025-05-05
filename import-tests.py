import argparse

parser = argparse.ArgumentParser(description="Test import of various Python packages.")
parser.add_argument(
    "--python-version",
    type=str,
    help="Version of Python to compare the version with.",
)
args = parser.parse_args()

import sys
print(f"{sys.executable = }\n{sys.version = }\n{sys.version_info = }")

version_str = '.'.join([str(x) for x in sys.version_info[0:2]])
assert args.python_version == version_str, f"Python version mismatch: {args.python_version} != {version_str}"

import event_model
print(f"{event_model.__version__ = }")

import bluesky
print(f"{bluesky.__version__ = }")

import ophyd
print(f"{ophyd.__version__ = }")

import ophyd_async
print(f"{ophyd_async.__version__ = }")

import databroker
print(f"{databroker.__version__ = }")

import tiled
print(f"{tiled.__version__ = }")

import nslsii
print(f"{nslsii.__version__ = }")

import numexpr
print(f"{numexpr.__version__ = }")

import larch
import larch.xrd
print(f"{larch.__version__ = }")
