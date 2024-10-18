import json
import struct
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(kw_only=True)
class Base:
    id: str = ""
    offset: int = 0

    def __bytes__(self):
        return b"none"

    def __len__(self):
        return len(bytes(self))


@dataclass
class DataEntry(Base):
    data: List

    def __bytes__(self):
        s = json.dumps(self.data)
        return s.encode("utf-8")


@dataclass
class LookupEntry(Base):
    letter: str
    next_table_words: int = 0
    next_table_offset: int = 0
    next_table_size: int = 0

    def __bytes__(self):
        return self.letter.encode("utf-8") + struct.pack(">III", self.next_table_words, self.next_table_offset, self.next_table_size)

    def __len__(self):
        return len(bytes(self))


@dataclass
class LookupTable(Base):
    data_offset: int = 0
    data_length: int = 0

    total_words: int = 0

    entries: List[LookupEntry] = field(default_factory=list)

    def __bytes__(self):
        result = struct.pack(">II", self.data_offset, self.data_length)

        for e in self.entries:
            result += bytes(e)

        return result


@dataclass
class Vocabulary:
    first_table_size: int = 0
    lookup: List[LookupTable] = field(default_factory=list)
    data: List[DataEntry] = field(default_factory=list)

    MAX_WORDS_PER_DATA = 40

    ORIGINAL_KEY = "en"
    TRANSLATED_KEY = "ru"
    TRANSCRIPTION_KEY = "tr"

    def __bytes__(self):
        result = struct.pack(">I", self.first_table_size)
        for e in self.lookup:
            result += bytes(e)

        for e in self.data:
            result += bytes(e)

        return result

    def _build(self, data: Dict, id_=""):
        keys = list(data.keys())
        keys.sort()

        table = LookupTable(id=id_, total_words=data["#"])
        table_index = len(self.lookup)
        self.lookup.append(table)

        for k in keys:
            if k in [".", "?", "#"]:
                continue

            entry = LookupEntry(id=f"{id_}{k}", letter=k)
            table.entries.append(entry)

        if "." in keys:
            self.data.append(
                DataEntry(
                    id=id_,
                    data=data["."]
                )
            )

        for entry in table.entries:
            self._build(data[entry.letter], f"{id_}{entry.letter}")

        return table_index

    def build(self, data: Dict) -> "Vocabulary":
        self._build(data)
        self.first_table_size = len(self.lookup[0])

        for entry in self.data:
            entry.data.sort(key=lambda x: x["i"])

        base_offset = 4
        for table in self.lookup:
            table.offset = base_offset
            base_offset += len(table)

        for entry in self.data:
            entry.offset = base_offset
            base_offset += len(entry)

        for table in self.lookup:
            for entry in table.entries:
                for next_table in self.lookup:
                    if entry.id == next_table.id:
                        entry.next_table_offset = next_table.offset
                        entry.next_table_size = len(next_table)
                        entry.next_table_words = next_table.total_words

            for entry in self.data:
                if entry.id == table.id:
                    table.data_offset = entry.offset
                    table.data_length = len(entry)

        return self

with open("../raw/raw.json", encoding="utf-8") as f:
    raw = json.load(f)

raw_cleared = dict()
for line in raw:
    if line[Vocabulary.ORIGINAL_KEY] in raw_cleared:
        print(f"word '{line}' conflicts with {raw_cleared[line[Vocabulary.ORIGINAL_KEY]]}")

    raw_cleared[line[Vocabulary.ORIGINAL_KEY]] = line

raw = []
for val in raw_cleared.values():
    raw.append({
        "i": val[Vocabulary.ORIGINAL_KEY],
        "o": val[Vocabulary.TRANSLATED_KEY],
        "s": val[Vocabulary.TRANSCRIPTION_KEY],
    })

tree = dict()

def _build_tree(words: List, root: Dict, level: int = 0):
    root["#"] = len(words) + len(root.get(".", []))

    if len(words) < Vocabulary.MAX_WORDS_PER_DATA:
        if "." not in root:
            root["."] = list
        root["."].extend(words)
        return

    for wd in words:
        w = wd["i"].lower()
        # print(f"{level} -> {w}")
        letter = w[level]

        if letter not in root:
            root[letter] = dict()

        if "." not in root[letter]:
            root[letter]["."] = list()

        if "?" not in root[letter]:
            root[letter]["?"] = list()

        if len(w) == level + 1:
            root[letter]["."].append(wd)
        else:
            root[letter]["?"].append(wd)

    for letter, leaf in root.items():
        if letter in [".", "?", "#"]:
            continue

        # leaf["#"] = len(leaf["?"]) + len(leaf["."])
        _build_tree(leaf["?"], leaf, level + 1)
        del leaf["?"]

_build_tree(raw, tree, 0)


v = Vocabulary().build(tree)

with open("../src/common/data/ENG-RU.txt", "wb") as f:
    f.write(bytes(v))