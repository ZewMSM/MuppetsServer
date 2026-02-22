import copy
import zlib
from io import BufferedReader, BufferedWriter
import json


class MSMLocalization:
    local: dict = {}

    def getHash(string: str) -> int:
        encoded_string: bytes = string.encode()
        salt: bytes = 1

        hash: int = zlib.crc32(encoded_string, salt)
        return hash

    def loadFromFile(self, lozalization_file, encoding="utf-8"):
        lozalization_file.read(4)

        length = int.from_bytes(lozalization_file.read(4), 'little')
        some_byte = 8
        text = 8 * (length + 1)

        for _ in range(length):
            lozalization_file.seek(some_byte)
            some_byte = lozalization_file.tell() + 8
            localization_hash = str(int.from_bytes(lozalization_file.read(4), 'little'))
            address = int.from_bytes(lozalization_file.read(4), 'little')

            lozalization_file.seek(text + address)
            localization_text = b''
            byte_index: int = 0
            while True:
                byte_index += 1
                if byte_index > 10000:
                    localization_text = b''
                    break
                byte = lozalization_file.read(1)
                if byte == b'\x00':
                    break
                localization_text += byte
            self.local[int(localization_hash)] = localization_text.decode(encoding)

        lozalization_file.close()
        return self

    def saveToFile(self, localization_file: BufferedWriter, encoding="utf-8"):
        l = len(self.local)

        localization_file.write((1).to_bytes(4, 'little'))
        localization_file.write((l).to_bytes(4, 'little'))

        pos = 0
        for key in self.local.keys():
            value = self.local[key]
            if key < 0:  # Проверка на отрицательные значения
                key += 2 ** 32  # Преобразование отрицательного числа в его беззнаковый эквивалент
            if pos < 0:  # Проверка на отрицательные значения
                pos += 2 ** 32  # Преобразование отрицательного числа в его беззнаковый эквивалент
            localization_file.write(key.to_bytes(4, 'little', signed=False))
            localization_file.write(pos.to_bytes(4, 'little', signed=False))
            pos += len(value.encode('utf-8')) + 2

        for word in self.local.values():
            localization_file.write(word.encode(encoding) + b'\x00\x00')

    def getLocalByHash(self, hash: int) -> str:
        if hash in self.local:
            return self.local[int(hash)]
        return None

    def getLocalByKey(self, key: str) -> str:
        hash = MSMLocalization.getHash(key)
        #
        result = self.getLocalByHash(hash)
        if result is None:
            return key
        return result

    def setLocalByHash(self, hash: int, local: str):
        self.local[int(hash)] = local

    def setLocalByKey(self, key: str, local: str):
        hash = MSMLocalization.getHash(key)
        self.setLocalByHash(hash, local)

    def loadFromJSON(self, json_string: str):
        local = json.loads(json_string)
        for k,v in local.items():
            self.local[int(k)] = v

    def dumpToJSON(self) -> str:
        return json.dumps(self.local, ensure_ascii=False)

    def __len__(self):
        return len(self.local)

    def __add__(self, other):
        new = copy.deepcopy(self)
        for key, value in other.local.items():
            new.local[key] = value

    def __mul__(self, other):
        new = MSMLocalization()
        for key, value in self.local.items():
            if key in other.local:
                new.local[key] = value
        for key, value in other.local.items():
            if key in self.local:
                new.local[key] = value

    def __sub__(self, other):
        new = MSMLocalization()
        for key, value in self.local.items():
            if not key in other.local:
                new.local[key] = value


if __name__ == "__main__":
    with open("cache/en.utf8", "rb") as f:
        localization = MSMLocalization()
        localization.loadFromFile(f, "latin-1")
        open("tt.txt", "w+", encoding="utf8").write(localization.dumpToJSON())
        print(localization.local)
        print(localization.getLocalByKey("ISLAND_5"))
