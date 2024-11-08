import json

def load_producer_config(file_path: str = "producer_config.json") -> dict:
    with open(file_path, 'r') as file:
        return json.load(file)

producer_config = load_producer_config()
