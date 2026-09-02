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

SQLITE_DB=created_tickets.db
RESOLVER_DB=resolved_tickets.db
LOG_FILE=ticket_audit.log
```

Never commit `.env`, API keys, tokens, databases, logs, or virtual environments.

## Safe local test

Activate the environment:

```bash
source .venv/bin/activate
```

Run a dry test against one order:

```bash
python main_preprod.py --dry-run --limit 1 --verbose
```

A successful test reports `dry_run=True` and `DRY-RUN would create ticket`. It does not create a live ticket.

## Live ticket creation

The following command creates real TicketFlow tickets:

```bash
python main_preprod.py --force --verbose
```

The SQLite database records created tickets to prevent duplicate processing.

## Resolver safety warning

`resolve_agent_v1.py` can modify GlobalCart orders and close or resolve TicketFlow tickets.

The resolver is not currently approved for unattended scheduling because:

- TicketFlow comment and closure payloads need correction.
- Unsupported order status values may be proposed.
- Unrelated test tickets may be processed.
- A ticket may be marked resolved even when a preceding operation fails.
- Manual-review cases must not be marked resolved automatically.

Do not enable `globalcart-resolver.timer` until these issues are corrected and tested with selected ticket IDs.

## Production server layout

The recommended Ubuntu layout is:

```text
/opt/globalcart/app    Application source
/opt/globalcart/data   SQLite runtime databases
/opt/globalcart/logs   Application and audit logs
/opt/globalcart/venv   Python virtual environment
/etc/globalcart/env    Protected production configuration
```

## Production installation

Install the required Ubuntu packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

Create the service account and directories:

```bash
sudo adduser --system --group --home /opt/globalcart --no-create-home globalcart
sudo mkdir -p /opt/globalcart/{app,data,logs,venv}
sudo chown -R globalcart:globalcart /opt/globalcart/data /opt/globalcart/logs
sudo chmod 750 /opt/globalcart/data /opt/globalcart/logs
```

Copy the Python files and `requirements.txt` into `/opt/globalcart/app`.

Create the virtual environment:

```bash
python3 -m venv /opt/globalcart/venv
sudo /opt/globalcart/venv/bin/python -m pip install --upgrade pip
sudo /opt/globalcart/venv/bin/python -m pip install -r /opt/globalcart/app/requirements.txt
```

## Production configuration

Copy `deploy/globalcart.env.example` to `/etc/globalcart/env` and fill in the real values directly on the server:

```bash
sudo mkdir -p /etc/globalcart
sudo cp deploy/globalcart.env.example /etc/globalcart/env
sudo nano /etc/globalcart/env
sudo chown root:globalcart /etc/globalcart/env
sudo chmod 640 /etc/globalcart/env
```

Never commit the populated production file.

## Install systemd definitions

Copy the service and timer files:

```bash
sudo cp deploy/globalcart-ticket-creation.service /etc/systemd/system/
sudo cp deploy/globalcart-ticket-creation.timer /etc/systemd/system/
sudo cp deploy/globalcart-resolver.service /etc/systemd/system/
sudo cp deploy/globalcart-resolver.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

Set the production timezone:

```bash
sudo timedatectl set-timezone Asia/Kolkata
```

Validate the definitions:

```bash
sudo systemd-analyze verify /etc/systemd/system/globalcart-*
```

## Enable ticket creation

Test the service manually first:

```bash
sudo systemctl start globalcart-ticket-creation.service
sudo systemctl status globalcart-ticket-creation.service --no-pager --full
```

Enable the daily 21:00 IST timer:

```bash
sudo systemctl enable --now globalcart-ticket-creation.timer
```

Keep the resolver timer disabled:

```bash
sudo systemctl disable --now globalcart-resolver.timer
```

## Monitoring

Check the schedule:

```bash
systemctl list-timers --all | grep globalcart
```

Inspect service and application logs:

```bash
sudo journalctl -u globalcart-ticket-creation.service --since today --no-pager
sudo tail -n 50 /opt/globalcart/logs/ticket_creation_service.log
sudo tail -n 50 /opt/globalcart/logs/ticket_audit.log
```

## Security

- Never run the agents as root.
- Store production secrets in `/etc/globalcart/env`.
- Use the dedicated `globalcart` service account.
- Restrict the secrets file to mode `0640`.
- Never commit `.env`, `.venv`, databases, or logs.
- Rotate any credential accidentally committed or shared.
- Keep Ubuntu and Python dependencies updated.
