from backend.modules.taste import service


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *a, **k):
        # emulate SQLAlchemy RowMapping with mappings().all() usage
        class R:
            def __init__(self, rows):
                self._rows = rows

            def mappings(self):
                class M:
                    def __init__(self, rows):
                        self._rows = rows

                    def all(self):
                        out = []
                        for r in self._rows:
                            out.append(
                                {
                                    "id": r[0],
                                    "name": r[1],
                                    "taste_score": r[2],
                                    "brand_alignment": r[3],
                                    "similarity": r[4],
                                }
                            )
                        return out

                return M(self._rows)

        return R(self._rows)


def test_similar_assets_sanitizes_nan_inf():
    rows = [
        (1, "a1", 0.8, 0.9, float("nan")),
        (2, "a2", 0.7, 0.85, float("inf")),
        (3, "a3", 0.6, 0.8, 0.123),
    ]
    sess = FakeSession(rows)
    out = service.similar_assets(sess, [0.0] * 1536, top_k=3, min_taste=0.0)
    # similarity coerced to 0.0 for nan/inf; preserve finite value
    by_id = {r[0]["id"]: r[0]["similarity"] for r in out}
    assert by_id[1] == 0.0
    assert by_id[2] == 0.0
    assert abs(by_id[3] - 0.123) < 1e-9
