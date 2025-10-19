import base64
from backend.tools.gate_report import write_report_bundle


def test_packager_zip_ok(tmp_path):
    run_meta = {"seconds_used": 4, "score": 0.96}
    copy_artifact = {"meta": {"variants": ["v1", "v2", "v3"]}}
    # one fake image
    raw_png = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("ascii")
    img_artifacts = [{"base64": raw_png}]
    out = tmp_path / "bundle.zip"
    write_report_bundle(str(out), "Acme", run_meta, copy_artifact, img_artifacts)
    assert out.exists()
    import zipfile

    with zipfile.ZipFile(out, "r") as z:
        names = set(z.namelist())
        assert "meta/run.json" in names
        assert "copy/copy.json" in names
        assert any(n.startswith("creatives/creative_") for n in names)
        assert "reports/gate_summary.png" in names
