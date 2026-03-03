import json

launcher_file_path = "../launcher.json"

def set_launcher_file_value(var: str, val: str):
    with open(launcher_file_path, "r") as f:
        data = json.load(f)
        data[var] = val
    with open(launcher_file_path, "w") as f:
        json.dump(data, f, indent=4)