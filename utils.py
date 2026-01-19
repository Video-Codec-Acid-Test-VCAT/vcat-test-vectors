import hashlib
import os


def getChecksum(local_file_path):
    """
    Calculate the checksum of a local file using SHA256.
    """
    hash_sha256 = hashlib.sha256()

    with open(local_file_path, "rb") as f:
        while chunk := f.read(4096):
            hash_sha256.update(chunk)

    return hash_sha256.hexdigest()


def getFileLength(file_path):
    """
    Get the length (size) of the file in bytes.
    """
    return os.path.getsize(file_path)
