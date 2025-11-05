# In: C:\Users\fishe\Desktop\CS203-G5T1-AY2025T1\MCP-Server\test\historical_viewer_test.py

import asyncio
import httpx
import json
import logging

logging.basicConfig(level=logging.INFO)

TEST_URL = "http://127.0.0.1:8000/tools/historical_viewer/data"

async def main():
    logging.info(f"--- Running Historical Viewer Test (Direct DB) ---")
    logging.info(f"Attempting to call endpoint at: {TEST_URL}")

    # --- UPDATED: Send integer IDs for countries ---
    # Example: 188 = USA, 33 = Canada (based on your helpers.py)
    params = {
        "reporter_country": 188,  # Example: USA
        "partner_country": 33,   # Example: Canada
        "category": "AD_VALOREM",
        "start_date": "2020-01-01"
    }
    # ------------------------------------------------

    try:
        async with httpx.AsyncClient() as client:
            
            response = await client.get(TEST_URL, params=params)
            
            if response.status_code == 200:
                logging.info("✅ Success! Server responded with 200 OK.")
                
                try:
                    data = response.json()
                    logging.info(f"Received {len(data)} data points.")
                    if data:
                        logging.info("First data point:")
                        print(json.dumps(data[0], indent=2))
                    else:
                        logging.info("Query returned no data (which might be correct).")
                except json.JSONDecodeError:
                    logging.error("❌ Error: Server responded, but it was not valid JSON.")
                    logging.error(f"Response text: {response.text}")
            
            # The 401 error should be gone, but we'll check for others
            else:
                logging.error(f"❌ Test Failed. Server responded with status code: {response.status_code}")
                logging.error(f"Response: {response.text}")

    except httpx.ConnectError:
        logging.error("❌ Test Failed. Could not connect to the server.")
        logging.error("   Is your MCP-Server running on http://127.0.0.1:8000?")
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    print("\n--- Test complete ---")