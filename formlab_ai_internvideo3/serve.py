#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
root=Path(__file__).resolve().parent
os.chdir(root)
print("FormLab AI")
print("Open: http://127.0.0.1:8000/FormLab_AI.html")
print("Camera access works on localhost. Deep InternVideo3 is a separate backend on port 8001.")
ThreadingHTTPServer(("127.0.0.1",8000),SimpleHTTPRequestHandler).serve_forever()
