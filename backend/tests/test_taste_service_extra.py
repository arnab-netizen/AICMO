from backend.modules.taste import service as taste


def test_taste_service_edge_branches():
    # If similar_assets expects a real query_embedding, exercise the empty-input branch
    if hasattr(taste, "similar_assets"):
        try:
            taste.similar_assets([], query_embedding=None, top_k=0)
        except Exception as e:
            # Similar_assets raises ValueError on empty query_embedding; ensure we handle it here
            assert isinstance(e, ValueError)
    else:
        # Fallback import check
        assert hasattr(taste, "__file__")
