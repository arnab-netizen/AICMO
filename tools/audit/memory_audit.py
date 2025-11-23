"""
Phase 4: Memory Engine & Neon Wiring Audit
Verify how the memory engine is configured and whether it persists data.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import time

# Ensure /workspaces/AICMO is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

OUT_DIR = Path(".aicmo/audit/memory")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# PART 1: Discover and import the memory engine
# ============================================================================

memory_config = {
    "timestamp": datetime.now().isoformat(),
    "engine_type": "unknown",
    "config_source": "unknown",
    "db_url": "unknown",
    "db_path": "unknown",
    "notes": [],
}

try:
    # Try to import memory engine from aicmo.memory
    from aicmo.memory.engine import DEFAULT_DB_PATH, USE_FAKE_EMBEDDINGS, DEFAULT_EMBEDDING_MODEL

    memory_config["engine_type"] = "SQLite with OpenAI embeddings"
    memory_config["db_path"] = DEFAULT_DB_PATH
    memory_config["embedding_model"] = DEFAULT_EMBEDDING_MODEL
    memory_config["using_fake_embeddings"] = USE_FAKE_EMBEDDINGS
    memory_config["notes"].append("Imported from aicmo.memory.engine")
    print("✓ Memory engine found: SQLite + OpenAI embeddings")

    if DEFAULT_DB_PATH:
        memory_config["notes"].append(f"Local DB path: {DEFAULT_DB_PATH}")
        if Path(DEFAULT_DB_PATH).exists():
            db_size = Path(DEFAULT_DB_PATH).stat().st_size
            memory_config["notes"].append(f"Local DB exists: {db_size} bytes")
            print(f"  DB file size: {db_size} bytes")
        else:
            memory_config["notes"].append(
                "Local DB does not exist yet (will be created on first write)"
            )

    if DEFAULT_DB_PATH == ":memory:":
        memory_config["notes"].append(
            "WARNING: Using in-memory DB (:memory:) - data will NOT persist"
        )
    elif DEFAULT_DB_PATH.startswith("/tmp/"):
        memory_config["notes"].append(
            "WARNING: Using temporary directory - data may be lost on reboot"
        )

except ImportError as e:
    memory_config["notes"].append(f"Import failed: {str(e)}")
    print(f"✗ Could not import memory engine: {e}")

# ============================================================================
# PART 2: Attempt minimal roundtrip write/read
# ============================================================================

roundtrip_result = {
    "test_timestamp": datetime.now().isoformat(),
    "test_marker": f"AUDIT_MEMORY_TEST_{int(time.time())}",
    "write_status": "not_attempted",
    "read_status": "not_attempted",
    "write_details": {},
    "read_details": {},
    "errors": [],
}

try:
    from aicmo.memory.engine import (
        learn_from_blocks,
        retrieve_relevant_blocks,
        get_memory_stats,
        DEFAULT_DB_PATH,
    )

    # Step 1: Write
    test_content = f"Audit test marker: {roundtrip_result['test_marker']}"

    try:
        print(f"Attempting write with marker: {roundtrip_result['test_marker']}...", end=" ")
        blocks = [("AUDIT_TEST_TITLE", test_content)]
        count = learn_from_blocks("AUDIT_TEST", blocks, db_path=DEFAULT_DB_PATH)
        roundtrip_result["write_status"] = "success"
        roundtrip_result["write_details"]["content"] = test_content
        roundtrip_result["write_details"]["blocks_written"] = count
        print("✓")
    except Exception as e:
        roundtrip_result["write_status"] = "failed"
        roundtrip_result["write_details"]["error"] = str(e)
        roundtrip_result["errors"].append(f"Write failed: {str(e)}")
        print(f"✗ {str(e)[:50]}")

    # Step 2: Query back
    if roundtrip_result["write_status"] == "success":
        try:
            print("Attempting query for test marker...", end=" ")
            results = retrieve_relevant_blocks(
                roundtrip_result["test_marker"], limit=5, db_path=DEFAULT_DB_PATH
            )

            if results and len(results) > 0:
                roundtrip_result["read_status"] = "success"
                roundtrip_result["read_details"]["results_count"] = len(results)
                roundtrip_result["read_details"]["first_result"] = {
                    "title": results[0].title,
                    "kind": results[0].kind,
                    "text_preview": results[0].text[:100],
                }
                print(f"✓ ({len(results)} results)")
            else:
                roundtrip_result["read_status"] = "empty_results"
                roundtrip_result["read_details"]["results_count"] = 0
                roundtrip_result["errors"].append("Query returned no results")
                print("✗ (no results)")
        except Exception as e:
            roundtrip_result["read_status"] = "failed"
            roundtrip_result["read_details"]["error"] = str(e)
            roundtrip_result["errors"].append(f"Query failed: {str(e)}")
            print(f"✗ {str(e)[:50]}")

except Exception as e:
    roundtrip_result["errors"].append(f"Memory engine not available: {str(e)}")
    print(f"✗ Memory engine roundtrip not possible: {e}")

# ============================================================================
# PART 3: Get memory stats
# ============================================================================

memory_stats = {"timestamp": datetime.now().isoformat(), "stats": "unknown"}

try:
    from aicmo.memory.engine import get_memory_stats

    stats = get_memory_stats()
    memory_stats["stats"] = stats
    print("✓ Memory stats retrieved")
except Exception as e:
    memory_stats["error"] = str(e)
    print(f"⚠ Could not get memory stats: {e}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

(OUT_DIR / "memory_config.json").write_text(json.dumps(memory_config, indent=2))
(OUT_DIR / "memory_roundtrip.json").write_text(json.dumps(roundtrip_result, indent=2))
(OUT_DIR / "memory_stats.json").write_text(json.dumps(memory_stats, indent=2))

print("\n" + "=" * 70)
print("MEMORY ENGINE AUDIT SUMMARY")
print("=" * 70)
print(f"Engine Type: {memory_config['engine_type']}")
print(f"Roundtrip Test: {roundtrip_result['write_status']} → {roundtrip_result['read_status']}")
if roundtrip_result["errors"]:
    print(f"Errors: {', '.join(roundtrip_result['errors'])}")
print("=" * 70)
print("\nDetails saved to:")
print("  - memory_config.json")
print("  - memory_roundtrip.json")
print("  - memory_stats.json")
