#!/usr/bin/env python3
import io, shutil, subprocess, sys, tarfile
from pathlib import Path

PARENT = Path(__file__).resolve().parent
ENCRYPTED_ARCHIVE = PARENT/'.scrt.tar.gz.age'
DECRYPTED_FOLDER = PARENT/'.scrt'

def _check_archive(archive):
    base = DECRYPTED_FOLDER.resolve()
    for member in archive.getmembers():
        target = (PARENT / member.name).resolve()
        if target != base and base not in target.parents: raise RuntimeError(f'Unsafe archive entry: {member.name}')

def encrypt():
    if not DECRYPTED_FOLDER.is_dir(): raise FileNotFoundError(f'{DECRYPTED_FOLDER} not found')
    ENCRYPTED_ARCHIVE.unlink(missing_ok=True)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive: archive.add(DECRYPTED_FOLDER, arcname=DECRYPTED_FOLDER.name)
    subprocess.run(['age', '--passphrase', '--armor', '-o', ENCRYPTED_ARCHIVE], input=buffer.getvalue(), check=True)
    print(f'encrypted -> {ENCRYPTED_ARCHIVE.name}')
    shutil.rmtree(DECRYPTED_FOLDER)
    print(f'deleted: {DECRYPTED_FOLDER}')

def decrypt():
    if not ENCRYPTED_ARCHIVE.exists(): raise FileNotFoundError(f'{ENCRYPTED_ARCHIVE} not found')
    shutil.rmtree(DECRYPTED_FOLDER, ignore_errors=True)
    result = subprocess.run(['age', '--decrypt', ENCRYPTED_ARCHIVE], stdout=subprocess.PIPE, check=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode='r:gz') as archive:
        _check_archive(archive)
        archive.extractall(PARENT)
    print(f'decrypted -> {DECRYPTED_FOLDER}/')

def deploy():
    try:
        decrypt()
        subprocess.run([sys.executable, Path(DECRYPTED_FOLDER)/'deploy.py'], check=True)
    finally:
        shutil.rmtree(DECRYPTED_FOLDER, ignore_errors=True)
        print(f'deleted: {Path(DECRYPTED_FOLDER)}')

if __name__ == '__main__':
    if sys.platform != 'linux': raise EnvironmentError(f'{sys.platform} not supported')
    if len(sys.argv) != 2 or sys.argv[1] not in {'encrypt','decrypt','deploy'}: sys.exit('Usage: scrt.py encrypt|decrypt|deploy')
    if sys.argv[1] == 'encrypt': encrypt()
    if sys.argv[1] == 'decrypt': decrypt()
    if sys.argv[1] == 'deploy': deploy()
