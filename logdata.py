def hex_to_custom_pairs(hex_string, sep=", "):
    hex_chars = "0123456789ABCDEF"
    custom_chars = "<=>?@ABCDEMNOPQR"
    mapping = dict(zip(hex_chars, custom_chars))
    if len(hex_string) % 2 != 0:
        raise ValueError("Hex string must have an even number of characters")
    result = []
    for i in range(0, len(hex_string), 2):
        pair = hex_string[i:i+2].upper()
        converted_pair = mapping[pair[0]] + mapping[pair[1]]
        result.append(converted_pair)
    return sep.join(result)

def bytes_to_custom_pairs(byte_data, sep=", "):
    # Define the mapping
    hex_chars = "0123456789ABCDEF"
    custom_chars = "<=>?@ABCDEMNOPQR"
    mapping = dict(zip(hex_chars, custom_chars))
    result = []
    for byte in byte_data:
        hex_pair = f"{byte:02X}"  # Convert byte to 2-digit uppercase hex
        converted_pair = mapping[hex_pair[0]] + mapping[hex_pair[1]]
        result.append(converted_pair)
    return sep.join(result)


def bytes_to_zHex(byte_data, sep=", "):
    # Define the mapping
    hex_chars = "0123456789ABCDEF"
    custom_chars = "~!@#$%^&*-=_+|<>"
    mapping = dict(zip(hex_chars, custom_chars))
    result = []
    for byte in byte_data:
        hex_pair = f"{byte:02X}"  # Convert byte to 2-digit uppercase hex
        converted_pair = mapping[hex_pair[0]] + mapping[hex_pair[1]]
        result.append(converted_pair)
    return sep.join(result)