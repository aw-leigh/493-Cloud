import constants
import json

#checks content for nonnull and nonblank "name", "type", and "length" attributes
def check_attributes_validity(content, item_type):
    if item_type == constants.boats:
        if "name" not in content or "type" not in content or "length" not in content:
            return -1
    elif item_type == constants.loads:
        if "weight" not in content or "content" not in content or "delivery_date" not in content:
            return -1
    return 1