import re
import subprocess
import argparse
import platform
import os
import aes128
from base64 import b64decode

argParser = argparse.ArgumentParser()
argParser.add_argument("-f", "--firmware", help="firmware folder")
args = argParser.parse_args()
firmware = "%s" % args.firmware

def decrypt(key, decryption_key):
	crypto = aes128.AESECB(decryption_key)
	return crypto.decrypt(key)

def encrypt(key, encryption_key):
	crypto = aes128.AESECB(encryption_key)
	return crypto.encrypt(key)

if firmware == "None":
    firmware = "firmware"

if platform.system() == "Windows":
    if subprocess.getstatusoutput("hactoolnet"):
        hactoolnet = "hactoolnet"
        hshell = False
    else:
        hactoolnet = "tools/hactoolnet-windows.exe"
        hshell = False
elif platform.system() == "Linux":
    if subprocess.getstatusoutput("hactoolnet"):
        hactoolnet = "hactoolnet"
        hshell = True
    else:
        hactoolnet = "tools/hactoolnet-linux"
        hshell = True
elif platform.system() == "MacOS":
    if subprocess.getstatusoutput("hactoolnet"):
        hactoolnet = "hactoolnet"
        hshell = True
    else:
        hactoolnet = "tools/hactoolnet-macos"
        hshell = True
else:
    print(f"Unknown Platform: {platform.system()}, proide your own hactoolnet, falling back to backup keygen")
    hactoolnet = False

mariko_kek                          = bytes([0x41, 0x30, 0xB8, 0xB8, 0x42, 0xDD, 0x7C, 0xD2, 0xEA, 0x8F, 0xD5, 0x0D, 0x3D, 0x48, 0xB7, 0x7C])
mariko_bek                          = bytes([0x6A, 0x5D, 0x16, 0x8B, 0x14, 0xE6, 0x4C, 0xAD, 0xD7, 0x0D, 0xA9, 0x34, 0xA0, 0x6C, 0xC2, 0x22])
master_key_source                   = bytes([0xD8, 0xA2, 0x41, 0x0A, 0xC6, 0xC5, 0x90, 0x01, 0xC6, 0x1D, 0x6A, 0x26, 0x7C, 0x51, 0x3F, 0x3C]) # https://github.com/Atmosphere-NX/Atmosphere/blob/master/fusee/program/source/fusee_key_derivation.cpp#L44


# master key sources
Master_Key_Sources = [
	#bytes([0x0C, 0xF0, 0x59, 0xAC, 0x85, 0xF6, 0x26, 0x65, 0xE1, 0xE9, 0x19, 0x55, 0xE6, 0xF2, 0x67, 0x3D]), # /* Zeroes encrypted with Master Key 00. */
	bytes([0x29, 0x4C, 0x04, 0xC8, 0xEB, 0x10, 0xED, 0x9D, 0x51, 0x64, 0x97, 0xFB, 0xF3, 0x4D, 0x50, 0xDD]), # /* Master key 00 encrypted with Master key 01. */
	bytes([0xDE, 0xCF, 0xEB, 0xEB, 0x10, 0xAE, 0x74, 0xD8, 0xAD, 0x7C, 0xF4, 0x9E, 0x62, 0xE0, 0xE8, 0x72]), # /* Master key 01 encrypted with Master key 02. */
	bytes([0x0A, 0x0D, 0xDF, 0x34, 0x22, 0x06, 0x6C, 0xA4, 0xE6, 0xB1, 0xEC, 0x71, 0x85, 0xCA, 0x4E, 0x07]), # /* Master key 02 encrypted with Master key 03. */
	bytes([0x6E, 0x7D, 0x2D, 0xC3, 0x0F, 0x59, 0xC8, 0xFA, 0x87, 0xA8, 0x2E, 0xD5, 0x89, 0x5E, 0xF3, 0xE9]), # /* Master key 03 encrypted with Master key 04. */
	bytes([0xEB, 0xF5, 0x6F, 0x83, 0x61, 0x9E, 0xF8, 0xFA, 0xE0, 0x87, 0xD7, 0xA1, 0x4E, 0x25, 0x36, 0xEE]), # /* Master key 04 encrypted with Master key 05. */
	bytes([0x1E, 0x1E, 0x22, 0xC0, 0x5A, 0x33, 0x3C, 0xB9, 0x0B, 0xA9, 0x03, 0x04, 0xBA, 0xDB, 0x07, 0x57]), # /* Master key 05 encrypted with Master key 06. */
	bytes([0xA4, 0xD4, 0x52, 0x6F, 0xD1, 0xE4, 0x36, 0xAA, 0x9F, 0xCB, 0x61, 0x27, 0x1C, 0x67, 0x65, 0x1F]), # /* Master key 06 encrypted with Master key 07. */
	bytes([0xEA, 0x60, 0xB3, 0xEA, 0xCE, 0x8F, 0x24, 0x46, 0x7D, 0x33, 0x9C, 0xD1, 0xBC, 0x24, 0x98, 0x29]), # /* Master key 07 encrypted with Master key 08. */
	bytes([0x4D, 0xD9, 0x98, 0x42, 0x45, 0x0D, 0xB1, 0x3C, 0x52, 0x0C, 0x9A, 0x44, 0xBB, 0xAD, 0xAF, 0x80]), # /* Master key 08 encrypted with Master key 09. */
	bytes([0xB8, 0x96, 0x9E, 0x4A, 0x00, 0x0D, 0xD6, 0x28, 0xB3, 0xD1, 0xDB, 0x68, 0x5F, 0xFB, 0xE1, 0x2A]), # /* Master key 09 encrypted with Master key 0A. */
	bytes([0xC1, 0x8D, 0x16, 0xBB, 0x2A, 0xE4, 0x1D, 0xD4, 0xC2, 0xC1, 0xB6, 0x40, 0x94, 0x35, 0x63, 0x98]), # /* Master key 0A encrypted with Master key 0B. */
	bytes([0xA3, 0x24, 0x65, 0x75, 0xEA, 0xCC, 0x6E, 0x8D, 0xFB, 0x5A, 0x16, 0x50, 0x74, 0xD2, 0x15, 0x06]), # /* Master key 0B encrypted with Master key 0C. */
	bytes([0x83, 0x67, 0xAF, 0x01, 0xCF, 0x93, 0xA1, 0xAB, 0x80, 0x45, 0xF7, 0x3F, 0x72, 0xFD, 0x3B, 0x38]), # /* Master key 0C encrypted with Master key 0D. */
	bytes([0xB1, 0x81, 0xA6, 0x0D, 0x72, 0xC7, 0xEE, 0x15, 0x21, 0xF3, 0xC0, 0xB5, 0x6B, 0x61, 0x6D, 0xE7]), # /* Master key 0D encrypted with Master key 0E. */
	bytes([0xAF, 0x11, 0x4C, 0x67, 0x17, 0x7A, 0x52, 0x43, 0xF7, 0x70, 0x2F, 0xC7, 0xEF, 0x81, 0x72, 0x16]), # /* Master key 0E encrypted with Master key 0F. */
	bytes([0x25, 0x12, 0x8B, 0xCB, 0xB5, 0x46, 0xA1, 0xF8, 0xE0, 0x52, 0x15, 0xB7, 0x0B, 0x57, 0x00, 0xBD]), # /* Master key 0F encrypted with Master key 10. */
	bytes([0x58, 0x15, 0xD2, 0xF6, 0x8A, 0xE8, 0x19, 0xAB, 0xFB, 0x2D, 0x52, 0x9D, 0xE7, 0x55, 0xF3, 0x93]), # /* Master key 10 encrypted with Master key 11. */
	bytes([0x4A, 0x01, 0x3B, 0xC7, 0x44, 0x6E, 0x45, 0xBD, 0xE6, 0x5E, 0x2B, 0xEC, 0x07, 0x37, 0x52, 0x86]), # /* Master key 11 encrypted with Master key 12. */
]
# ^ todo: add latest master_key_sources from https://github.com/Atmosphere-NX/Atmosphere/blob/master/fusee/program/source/fusee_key_derivation.cpp#L116-L136

mariko_master_kek_sources = [
	bytes([0x77, 0x60, 0x5A, 0xD2, 0xEE, 0x6E, 0xF8, 0x3C, 0x3F, 0x72, 0xE2, 0x59, 0x9D, 0xAC, 0x5E, 0x56]),
	bytes([0x1E, 0x80, 0xB8, 0x17, 0x3E, 0xC0, 0x60, 0xAA, 0x11, 0xBE, 0x1A, 0x4A, 0xA6, 0x6F, 0xE4, 0xAE]),
	bytes([0x94, 0x08, 0x67, 0xBD, 0x0A, 0x00, 0x38, 0x84, 0x11, 0xD3, 0x1A, 0xDB, 0xDD, 0x8D, 0xF1, 0x8A]),
	bytes([0x5C, 0x24, 0xE3, 0xB8, 0xB4, 0xF7, 0x00, 0xC2, 0x3C, 0xFD, 0x0A, 0xCE, 0x13, 0xC3, 0xDC, 0x23]),
	bytes([0x86, 0x69, 0xF0, 0x09, 0x87, 0xC8, 0x05, 0xAE, 0xB5, 0x7B, 0x48, 0x74, 0xDE, 0x62, 0xA6, 0x13]),
	bytes([0x0E, 0x44, 0x0C, 0xED, 0xB4, 0x36, 0xC0, 0x3F, 0xAA, 0x1D, 0xAE, 0xBF, 0x62, 0xB1, 0x09, 0x82]),
	bytes([0xE5, 0x41, 0xAC, 0xEC, 0xD1, 0xA7, 0xD1, 0xAB, 0xED, 0x03, 0x77, 0xF1, 0x27, 0xCA, 0xF8, 0xF1]),
	bytes([0x52, 0x71, 0x9B, 0xDF, 0xA7, 0x8B, 0x61, 0xD8, 0xD5, 0x85, 0x11, 0xE4, 0x8E, 0x4F, 0x74, 0xC6]),
	bytes([0xD2, 0x68, 0xC6, 0x53, 0x9D, 0x94, 0xF9, 0xA8, 0xA5, 0xA8, 0xA7, 0xC8, 0x8F, 0x53, 0x4B, 0x7A]),
	bytes([0xEC, 0x61, 0xBC, 0x82, 0x1E, 0x0F, 0x5A, 0xC3, 0x2B, 0x64, 0x3F, 0x9D, 0xD6, 0x19, 0x22, 0x2D]),
	bytes([0xA5, 0xEC, 0x16, 0x39, 0x1A, 0x30, 0x16, 0x08, 0x2E, 0xCF, 0x09, 0x6F, 0x5E, 0x7C, 0xEE, 0xA9]),
	bytes([0x8D, 0xEE, 0x9E, 0x11, 0x36, 0x3A, 0x9B, 0x0A, 0x6A, 0xC7, 0xBB, 0xE9, 0xD1, 0x03, 0xF7, 0x80]),
	bytes([0x4F, 0x41, 0x3C, 0x3B, 0xFB, 0x6A, 0x01, 0x2A, 0x68, 0x9F, 0x83, 0xE9, 0x53, 0xBD, 0x16, 0xD2]),
	bytes([0x31, 0xBE, 0x25, 0xFB, 0xDB, 0xB4, 0xEE, 0x49, 0x5C, 0x77, 0x05, 0xC2, 0x36, 0x9F, 0x34, 0x80])
]
# ^ todo: add latest mariko_master_kek_source from https://github.com/Atmosphere-NX/Atmosphere/blob/master/fusee/program/source/fusee_key_derivation.cpp#L26
with open('temp.keys', 'w') as temp_keys:
    temp_keys.write(f'mariko_kek = {mariko_kek.hex().upper()}\n')
    temp_keys.write(f'mariko_bek = {mariko_bek.hex().upper()}\n')
    temp_keys.write(f'master_key_source = {master_key_source.hex().upper()}\n')

    master_keks = [decrypt(i, mariko_kek) for i in mariko_master_kek_sources]
    count = 0x4
    for i in master_keks:
        count = count + 0x1
        keys = f'master_kek_{hex(count)[2:].zfill(2)} = '  + (i.hex().upper())
        temp_keys.write(f'{keys}\n')

    # generate master_key_%% from all provided master_kek_%% using master_key_source
    current_master_key = decrypt(master_key_source, master_keks[-1])

    current_master_key_revision = len(Master_Key_Sources)
    master_keys = []
    first = True
    for i in reversed(Master_Key_Sources):
        if first:
            first = False
            previous_key = i
            next_master_key = decrypt(previous_key, current_master_key)
            current_master_key_revision = current_master_key_revision -1
            master_keys.append(current_master_key)
            master_keys.append(next_master_key)
        else:
            key = previous_key
            previous_key = i
            next_master_key = decrypt(previous_key, next_master_key)
            current_master_key_revision = current_master_key_revision -1
            master_keys.append(next_master_key)

	# Write master_key_%%
    count = -0x1
    for i in reversed(master_keys):
        count = count + 0x1
        keys = f'master_key_{hex(count)[2:].zfill(2)} = '  + (i.hex().upper())
        temp_keys.write(f'{keys}\n')

    temp_keys.close()
    subprocess.run(f'{hactoolnet} --keyset temp.keys -t switchfs {firmware} --title 0100000000000819 --romfsdir {firmware}/0100000000000819/romfs/', shell = hshell, stdout = subprocess.DEVNULL)
    subprocess.run(f'{hactoolnet} --keyset temp.keys -t pk11 {firmware}/0100000000000819/romfs/a/package1 --outdir {firmware}/0100000000000819/romfs/a/pkg1', shell = hshell, stdout = subprocess.DEVNULL)
    with open(f'{firmware}/0100000000000819/romfs/a/pkg1/Decrypted.bin', 'rb') as decrypted_bin:
        secmon_data = decrypted_bin.read()
        result = re.search(b'\x4F\x59\x41\x53\x55\x4D\x49', secmon_data)
        byte_alignment = decrypted_bin.seek(result.end() + 0x22)
        mariko_master_kek_source_dev_key = decrypted_bin.read(0x10)
        byte_alignment = decrypted_bin.seek(result.end() + 0x32)
        mariko_master_kek_source_key = decrypted_bin.read(0x10)
        byte_alignment = decrypted_bin.seek(0x150)
        revision = decrypted_bin.read(0x01).hex().upper()
        incremented_revision = int(revision) - 0x1
        if mariko_master_kek_source_key == mariko_master_kek_sources[-1]:
            print(f'mariko_master_kek_source_{incremented_revision} = {mariko_master_kek_source_key.hex().upper()}')
            print(f'master_kek_{incremented_revision} = '  + (master_keks[-1].hex().upper()))
            print(f'master_key_{incremented_revision} = '  + (master_keys[0].hex().upper()))
            print(f'no new master_key_source_vector')
        else:
            print(f'mariko_master_kek_source_{incremented_revision} = {mariko_master_kek_source_key.hex().upper()}')
            formatted_mariko_master_kek_source = '0x' + ', 0x'.join(mariko_master_kek_source_key.hex().upper()[i:i+2] for i in range(0, len(mariko_master_kek_source_key.hex().upper()), 2))
            print(formatted_mariko_master_kek_source)
            print(f'^ add this string to mariko_master_kek_sources array ^')
            new_master_kek = decrypt(mariko_master_kek_source_key, mariko_kek)
            print(f'master_kek_{incremented_revision} = ' + new_master_kek.hex().upper())
            new_master_key =  decrypt(master_key_source, decrypt(mariko_master_kek_source_key, mariko_kek))
            print(f'master_key_{incremented_revision} = '  +   new_master_key.hex().upper())
            new_master_key_source_vector = encrypt(master_keys[0], new_master_key).hex().upper()
            formatted_vector = '0x' + ', 0x'.join(new_master_key_source_vector[i:i+2] for i in range(0, len(new_master_key_source_vector), 2))
            print(f'master_key_source_vector_{incremented_revision} is as follows:')
            print(formatted_vector)
            print(f'^ add this string to master_key_sources array ^')
        decrypted_bin.close()
        os.remove('temp.keys')
        