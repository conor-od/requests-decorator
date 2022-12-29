from copy import deepcopy


def deep_concat(original_dict, override_dict):
    new_dict = deepcopy(original_dict)
    for key, override_value in override_dict.items():
        if key in original_dict and isinstance(original_dict[key], list) and isinstance(override_value, list):
            new_dict[key] = original_dict[key] + override_value
        elif key in original_dict and isinstance(original_dict[key], dict) and isinstance(override_value, dict):
            new_dict[key] = deep_concat(original_dict[key], override_value)
        else:
            new_dict[key] = override_value
    return new_dict
