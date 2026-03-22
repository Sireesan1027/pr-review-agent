"""Entry point for preview server — adds project dir to sys.path then runs uvicorn."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
