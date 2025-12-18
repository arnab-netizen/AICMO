import pytest
from aicmo.core.compat import validate_compat, IncompatibleSchemaError


def make_artifact(version="1.0", include_required=True):
    base = {
        "id": "s1",
        "tenant_id": "t1",
        "project_id": "p1",
        "type": "STRATEGY",
        "schema_version": version,
        "version": 1,
        "checksum": "abc",
    }
    if include_required:
        base.update({"produced_by": "system"})
    return base


def test_older_compatible_passes():
    art = make_artifact(version="1.0")
    assert validate_compat(art)


def test_breaking_artifact_rejected():
    art = make_artifact(version="2.0")
    with pytest.raises(IncompatibleSchemaError):
        validate_compat(art)
