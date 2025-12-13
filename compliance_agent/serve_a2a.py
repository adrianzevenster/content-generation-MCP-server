# compliance_agent/serve_a2a.py

import asyncio
import os

import uvicorn
from fastapi import FastAPI
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from .agent import build_compliance_agent


def create_app() -> FastAPI:
    agent = build_compliance_agent()
    a2a_app = to_a2a(agent)
    return a2a_app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("compliance_agent.serve_a2a:app", host="0.0.0.0", port=port)
