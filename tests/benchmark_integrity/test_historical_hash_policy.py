"""Synthetic controls for explicit historical checkout-byte compatibility."""
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments/rcir_v8_5/scripts"))
from provenance import hash_file, matches_recorded_file_hash


@pytest.mark.parametrize("content", [b"line\n", b"line\r\n", "π 雪\n".encode(), b"\x00\xff\n"])
def test_raw_digest_always_remains_raw(tmp_path, content):
    path = tmp_path / "evidence"
    path.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    assert hash_file(path) == digest
    assert matches_recorded_file_hash(path, digest)


def test_reconstruction_requires_explicit_historical_policy(tmp_path):
    path = tmp_path / "evidence"
    raw = "π 雪\nsecond line\n".encode()
    path.write_bytes(raw)
    historical = hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()
    assert not matches_recorded_file_hash(path, historical)
    assert matches_recorded_file_hash(path, historical, allow_legacy_crlf=True)
    assert path.read_bytes() == raw
    assert hash_file(path) != historical
    path.write_bytes(raw.replace(b"second", b"SECOND"))
    assert not matches_recorded_file_hash(path, historical, allow_legacy_crlf=True)


@pytest.mark.parametrize("raw", [b"\x00binary\n", b"\xffinvalid\n", b"mixed\r\nlines\n"])
def test_binary_and_mixed_ending_transform_is_rejected(tmp_path, raw):
    path = tmp_path / "evidence"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()
    assert not matches_recorded_file_hash(path, digest, allow_legacy_crlf=True)


@pytest.mark.parametrize("digest", [None, "", "garbage", "0" * 64])
def test_missing_wrong_hash_and_missing_file_are_rejected(tmp_path, digest):
    assert not matches_recorded_file_hash(tmp_path / "missing", digest, allow_legacy_crlf=True)
    path = tmp_path / "exists"
    path.write_bytes(b"file\n")
    assert not matches_recorded_file_hash(path, digest, allow_legacy_crlf=True)
