def hide_file_simple(source_filename, res_filename, file_to_hide):
    source_file = open(source_filename, 'rb')
    zip_bytes = bytearray(source_file.read())
    source_file.close()
    val = get_central_directory_idx(zip_bytes)
    start, end = find_central_directory_file_header_with_filename(zip_bytes[val:], bytearray(file_to_hide.encode()))
    zip_bytes[start + val] = 0x00
    res_file = open(res_filename, 'wb')
    res_file.write(zip_bytes)
    res_file.close()
    print(file_to_hide + " was successfully hidden!")


def uncover_file_simple(source_filename, res_filename, file_to_uncover):
    source_file = open(source_filename, 'rb')
    zip_bytes = bytearray(source_file.read())
    source_file.close()
    val = get_central_directory_idx(zip_bytes)
    filename_bytes = bytearray(file_to_uncover.encode())
    filename_beginning = filename_bytes[0]
    filename_bytes[0] = 0x00
    start, end = find_central_directory_file_header_with_filename(zip_bytes[val:], filename_bytes)
    zip_bytes[start + val] = filename_beginning
    res_file = open(res_filename, 'wb')
    res_file.write(zip_bytes)
    res_file.close()
    print(file_to_uncover + " was successfully uncovered!")


def insert_file_to_zip(source_zip, res_zip, file_to_hide_name):
    file_to_hide = open(file_to_hide_name, 'rb')
    file_bytes = bytearray(file_to_hide.read())
    file_to_hide.close()
    zip_file = open(source_zip, "rb")
    zip_bytes = bytearray(zip_file.read())
    zip_file.close()
    val1 = get_central_directory_idx(zip_bytes)
    val2 = get_end_of_central_directory_record(zip_bytes[val1:]) + val1
    filename_bytes = bytearray(file_to_hide_name.encode())
    file_len = len(file_bytes)
    filename_len = len(filename_bytes)
    addition = bytearray(b"PK\x08\x09") + filename_len.to_bytes(2, "little") + filename_bytes + file_len.to_bytes(4, "little") + file_bytes
    offset = zip_bytes[val2+16:val2+20]
    offset_num = int.from_bytes(offset, "little") + len(addition)
    zip_bytes[val2+16:val2+20] = offset_num.to_bytes(4, "little")
    new_zip_bytes = zip_bytes[:val1] + addition + zip_bytes[val1:]
    res_file = open(res_zip, 'wb')
    res_file.write(new_zip_bytes)
    res_file.close()
    print("File was successfully hidden in zip!")


def extract_file_from_zip(source_zip, file_location = ""):
    zip_file = open(source_zip, "rb")
    zip_bytes = bytearray(zip_file.read())
    zip_file.close()
    val = get_hidden_file_idx(zip_bytes) + 4
    filename_length = zip_bytes[val:val+2]
    filename_length_num = int.from_bytes(filename_length, "little")
    filename = zip_bytes[val + 2:val + 2 + filename_length_num]
    val2 = val + 2 + filename_length_num
    file_length = zip_bytes[val2:val2+4]
    file_length_num = int.from_bytes(file_length, "little")
    file_bytes = zip_bytes[val2+4:val2+4+file_length_num]
    extracted_file = open(file_location + filename.decode(), "wb")
    extracted_file.write(file_bytes)
    extracted_file.close()
    print("File was successfully retrieved from zip!")


def remove_file_from_zip(source_zip):
    zip_file = open(source_zip, "rb")
    zip_bytes = bytearray(zip_file.read())
    zip_file.close()
    val = get_hidden_file_idx(zip_bytes)
    filename_length = zip_bytes[val+4:val+6]
    filename_length_num = int.from_bytes(filename_length, "little")
    val2 = val + 6 + filename_length_num
    file_length = zip_bytes[val2:val2+4]
    file_length_num = int.from_bytes(file_length, "little")
    zip_new = zip_bytes[:val] + zip_bytes[val + 10 + file_length_num + file_length_num:]
    extracted_zip = open(source_zip, "wb")
    extracted_zip.write(zip_new)
    extracted_zip.close()
    print("File was successfully retrieved from zip!")


def get_hidden_file_idx(bytes):
    if bytes[0:4] != bytearray(b"PK\x03\x04"):
        raise Exception("Wrong input. Expected to start wiht " + str(b"PK\x03\x04"))
    seek_bytes = bytearray(b"PK\x08\x09")
    val = 0
    while bytes[val:val + 4] != seek_bytes:
        val += get_next_file_header_idx(bytes[val:])
    return val


def find_central_directory_file_header_with_filename(bytes, filename_bytearray):
    val = 0
    beginning = bytearray(b"PK\x01\02")
    while bytes[val:val + 4] == beginning:
        filename_size = int.from_bytes(bytes[28 + val:30 + val], "little")
        filename = bytes[46 + val:46 + val + filename_size]
        end_filename = filename.split(b"/")[-1]
        if end_filename == filename_bytearray:
            return val + 46 + filename_size - len(end_filename), val + 46 + filename_size
        val += get_next_central_directory_file_header(bytes[val:])
    raise Exception("Filename: " + str(filename_bytearray) + "was not found")


def get_end_of_central_directory_record(bytes):
    val = 0
    seek_bytes = bytearray(b"PK\x05\x06")
    while bytes[val:val+4] != seek_bytes:
        val += get_next_central_directory_file_header(bytes[val:])
    return val


def get_next_central_directory_file_header(bytes):
    if bytes[0:4] != bytearray(b"PK\x01\x02"):
        raise Exception("Wrong input. Expected to start wiht " + str(b"PK\x01\x02"))
    filename_size = int.from_bytes(bytes[28:30], "little")
    extra_field_size = int.from_bytes(bytes[30:32], "little")
    comment_size = int.from_bytes(bytes[32:34], "little")
    return 46 + filename_size + extra_field_size + comment_size


def get_central_directory_idx(bytes):
    if bytes[0:4] != bytearray(b"PK\x03\x04"):
        raise Exception("Wrong input. Expected to start wiht " + str(b"PK\x03\x04"))
    seek_bytes = bytearray(b"PK\x01\02")
    val = 0
    while bytes[val:val + 4] != seek_bytes:
        val += get_next_file_header_idx(bytes[val:])
    return val


def get_next_file_header_idx(bytes):
    if bytes[0:4] != bytearray(b"PK\x03\x04"):
        raise Exception("Wrong input. Expected to start wiht " + str(b"PK\x03\x04"))
    compressed_size = int.from_bytes(bytes[18:22], "little")
    filename_size = int.from_bytes(bytes[26:28], "little")
    extra_field_size = int.from_bytes(bytes[28:30], "little")
    return 30 + compressed_size + filename_size + extra_field_size


if __name__ == "__main__":
    #hide_file_simple("folder.zip", "folder2.zip", "to_hide.txt")
    #uncover_file_simple("folder2.zip", "folder3.zip", "to_hide.txt")

    #insert_file_to_zip("folder.zip", "folder2.zip", "bm2000.exe")
    #extract_file_from_zip("folder2.zip", "result/")

    remove_file_from_zip("folder3.zip")
    extract_file_from_zip("folder3.zip", "result/")

