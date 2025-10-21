from backend.app import app


def test_print_routes():
    print("\n".join(sorted({r.path for r in app.routes})))
