#!/bin/bash
# API Testing Script for GlobalCart and TicketFlow
# Usage: bash test-apis.sh

set -e

GLOBALCART_BASE="https://globalcart-production.up.railway.app"
TICKETFLOW_BASE="https://ticketflow-production-1ea7.up.railway.app"
TICKETFLOW_TOKEN="1LXhUonIMQM_WrrWsO5McZCk5_Ahq4UcYDqPDj-cihg"

echo "=========================================="
echo "Testing GlobalCart API"
echo "=========================================="

echo -e "\n1. Health Check:"
curl -s $GLOBALCART_BASE/health | python3 -m json.tool

echo -e "\n2. Get Order GC-1001:"
curl -s $GLOBALCART_BASE/api/orders/GC-1001 | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Order: {d['order_id']} | Status: {d['status']} | Customer: {d['customer_name']}\")"

echo -e "\n3. Get Diagnostics for GC-1042 (stuck order):"
curl -s $GLOBALCART_BASE/api/diagnostics/GC-1042 | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Order: {d['order_id']} | Status: {d['status']} | Logs: {len(d['system_logs'])} | Action: {d['recommended_action']}\")"

echo -e "\n4. Create New Order:"
curl -s -X POST $GLOBALCART_BASE/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Test User","customer_email":"test@example.com","total_amount":99.99,"status":"PROCESSING","payment_status":"PENDING","items":[{"sku":"TEST-1","name":"Test Item","qty":1,"price":99.99}]}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Created: {d['order_id']} | Status: {d['status']}\")"

echo -e "\n=========================================="
echo "Testing TicketFlow API"
echo "=========================================="

echo -e "\n1. Health Check:"
curl -s $TICKETFLOW_BASE/health | python3 -m json.tool

echo -e "\n2. Create Ticket:"
TICKET_ID=$(curl -s -X POST $TICKETFLOW_BASE/tickets \
  -H "Authorization: Bearer $TICKETFLOW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"API Test Ticket","description":"Testing the TicketFlow API","priority":"medium","created_by":"test-script"}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['id'])")
echo "Created ticket ID: $TICKET_ID"

echo -e "\n3. Get Ticket:"
curl -s $TICKETFLOW_BASE/tickets/$TICKET_ID \
  -H "Authorization: Bearer $TICKETFLOW_TOKEN" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Ticket #{d['id']}: {d['title']} | Status: {d['status']} | Priority: {d['priority']}\")"

echo -e "\n4. Update Ticket:"
curl -s -X POST $TICKETFLOW_BASE/tickets/$TICKET_ID/update \
  -H "Authorization: Bearer $TICKETFLOW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress","assigned_to":"test-agent"}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Updated: Status={d['status']}, Assigned={d['assigned_to']}\")"

echo -e "\n5. Add Comment:"
curl -s -X POST $TICKETFLOW_BASE/tickets/$TICKET_ID/comment \
  -H "Authorization: Bearer $TICKETFLOW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"author":"test-agent","body":"This is a test comment from the API test script."}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Comments: {len(d['comments'])}\")"

echo -e "\n6. Search Tickets:"
curl -s "$TICKETFLOW_BASE/tickets/search?q=test" \
  -H "Authorization: Bearer $TICKETFLOW_TOKEN" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Found {d['count']} tickets matching 'test'\")"

echo -e "\n7. List All Tickets:"
curl -s $TICKETFLOW_BASE/tickets \
  -H "Authorization: Bearer $TICKETFLOW_TOKEN" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"Total tickets: {d['count']}\")"

echo -e "\n=========================================="
echo "All API tests completed successfully! ✅"
echo "=========================================="
