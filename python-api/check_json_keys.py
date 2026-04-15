import json

with open("db_record.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(data[0].keys())
print("Keys inside resultado_json:")
if "resultado_json" in data[0]:
    print(data[0]["resultado_json"].keys())
elif "resultado" in data[0]:
    if isinstance(data[0]["resultado"], dict):
        print(data[0]["resultado"].keys())
    else:
        print("resultado is not a dict")
