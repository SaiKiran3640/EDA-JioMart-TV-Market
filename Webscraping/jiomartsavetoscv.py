import json
import csv
import pandas as pd
import numpy as np


# Load JSON data
with open("jiomart_tvs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Write to CSV
if data:
    with open("jiomart_tvs.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print("Exported to jiomart_tvs.csv")
else:
    print("No data found in JSON file.")


