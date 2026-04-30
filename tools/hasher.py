"""
Evidence Integrity Validator - File Hashing Module
Supports: MD5, SHA1, SHA256, SHA512, BLAKE2b, CRC32
"""

import hashlib
import os
import zlib
from datetime import datetime
from pathlib import Path


def hash_file(filepath: str, algorithm: str = "sha256", chunk_size: int = 65536) -> dict:
    """
    Compute hash of a file using the specified algorithm.
    Returns dict with filename, algorithm, hash, filesize, timestamp.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    path = Path(filepath)
    filesize = path.stat().st_size
    mod_time = datetime.fromtimestamp(path.stat().st_mtime)

    hash_func = _get_hash_func(algorithm)
    hexdigest = _compute(filepath, hash_func, chunk_size)

    return {
        "filename": path.name,
        "filepath": str(path.absolute()),
        "algorithm": algorithm.upper(),
        "hash": hexdigest,
        "filesize": filesize,
        "filesize_hr": _human_size(filesize),
        "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
        "extension": path.suffix.lower(),
    }


def hash_bulk(filepaths: list, algorithm: str = "sha256") -> list:
    """Hash multiple files, returning a list of results."""
    results = []
    for fp in filepaths:
        try:
            results.append(hash_file(fp, algorithm))
        except Exception as e:
            results.append({
                "filename": os.path.basename(fp),
                "filepath": fp,
                "error": str(e),
            })
    return results


def verify_hash(filepath: str, expected_hash: str, algorithm: str = None) -> dict:
    """
    Verify a file against an expected hash.
    Auto-detects algorithm if not specified.
    """
    if not algorithm:
        algorithm = _detect_algorithm(expected_hash)

    result = hash_file(filepath, algorithm)
    result["expected"] = expected_hash
    result["match"] = result["hash"].lower() == expected_hash.lower()
    return result


def _get_hash_func(algorithm: str):
    algo = algorithm.lower().replace("-", "").strip()
    algos = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha224": hashlib.sha224,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
        "blake2b": hashlib.blake2b,
        "blake2s": hashlib.blake2s,
        "sha3_256": hashlib.sha3_256,
        "sha3_512": hashlib.sha3_512,
    }
    if algo in algos:
        return algos[algo]
    raise ValueError(f"Unsupported algorithm: {algorithm}")


def _compute(filepath: str, hash_func, chunk_size: int) -> str:
    h = hash_func()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def _detect_algorithm(hash_str: str) -> str:
    h = hash_str.strip().lower()
    lengths = {32: "md5", 40: "sha1", 56: "sha224", 64: "sha256", 96: "sha384", 128: "sha512"}
    return lengths.get(len(h), "sha256")


if __name__ == "__main__":
    # Quick test
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else __file__
    for algo in ["md5", "sha1", "sha256", "sha512"]:
        r = hash_file(test_file, algo)
        print(f"{algo.upper()}: {r['hash']}  ({r['filename']})")
