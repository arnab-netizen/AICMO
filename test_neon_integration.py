#!/usr/bin/env python3
"""
Test Neon database integration for AICMO learn-store.

This verifies that the Neon-backed learn functions work correctly.
"""

import os

# Set a test database URL (or use existing)
os.environ["DATABASE_URL"] = (
    os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/aicmo_test"
)

from streamlit_pages.aicmo_operator import (
    append_learn_item,
    ensure_learn_table,
    get_engine,
    load_learn_items,
)


def test_database_configuration():
    """Test that database is configured."""
    print("\n✓ TEST: Database Configuration")
    engine = get_engine()
    assert engine is not None
    print("  ✓ Engine created successfully")
    print(f"  ✓ Engine type: {type(engine)}")


def test_table_creation():
    """Test that the learn table is created."""
    print("\n✓ TEST: Table Creation")
    ensure_learn_table()
    print("  ✓ Table ensured (CREATE TABLE IF NOT EXISTS executed)")

    engine = get_engine()
    with engine.begin() as conn:
        from sqlalchemy import text

        result = conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'aicmo_learn_items')"
            )
        ).scalar()
        assert result, "aicmo_learn_items table not found"
        print("  ✓ Table exists in database")


def test_insert_and_load():
    """Test inserting and loading learn items."""
    print("\n✓ TEST: Insert & Load Items")

    # Clear existing items first (for test isolation)
    engine = get_engine()
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(text("DELETE FROM aicmo_learn_items"))
    print("  ✓ Cleared existing items")

    # Create test items
    test_items = [
        {
            "kind": "good",
            "filename": "best_practice.md",
            "size_bytes": 1024,
            "notes": "This is a gold standard example",
            "tags": ["marketing", "strategy"],
        },
        {
            "kind": "bad",
            "filename": "antipattern.md",
            "size_bytes": 512,
            "notes": "Avoid this approach",
            "tags": ["mistake", "design"],
        },
    ]

    # Insert items
    for item in test_items:
        append_learn_item(item)
    print(f"  ✓ Inserted {len(test_items)} test items")

    # Load items back
    loaded = load_learn_items()
    assert len(loaded) == len(test_items), f"Expected {len(test_items)}, got {len(loaded)}"
    print(f"  ✓ Loaded {len(loaded)} items from database")

    # Verify first item
    first_item = loaded[0]
    assert first_item["kind"] in ["good", "bad"]
    assert first_item["notes"]
    assert isinstance(first_item["tags"], list)
    print(f"  ✓ Item structure verified: {first_item['kind']} - {first_item['notes']}")

    # Check tags are properly deserialized
    assert all(isinstance(t, str) for t in first_item["tags"])
    print(f"  ✓ Tags properly deserialized: {first_item['tags']}")


def test_jsonb_handling():
    """Test that JSONB tags are handled correctly."""
    print("\n✓ TEST: JSONB Tag Handling")

    # Clear
    engine = get_engine()
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(text("DELETE FROM aicmo_learn_items"))

    # Insert with complex tags
    complex_item = {
        "kind": "good",
        "filename": "complex.md",
        "size_bytes": 2048,
        "notes": "Complex example with nested tags",
        "tags": ["a", "b", "c"],
    }
    append_learn_item(complex_item)
    print("  ✓ Inserted item with tags")

    # Load and verify
    items = load_learn_items()
    assert len(items) == 1
    loaded_item = items[0]
    assert loaded_item["tags"] == ["a", "b", "c"]
    print(f"  ✓ Tags preserved correctly: {loaded_item['tags']}")


def test_null_handling():
    """Test handling of optional fields."""
    print("\n✓ TEST: Null/Optional Field Handling")

    # Clear
    engine = get_engine()
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(text("DELETE FROM aicmo_learn_items"))

    # Insert minimal item
    minimal_item = {
        "kind": "good",
        "filename": None,
        "size_bytes": None,
        "notes": "",
        "tags": [],
    }
    append_learn_item(minimal_item)
    print("  ✓ Inserted minimal item (null fields)")

    # Load and verify
    items = load_learn_items()
    assert len(items) == 1
    loaded_item = items[0]
    assert loaded_item["filename"] is None
    assert loaded_item["size_bytes"] == 0
    assert loaded_item["notes"] == ""
    assert loaded_item["tags"] == []
    print("  ✓ Null/empty fields handled correctly")


def test_ordering():
    """Test that items are ordered by created_at DESC."""
    print("\n✓ TEST: Ordering by created_at")

    # Clear
    engine = get_engine()
    with engine.begin() as conn:
        from sqlalchemy import text

        conn.execute(text("DELETE FROM aicmo_learn_items"))

    # Insert multiple items
    for i in range(3):
        append_learn_item(
            {
                "kind": "good",
                "filename": f"item_{i}.md",
                "size_bytes": 100 * (i + 1),
                "notes": f"Item {i}",
                "tags": [],
            }
        )
    print("  ✓ Inserted 3 items")

    # Load and check order (most recent first)
    items = load_learn_items()
    assert len(items) == 3
    assert items[0]["filename"] == "item_2.md"
    assert items[1]["filename"] == "item_1.md"
    assert items[2]["filename"] == "item_0.md"
    print(f"  ✓ Items ordered correctly (DESC): {[i['filename'] for i in items]}")


def main():
    """Run all tests."""
    print("=" * 70)
    print("NEON DATABASE INTEGRATION TEST SUITE")
    print("=" * 70)

    try:
        test_database_configuration()
        test_table_creation()
        test_insert_and_load()
        test_jsonb_handling()
        test_null_handling()
        test_ordering()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nNeon integration ready. The learn-store is now backed by:")
        print("  • Neon Postgres database (DATABASE_URL)")
        print("  • SQLAlchemy ORM")
        print("  • JSONB for flexible tagging")
        print("  • Automatic table creation (idempotent)")
        print("\nNo changes needed to Streamlit code - it still calls:")
        print("  • load_learn_items()")
        print("  • append_learn_item()")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
