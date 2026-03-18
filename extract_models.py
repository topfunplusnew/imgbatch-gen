import json

with open("pricing_new.json", "r", encoding="utf-8") as f:
    data = json.load(f)

result = [
    {"model_name": item.get("model_name", ""), "supported_endpoint_types": item.get("supported_endpoint_types", [])}
    for item in data["data"]
]

with open("models_endpoints.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"已输出 {len(result)} 个模型到 models_endpoints.json")
