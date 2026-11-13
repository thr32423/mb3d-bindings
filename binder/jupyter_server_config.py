# mybinder.org: the explorer demo, started when its page (.../explorer/) is first opened
import os
import sys

home = os.path.expanduser("~")
c.ServerProxy.servers = {
    "explorer": {
        "command": [sys.executable, os.path.join(home, "demos", "explorer", "server.py"), "{port}"],
        "environment": {"MB3D": os.path.join(home, ".cache", "mb3d-notebook", "mb3d")},
        "timeout": 120,
        "launcher_entry": {"title": "mb3d explorer"},
    }
}
