import asyncio
import httpx
import json
from datetime import datetime

# This script simulates a real failure scenario:
# Step 1: RDBMS outage — sends 150 signals for database failure
# Step 2: MCP Host failure — sends 50 signals for MCP failure
# Step 3: Cache degradation — sends 30 signals for cache issue

BASE_URL = "http://localhost:8000/api/v1"

async def send_signal(client, component_id, component_type, error_code, message):
    """Send one signal to the IMS backend"""
    signal = {
        "component_id": component_id,
        "component_type": component_type,
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {"simulated": True, "script": "mock_failure.py"}
    }
    try:
        response = await client.post(f"{BASE_URL}/signals", json=signal)
        return response.status_code
    except Exception as e:
        print(f"Error sending signal: {e}")
        return 500

async def simulate_rdbms_outage(client):
    """Simulate RDBMS (PostgreSQL) outage — 150 signals in 10 seconds"""
    print("\n[SCENARIO 1] Simulating RDBMS outage...")
    print("Sending 150 signals for RDBMS_PRIMARY_01...")

    # Send 150 signals — debouncing should create only 1 work item
    tasks = []
    for i in range(150):
        tasks.append(send_signal(
            client,
            component_id="RDBMS_PRIMARY_01",
            component_type="RDBMS",
            error_code="DB_CONNECTION_FAILED",
            message=f"Connection pool exhausted - attempt {i+1}"
        ))

    results = await asyncio.gather(*tasks)
    success = results.count(202)
    print(f"Sent 150 signals — {success} accepted")
    print("Expected: Only 1 Work Item created (debouncing active)")

async def simulate_mcp_failure(client):
    """Simulate MCP Host failure — 50 signals"""
    print("\n[SCENARIO 2] Simulating MCP Host failure...")
    print("Sending 50 signals for MCP_HOST_01...")

    tasks = []
    for i in range(50):
        tasks.append(send_signal(
            client,
            component_id="MCP_HOST_01",
            component_type="MCP_HOST",
            error_code="MCP_TIMEOUT",
            message=f"MCP host not responding - timeout {i+1}"
        ))

    results = await asyncio.gather(*tasks)
    success = results.count(202)
    print(f"Sent 50 signals — {success} accepted")

async def simulate_cache_degradation(client):
    """Simulate cache degradation — 30 signals"""
    print("\n[SCENARIO 3] Simulating Cache degradation...")
    print("Sending 30 signals for CACHE_CLUSTER_01...")

    tasks = []
    for i in range(30):
        tasks.append(send_signal(
            client,
            component_id="CACHE_CLUSTER_01",
            component_type="CACHE",
            error_code="CACHE_MISS_RATE_HIGH",
            message=f"Cache miss rate above threshold - {80 + i}%"
        ))

    results = await asyncio.gather(*tasks)
    success = results.count(202)
    print(f"Sent 30 signals — {success} accepted")

async def simulate_api_errors(client):
    """Simulate API errors — 20 signals"""
    print("\n[SCENARIO 4] Simulating API errors...")
    print("Sending 20 signals for API_GATEWAY_01...")

    tasks = []
    for i in range(20):
        tasks.append(send_signal(
            client,
            component_id="API_GATEWAY_01",
            component_type="API",
            error_code="HTTP_500_SPIKE",
            message=f"500 error rate spike - {5 + i}% errors"
        ))

    results = await asyncio.gather(*tasks)
    success = results.count(202)
    print(f"Sent 20 signals — {success} accepted")

async def check_work_items(client):
    """Check what work items were created"""
    print("\n[CHECKING] Work items created...")
    try:
        response = await client.get(f"{BASE_URL}/workitems")
        items = response.json()
        print(f"Total work items created: {len(items)}")
        for item in items:
            print(f"  - {item['component_id']} | {item['priority']} | {item['status']} | signals: {item['signal_count']}")
    except Exception as e:
        print(f"Error checking work items: {e}")

async def main():
    print("=" * 60)
    print("IMS Mock Failure Simulation")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print("Make sure backend is running on http://localhost:8000")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health first
        try:
            health = await client.get("http://localhost:8000/health")
            print(f"\nBackend health: {health.json()['status']}")
        except Exception:
            print("\nERROR: Backend is not running!")
            print("Run: cd backend && python3 -m uvicorn main:app --reload")
            return

        # Run all 4 scenarios
        await simulate_rdbms_outage(client)
        await asyncio.sleep(2)  # wait 2 seconds between scenarios

        await simulate_mcp_failure(client)
        await asyncio.sleep(2)

        await simulate_cache_degradation(client)
        await asyncio.sleep(2)

        await simulate_api_errors(client)
        await asyncio.sleep(3)  # wait for consumer to process

        # Show results
        await check_work_items(client)

        print("\n" + "=" * 60)
        print("Simulation complete!")
        print("Open http://localhost:5173 to see incidents on dashboard")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
