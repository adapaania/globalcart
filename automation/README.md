# GlobalCart Automation

Python agents that:

1. Create TicketFlow tickets from GlobalCart order diagnostics.
2. Attempt to resolve eligible tickets and repair corresponding orders.

## Requirements

- Python 3.10 or newer
- Access to the GlobalCart and TicketFlow APIs
- A RouteLLM/OpenAI-compatible API key

## Local setup

```bash
cd automation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
