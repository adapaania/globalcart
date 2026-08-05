# TicketFlow Deployment Info

## Live URL
https://ticketflow-production-1ea7.up.railway.app

## API Token (Bearer Auth)
**Environment variable:** `TICKETFLOW_API_TOKEN`  
**Value:** `1LXhUonIMQM_WrrWsO5McZCk5_Ahq4UcYDqPDj-cihg`

⚠️ **Keep this token secure.** It grants full access to all TicketFlow write operations (create, update, comment, close tickets).

## Quick verification
```bash
TOKEN=1LXhUonIMQM_WrrWsO5McZCk5_Ahq4UcYDqPDj-cihg
BASE=https://ticketflow-production-1ea7.up.railway.app

# Health check (no auth)
curl $BASE/health

# Create a ticket
curl -X POST $BASE/tickets -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test ticket","description":"Testing the API","priority":"medium","created_by":"test"}'
```

## Railway project
- **Project:** ticketflow
- **Project ID:** 67a34a45-5ebf-487e-8603-22df383f7468
- **Service:** ticketflow
- **Region:** sfo (San Francisco)

## Database
SQLite file stored in the container's ephemeral filesystem. Data resets on each redeploy (this is expected for the demo/simulation).

To persist data across deploys, attach a Railway volume or switch to PostgreSQL.

## Deployment commands (from `apps/ticketflow/backend/`)
```bash
# Link to the project
railway link

# Set environment variables
railway variables set TICKETFLOW_API_TOKEN="<your-token>"

# Deploy
railway up
```
