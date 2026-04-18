# MONC Content Generation MCP Server

The MONC Content Generation MCP Server provides a set of callable tools for generating marketing content, validating compliance, and supporting agent-driven workflows. It acts as a lightweight protocol layer that exposes internal logic to agent frameworks.

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/adrianzevenster/content-generation-MCP-server.git
cd content-generation-MCP-server

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Start the MCP server:

```bash
python -m mcp_server
```

Run the local API entry point:

```bash
python api.py
```

## Project Structure

```text
ad_copy_agent/              # Ad and marketing copy generation logic
compliance_agent/           # Compliance validation modules
mcp_server/                 # MCP capability definitions and server logic
agent-content-creation/     # Shared prompting and content utilities
shared/                     # Common utility functions
api.py                      # Local API/testing entry point
requirements.txt
```

## Purpose

This server provides:

- A consistent interface for content-generation tools.  
- Centralized ad-copy and compliance logic.  
- A protocol layer designed to integrate with agents.  
- A simple foundation for extensions such as orchestration or scoring.

## Development Notes

- Keep logic inside the agent modules, not the server layer.  
- Update capability registration when agent interfaces change.  
- Keep the server environment-agnostic.  
- Maintain minimal and documented dependencies.

## Roadmap

- Extend capabilities for full campaign workflows.  
- Add compliance scoring and explanation features.  
- Improve prompting templates and domain-specific logic.  
- Introduce automated test coverage.  
- Add optional deployment configs.

