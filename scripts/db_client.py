import requests
import json
import sys
import argparse

def query_db(sql, host="http://localhost:8000"):
    url = f"{host}/admin/execute_sql"
    try:
        response = requests.post(url, json={"sql": sql})
        if response.status_code == 200:
            res = response.json()
            if res.get("status") == "success":
                data = res.get("data")
                if data is None:
                    print("Success (No data returned)")
                else:
                    print(f"Rows returned: {len(data)}")
                    for row in data:
                        print(row)
            else:
                print(f"Error from server: {res.get('message')}")
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Is it running on port 8000?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the target app database via API to avoid locking issues.")
    parser.add_argument("sql", nargs="?", help="SQL query to execute", default="SELECT count(*) FROM assignments")
    args = parser.parse_args()
    
    print(f"Executing: {args.sql}")
    query_db(args.sql)
