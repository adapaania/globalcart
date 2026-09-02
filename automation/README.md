# GlobalCart Automation

Python agents that integrate GlobalCart with TicketFlow:

1. `main_preprod.py` creates TicketFlow tickets from GlobalCart orders.
2. `resolve_agent_v1.py` attempts to diagnose tickets and repair corresponding orders.

## Requirements

- Python 3.12 recommended
- GlobalCart API access
- TicketFlow API access
- RouteLLM or another OpenAI-compatible API key

## Local installation

Clone the repository and enter the automation directory:

```bash
git clone https://github.com/adapaania/globalcart.git
cd globalcart/automation
```

Create a Python 3.12 virtual environment on macOS:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Validate the installation:

```bash
python -m pip check
python -m py_compile main_preprod.py resolve_agent_v1.py
```

## Local configuration

Create `automation/.env`:

```ini
ROUTELLM_API_KEY=replace_me
ROUTELLM_BASE=https://routellm.abacus.ai/v1
LLM_MODEL=replace_me
GLOBALCART_BASE=https://globalcart-production.up.railway.app
TICKETFLOW_BASE_URL=replace_me
TICKETFLOW_API_TOKEN=replace_me
