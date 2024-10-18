import json

with open("../src/common/data/ENG-RU.txt", "rb") as f:
    raw = f.read()

def read_bytes(position: int, length: int) -> bytes:
    return raw[position : position + length]

def read_int32(position):
    result = read_bytes(position, 4)
    return int.from_bytes(result, byteorder="big")

def print_table(data: bytes):
    data_offset = int.from_bytes(data[0: 4], byteorder="big")
    data_length = int.from_bytes(data[4: 8], byteorder="big")

    if data_length:
        print(f"Data segment found! Offset: {data_offset}, Length: {data_length}")

    i = 8
    while i < len(data):
        start = i
        while data[i] != 0:
            i += 1

        letter = data[start: i]
        print(f"letter: {letter.decode('utf-8')}")

        next_table_words = int.from_bytes(data[i: i + 4], byteorder="big")
        i += 4
        print(f"\tnext_table_words: {next_table_words}")

        next_table_offset = int.from_bytes(data[i: i + 4], byteorder="big")
        i += 4
        print(f"\tnext_table_offset: {next_table_offset}")

        next_table_length = int.from_bytes(data[i: i + 4], byteorder="big")
        i += 4
        print(f"\tnext_table_length: {next_table_length}")

first_table_size = read_int32(0)
print(f"First table size = {first_table_size}")

table = read_bytes(4, first_table_size)
print_table(table)

table = read_bytes(337, 281)
print_table(table)

data = read_bytes(13389, 177)
parsed = json.loads(data.decode("utf-8"))
print(parsed)