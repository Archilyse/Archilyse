#!/usr/bin/env python
from slam_api.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
