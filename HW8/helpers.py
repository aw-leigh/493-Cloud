import constants

#checks content for nonnull and nonblank "name", "type", and "length" attributes
def check_attributes_validity(content, item_type):
    if item_type == constants.boats:
        if "name" not in content or "type" not in content or "length" not in content:
            return -1
    elif item_type == constants.slips:
        if "number" not in content:
            return -1
    return 1