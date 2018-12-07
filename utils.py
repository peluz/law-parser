import json


def load_dataset():
    with open("data/dataset.json") as dataset:
        return json.load(dataset)
