import file from '@system.file'

export class VocabularyUtils {
    static bytesToInt32(arr, pos=0) {
        //console.log(`b32 ${arr}`)
        return arr[pos+3] | arr[pos+2] << 8 | arr[pos+1] << 16 | arr[pos+0] << 24
    }

    static decodeUtf8(array, outLimit=Infinity, startPosition=0) {
		let out = "";
		let length = array.length;

		let i = startPosition, c, char2, char3;
		while (i < length && out.length < outLimit) {
			c = array[i++];
			switch (c >> 4) {
				case 0:
				case 1:
				case 2:
				case 3:
				case 4:
				case 5:
				case 6:
				case 7:
					// 0xxxxxxx
					out += String.fromCharCode(c);
					break;
				case 12:
				case 13:
					// 110x xxxx   10xx xxxx
					char2 = array[i++];
					out += String.fromCharCode(
						((c & 0x1f) << 6) | (char2 & 0x3f)
					);
					break;
				case 14:
					// 1110 xxxx  10xx xxxx  10xx xxxx
					char2 = array[i++];
					char3 = array[i++];
					out += String.fromCharCode(
						((c & 0x0f) << 12) |
							((char2 & 0x3f) << 6) |
							((char3 & 0x3f) << 0)
					);
					break;
			}
		}

		return out;
	}

    static readFirstSize(filepath, success) {
        file.readArrayBuffer({
            uri: filepath,
            position: 0,
            length: 4,
            success: (data) => {
                success(VocabularyUtils.bytesToInt32(data.buffer))
            },
            fail: (code, data) => {
                console.log(`readFirstSize: ${code} ${data}`)
            },
        })
    }

    static readTable(filepath, offset, length, success) {
        console.log(`readTable ${filepath} ${offset} ${length}`)
        file.readArrayBuffer({
            uri: filepath,
            position: Number(offset),
            length: Number(length),
            success: (data) => {
                let result = {};

                let arr = data.buffer
                let data_offset = VocabularyUtils.bytesToInt32(arr, 0)
                let data_length = VocabularyUtils.bytesToInt32(arr, 4)
                result.tables = []

                let i = 8;
                while(i < length) {
                    let entry = {};
                    let start = i;
                    while(arr[i] != 0) i++

                    entry.letter = VocabularyUtils.decodeUtf8(arr, i - start, start)

                    entry.words = VocabularyUtils.bytesToInt32(arr, i)
                    i += 4

                    entry.next_offset = VocabularyUtils.bytesToInt32(arr, i)
                    i += 4

                    entry.next_length = VocabularyUtils.bytesToInt32(arr, i)
                    i += 4

                    result.tables.push(entry)
                }

                result.words = []
                if(data_offset && data_length) {
                    console.log(`reading data segment ${data_offset} ${data_length}`)
                    file.readArrayBuffer({
                        uri: filepath,
                        position: data_offset,
                        length: data_length,
                        success: (data) => {
                            let str = VocabularyUtils.decodeUtf8(data.buffer)
                            result.words = JSON.parse(str)
                            success(result)
                        },
                        fail: (code, data) => {
                            console.log(`readTable (data): ${code} ${data}`)
                        },
                    })
                } else {
                    success(result)
                }
            },
            fail: (code, data) => {
                console.log(`readTable: ${code} ${data}`)
            },
        })
    }
}