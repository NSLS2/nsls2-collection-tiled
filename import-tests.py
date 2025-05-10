import argparse
import sys
import event_model
import bluesky
import ophyd
import ophyd_async
import databroker
import tiled
import nslsii
import numexpr
import larch
import larch.xrd

parser = argparse.ArgumentParser(description="Test import of various Python packages.")
parser.add_argument(
    "--python-version",
    type=str,
    help="Version of Python to compare the version with.",
)
args = parser.parse_args()

print(f"{sys.executable = }\n{sys.version = }\n{sys.version_info = }")

version_str = ".".join([str(x) for x in sys.version_info[0:2]])
assert args.python_version == version_str, (
    f"Python version mismatch: {args.python_version} != {version_str}"
)

print(f"{event_model.__version__ = }")
print(f"{bluesky.__version__ = }")
print(f"{ophyd.__version__ = }")
print(f"{ophyd_async.__version__ = }")
print(f"{databroker.__version__ = }")
print(f"{tiled.__version__ = }")
print(f"{nslsii.__version__ = }")
print(f"{numexpr.__version__ = }")
print(f"{larch.__version__ = }")
