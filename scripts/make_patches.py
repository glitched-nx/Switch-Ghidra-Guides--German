#!/usr/bin/env python

import re
import subprocess
import shutil
import hashlib
import os
import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument("-l", "--location", help="firmware folder location")
argParser.add_argument("-f", "--firmware", help="firmware version number")
args = argParser.parse_args()
version = "%s" % args.firmware
location = "%s" % args.location

if version == "None":
    version = "NO-VERSION-PROVIDED"

if location == "None":
    location = "firmware"

print("# initiating keygen if needed, or if required root keys exist")
prod_keys = os.path.expanduser('~/.switch/prod.keys')
with open(prod_keys, 'r') as keycheck:
    check_key = keycheck.read()
    if 'mariko_bek' in check_key:
            print("# Checking if latest mariko_master_kek_source is needed from package1 retrieved from BootImagePackage")
            subprocess.run(f'hactoolnet -t switchfs {location} --title 0100000000000819 --romfsdir {location}/titleid/0100000000000819/romfs/', stdout = subprocess.DEVNULL)
            subprocess.run(f'hactoolnet -t pk11 {location}/titleid/0100000000000819/romfs/a/package1 --outdir {location}/titleid/0100000000000819/romfs/a/pkg1', stdout = subprocess.DEVNULL)
            with open(f'{location}/titleid/0100000000000819/romfs/a/pkg1/Decrypted.bin', 'rb') as decrypted_bin:
                secmon_data = decrypted_bin.read()
                result = re.search(b'\x4F\x59\x41\x53\x55\x4D\x49', secmon_data)
                patch = '%06X' % (result.end() + 0x32)
                hekate_bytes = decrypted_bin.seek(result.end() + 0x32)
                mariko_master_kek_source_key = decrypted_bin.read(0x10).hex().upper()
                if mariko_master_kek_source_key in check_key:
                    print(f'Key already exists in prod.keys at {prod_keys}, no need to initiate keygen')
                    keycheck.close()
                else:
                    revision = re.findall(r'mariko_master_kek_source_\w{2}', check_key)
                    incremented_revision = (int(max(revision).split('mariko_master_kek_source_')[1]) + 0x1)
                    mariko_master_kek_source = f'mariko_master_kek_source_{incremented_revision}       = ' + mariko_master_kek_source_key
                    if 'mariko_kek' in check_key:
                        keycheck.close()
                        os.rename(prod_keys, 'temp.keys')
                        with open('temp.keys', 'a') as temp_keys:
                            temp_keys.write(f'\n')
                            temp_keys.write(f'{mariko_master_kek_source}')
                            temp_keys.close()
                            with open(prod_keys, 'w') as new_prod_keys:
                                subprocess.run(f'hactoolnet --keyset "temp.keys" -t keygen', stdout=new_prod_keys)
                                new_prod_keys.close()
                                os.remove('temp.keys')
                                print(f'# Keygen completed and output to {prod_keys}')
                    else:
                        keycheck.close()
                        print('mariko_kek is missing, we cannot derive master keys, keygen will not yield viable keyset.')
    else:
        keycheck.close()
        print('mariko_kek keys not found, cannot proceed with keygen as package1 cannot be opened')
        
        
print('# Extracting ES')
subprocess.run(f'hactoolnet -t switchfs {location} --title 0100000000000033 --exefsdir {location}/titleid/0100000000000033/exefs/', stdout = subprocess.DEVNULL)
shutil.copyfile(f'{location}/titleid/0100000000000033/exefs/main', 'compressed_es.nso0')

print('# Extracting NIFM')
subprocess.run(f'hactoolnet -t switchfs {location} --title 010000000000000f --exefsdir {location}/titleid/010000000000000f/exefs/', stdout = subprocess.DEVNULL)
shutil.copyfile(f'{location}/titleid/010000000000000f/exefs/main', 'compressed_nifm.nso0')

print('# Extracting NIM')
subprocess.run(f'hactoolnet -t switchfs {location} --title 0100000000000025 --exefsdir {location}/titleid/0100000000000025/exefs/', stdout = subprocess.DEVNULL)
shutil.copyfile(f'{location}/titleid/0100000000000025/exefs/main', 'compressed_nim.nso0')

print('# Extracting fat32')
subprocess.run(f'hactoolnet -t switchfs {location} --title 0100000000000819 --romfsdir {location}/titleid/0100000000000819/romfs/', stdout = subprocess.DEVNULL)
subprocess.run(f'hactoolnet -t pk21 {location}/titleid/0100000000000819/romfs/nx/package2 --ini1dir {location}/titleid/0100000000000819/romfs/nx/ini1', stdout = subprocess.DEVNULL)
subprocess.run(f'hactoolnet -t kip1 {location}titleid/0100000000000819/romfs/nx/ini1/FS.kip1 --uncompressed uncompressed_fat32.kip1', stdout = subprocess.DEVNULL)
fat32compressed = 'compressed_fat32.kip1'
shutil.copyfile(f'{location}/titleid/0100000000000819/romfs/nx/ini1/FS.kip1', fat32compressed)

print('# Extracting exfat')
subprocess.run(f'hactoolnet -t switchfs {location} --title 010000000000081b --romfsdir {location}/titleid/010000000000081b/romfs/', stdout = subprocess.DEVNULL)
subprocess.run(f'hactoolnet -t pk21 {location}/titleid/010000000000081b/romfs/nx/package2 --ini1dir {location}/titleid/010000000000081b/romfs/nx/ini1', stdout = subprocess.DEVNULL)
subprocess.run(f'hactoolnet -t kip1 {location}/titleid/010000000000081b/romfs/nx/ini1/FS.kip1 --uncompressed uncompressed_exfat.kip1', stdout = subprocess.DEVNULL)
exfatcompressed = 'compressed_exfat.kip1'
shutil.copyfile(f'{location}/titleid/010000000000081b/romfs/nx/ini1/FS.kip1', exfatcompressed)


escompressed = f'compressed_es.nso0'
nifmcompressed = f'compressed_nifm.nso0'
nimcompressed = f'compressed_nim.nso0'
exfatuncompressed = f'uncompressed_exfat.kip1'
fat32uncompressed = f'uncompressed_fat32.kip1'
exfatcompressed = f'compressed_exfat.kip1'
fat32compressed = f'compressed_fat32.kip1'

def get_es_build_id():
    with open(escompressed, 'rb') as f:
        f.seek(0x40)
        return f.read(0x14).hex().upper()

def get_nifm_build_id():
    with open(nifmcompressed, 'rb') as f:
        f.seek(0x40)
        return f.read(0x14).hex().upper()
        
def get_nim_build_id():
    with open(nimcompressed, 'rb') as f:
        f.seek(0x40)
        return f.read(0x14).hex().upper()

print(f'\n===== Printing relevant hashes and buildids for {version}  =====')
print('es build-id:', get_es_build_id())
print('nifm build-id:', get_nifm_build_id())
print('nim build-id:', get_nim_build_id())
print('fat32 sha256:', hashlib.sha256(open(fat32compressed, 'rb').read()).hexdigest().upper())
print('exfat sha256:', hashlib.sha256(open(exfatcompressed, 'rb').read()).hexdigest().upper())

print(f'\n===== Making patches for {version} =====')
changelog = open(f'./patch_changelog.txt', 'w')
changelog.write(f'Patch changelog for {version}:\n\n')

esbuildid = get_es_build_id()
es_patch = f'{esbuildid}.ips'
if es_patch in os.listdir('patches/atmosphere/exefs_patches/es_patches'):
    changelog.write(f'ES related patch changelog for {version}:\n')
    changelog.write(f'ES patch for version {version} already exists as an .ips patch, and the build id is: {esbuildid}\n\n')
else:
    subprocess.run('hactool -t nso0 compressed_es.nso0 --uncompressed=uncompressed_es.nso0', stdout = subprocess.DEVNULL)
    with open('uncompressed_es.nso0', 'rb') as decompressed_es_nso:
        read_data = decompressed_es_nso.read()
        result = re.search(rb'.\x00\x91.{2}\x00\x94\xa0\x83\x00\xd1.{2}\xff\x97', read_data)
        if not result:
            changelog.write(f'ES related patch changelog for {version}:\n')
            changelog.write(f'{version} ES offset not found\n\n')
        else:
            patch = '%06X%s%s' % (result.end(), '0004', 'E0031FAA')
            offset = '%06X' % (result.end())
            text_file = open('./patches/atmosphere/exefs_patches/es_patches/%s.ips' % esbuildid, 'wb')
            changelog.write(f'ES related patch changelog for {version}:\n')
            changelog.write(f'{version} ES build-id: {esbuildid}\n')
            changelog.write(f'{version} ES offset and patch at: {patch}\n\n')
            text_file.write(bytes.fromhex(str(f'5041544348{patch}454F46')))
            text_file.close()


nifmbuildid = get_nifm_build_id()
nifm_patch = f'{nifmbuildid}.ips'

if nifm_patch in os.listdir('patches/atmosphere/exefs_patches/nifm_ctest'):
    changelog.write(f'NIFM CTEST related patch changelog for {version}:\n')
    changelog.write(f'NIFM CTEST patch for version {version} already exists as an .ips patch, and the build id is: {nifmbuildid}\n\n')
else:
    subprocess.run('hactool -t nso0 compressed_nifm.nso0 --uncompressed=uncompressed_nifm.nso0', stdout = subprocess.DEVNULL)
    with open('uncompressed_nifm.nso0', 'rb') as decompressed_nifm_nso:
        read_data = decompressed_nifm_nso.read()
        result = re.search(rb'.{20}\xf4\x03\x00\xaa.{4}\xf3\x03\x14\xaa\xe0\x03\x14\xaa\x9f\x02\x01\x39\x7f\x8e\x04\xf8', read_data)
        if not result:
            changelog.write(f'NIFM related patch changelog for {version}:\n')
            changelog.write(f'{version} NIFM offset not found\n\n')
        else:
            text_file = open('./patches/atmosphere/exefs_patches/nifm_ctest/%s.ips' % nifmbuildid, 'wb')
            patch = '%06X%s%s' % (result.start(), '0014', '00309AD2001EA1F2610100D4E0031FAAC0035FD6')
            offset = '%06X' % (result.start())
            changelog.write(f'NIFM related patch changelog for {version}:\n')
            changelog.write(f'{version} NIFM CTEST build-id: {nifmbuildid}\n')
            changelog.write(f'{version} NIFM CTEST offset and patch at: {patch}\n\n')
            text_file.write(bytes.fromhex(str(f'5041544348{patch}454F46')))
            text_file.close()
 
 
nimbuildid = get_nim_build_id()
nim_patch = f'{nimbuildid}.ips'
       
if nim_patch in os.listdir('patches/atmosphere/exefs_patches/ams_blanker_fix'):
    changelog.write(f'NIM related patch changelog for {version}:\n')
    changelog.write(f'NIM patch for version {version} already exists as an .ips patch, and the build id is: {nimbuildid}\n\n')
else:
    subprocess.run('hactool -t nso0 compressed_nim.nso0 --uncompressed=uncompressed_nim.nso0', stdout = subprocess.DEVNULL)     
    with open('uncompressed_nim.nso0', 'rb') as decompressed_nim_nso:
        read_data = decompressed_nim_nso.read()
        result = re.search(rb'\x80\x0f\x00\x35\x1f\x20\x03\xd5', read_data)
        if not result:
            changelog.write(f'nim related patch changelog for {version}:\n')
            changelog.write(f'{version} nim offset not found\n\n')
        else:
            text_file = open('./patches/atmosphere/exefs_patches/ams_blanker_fix/%s.ips' % nimbuildid, 'wb')
            patch = '%06X%s%s' % (result.end(), '0004', 'E2031FAA')
            offset = '%06X' % (result.end())
            changelog.write(f'nim related patch changelog for {version}:\n')
            changelog.write(f'{version} nim build-id: {nimbuildid}\n')
            changelog.write(f'{version} nim offset and patch at: {patch}\n\n')
            text_file.write(bytes.fromhex(str(f'5041544348{patch}454F46')))
            text_file.close()


fat32hash = hashlib.sha256(open(fat32compressed, 'rb').read()).hexdigest().upper()
with open('./hekate_patches/fs_patches.ini') as fs_patches:
    if fat32hash[:16] in fs_patches.read():
        changelog.write(f'FS-FAT32 patch related changelog for {version}:\n')
        changelog.write(f'FS-FAT32 patch for version {version} already exists in fs_patches.ini with the short hash of: {fat32hash[:16]}\n\n')
    else:
        with open(fat32uncompressed, 'rb') as fat32f:
            read_data = fat32f.read()
            result1 = re.search(rb'\x52.{3}\x52.{3}\x52.{3}\x52.{3}\x94', read_data)
            result2 = re.search(rb'\x08\x1C\x00\x12\x1F\x05\x00\x71\x41\x01\x00\x54', read_data)
            if not result1:
                changelog.write(f'FS-FAT32 patch related changelog for {version}:\n')
                changelog.write(f'{version} First FS-FAT32 offset not found\n')
            elif not result2:
                changelog.write(f'FS-FAT32 patch related changelog for {version}:\n')
                changelog.write(f'{version} Second FS-FAT32 offset not found\n')
            else:
                patch1 = '%06X%s%s' % (result1.end(), '0004', '1F2003D5')
                patch2 = '%06X%s%s' % (result2.start() - 0x4, '0004', 'E0031F2A')
                changelog.write(f'FS-FAT32 patch related changelog for {version}:\n')
                changelog.write(f'{version} First FS-FAT32 offset and patch at: {patch1}\n')
                changelog.write(f'{version} Second FS-FAT32 offset and patch at: {patch2}\n')
                changelog.write(f'{version} FS-FAT32 SHA256 hash: {fat32hash}\n\n')
                fat32_hekate = open('./hekate_patches/fs_patches.ini', 'a')
                fat32_hekate.write(f'\n#FS {version}-fat32\n')
                fat32_hekate.write(f'[FS:{fat32hash[:16]}]\n')
                hekate_bytes = fat32f.seek(result1.end())
                fat32_hekate.write('.nosigchk=0:0x' + '%06X' % (result1.end()-0x100) + ':0x4:' + fat32f.read(0x4).hex().upper() + ',1F2003D5\n')
                hekate_bytes = fat32f.seek(result2.start() - 0x4)
                fat32_hekate.write('.nosigchk=0:0x' + '%06X' % (result2.start()-0x104) + ':0x4:' + fat32f.read(0x4).hex().upper() + ',E0031F2A\n')
                fat32_hekate.close()
        fat32f.close()
fs_patches.close()

exfathash = hashlib.sha256(open(exfatcompressed, 'rb').read()).hexdigest().upper()
with open('./hekate_patches/fs_patches.ini') as fs_patches:
    if exfathash[:16] in fs_patches.read():
        changelog.write(f'FS-ExFAT patch related changelog for {version}:\n')
        changelog.write(f'FS-ExFAT patch for version {version} already exists in fs_patches.ini with the short hash of: {exfathash[:16]}\n')
    else:
        with open(exfatuncompressed, 'rb') as exfatf:
            read_data = exfatf.read()
            result1 = re.search(rb'\x52.{3}\x52.{3}\x52.{3}\x52.{3}\x94', read_data)
            result2 = re.search(rb'\x08\x1C\x00\x12\x1F\x05\x00\x71\x41\x01\x00\x54', read_data)
            if not result1:
                changelog.write(f'FS-ExFAT patch related changelog for {version}:\n')
                changelog.write(f'{version} First FS-ExFAT offset not found\n')
            elif not result2:
                changelog.write(f'FS-ExFAT patch related changelog for {version}:\n')
                changelog.write(f'{version} Second FS-ExFAT offset not found\n')
            else:
                patch1 = '%06X%s%s' % (result1.end(), '0004', '1F2003D5')
                patch2 = '%06X%s%s' % (result2.start() - 0x4, '0004', 'E0031F2A')
                changelog.write(f'FS-ExFAT patch related changelog for {version}:\n')
                changelog.write(f'{version} First FS-ExFAT offset and patch at: {patch1}\n')
                changelog.write(f'{version} Second FS-exFAT offset and patch at: {patch2}\n')
                changelog.write(f'{version} FS-ExFAT SHA256 hash: {exfathash}\n')
                exfat_hekate = open('./hekate_patches/fs_patches.ini', 'a')
                exfat_hekate.write(f'\n#FS {version}-exfat\n')
                exfat_hekate.write(f'[FS:{exfathash[:16]}]\n')
                hekate_bytes = exfatf.seek(result1.end())
                exfat_hekate.write('.nosigchk=0:0x' + '%06X' % (result1.end()-0x100) + ':0x4:' + exfatf.read(0x4).hex().upper() + ',1F2003D5\n')
                hekate_bytes = exfatf.seek(result2.start() - 0x4)
                exfat_hekate.write('.nosigchk=0:0x' + '%06X' % (result2.start()-0x104) + ':0x4:' + exfatf.read(0x4).hex().upper() + ',E0031F2A\n')
                exfat_hekate.close()
        exfatf.close()
fs_patches.close()
changelog.close()

with open(f'./patch_changelog.txt') as print_changelog:
    print(print_changelog.read())
print_changelog.close()

with open('./patches/bootloader/patches.ini', 'wb') as outfile:
    for filename in ['./hekate_patches/header.ini', './hekate_patches/fs_patches.ini', './hekate_patches/loader_patches.ini']:
        with open(filename, 'rb') as readfile:
            shutil.copyfileobj(readfile, outfile)