import numpy
import json
import os


def get_JSON_File():
    with open(os.path.dirname(__file__) + '/US-data.json') as json_file:
        data = json.load(json_file)
        return data