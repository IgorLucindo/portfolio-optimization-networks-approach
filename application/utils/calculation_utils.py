import numpy as np


def round_array(_array, round_number):
    return [round(value, round_number) if isinstance(value, (int, float)) else value for value in _array]


def round_dict(_dict, round_number):
    return {key: round(value, round_number) if isinstance(value, (int, float)) else value for key, value in _dict.items()}