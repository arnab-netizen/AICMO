#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          STREAMLIT STALE CACHE FIX SCRIPT v1                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"

ROOT="/workspaces/AICMO"
cd "$ROOT"

echo ""
echo "📋 PRE-FIX VERIFICATION"
echo "════════════════════════════════════════════════════════════════"
echo "Working directory: $(pwd)"
echo "Python: $(which python)"
echo "Streamlit: $(which streamlit)"
echo "Python version: $(python --version)"

# Step 1: Deactivate and reactivate venv
echo ""
echo "🔄 STEP 1: Reset Virtual Environment"
echo "════════════════════════════════════════════════════════════════"
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Deactivating current venv: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

source "$ROOT/.venv-1/bin/activate"
echo "✅ Activated: $VIRTUAL_ENV"

# Step 2: Clean Python caches
echo ""
echo "🗑️  STEP 2: Delete Python Cache (__pycache__)"
echo "════════════════════════════════════════════════════════════════"
CACHE_COUNT=$(find "$ROOT" -type d -name __pycache__ -not -path "*/.venv*" | wc -l)
echo "Found $CACHE_COUNT __pycache__ directories"
find "$ROOT" -type d -name __pycache__ -not -path "*/.venv*" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Deleted all .pyc files and __pycache__ directories"

# Step 3: Clean Streamlit cache
echo ""
echo "🗑️  STEP 3: Delete Streamlit Cache"
echo "════════════════════════════════════════════════════════════════"
rm -rf ~/.streamlit/ 2>/dev/null || true
rm -rf "$ROOT/.streamlit/" 2>/dev/null || true
echo "✅ Cleared Streamlit cache"

# Step 4: Reinstall Streamlit fresh
echo ""
echo "📦 STEP 4: Reinstall Streamlit (Fresh)"
echo "════════════════════════════════════════════════════════════════"
pip install --force-reinstall --no-cache-dir streamlit==1.50.0 > /dev/null 2>&1 && echo "✅ Streamlit reinstalled"

# Step 5: Create multipage structure
echo ""
echo "📁 STEP 5: Set Up Multipage Structure"
echo "════════════════════════════════════════════════════════════════"

if [[ -d "$ROOT/streamlit_pages" && ! -d "$ROOT/pages" ]]; then
    echo "Moving streamlit_pages/ → pages/"
    mkdir -p "$ROOT/pages"
    mv "$ROOT/streamlit_pages"/*.py "$ROOT/pages/" 2>/dev/null || true
    
    # Rename aicmo_operator.py to have Streamlit prefix
    if [[ -f "$ROOT/pages/aicmo_operator.py" ]]; then
        mv "$ROOT/pages/aicmo_operator.py" "$ROOT/pages/1_Operator_Dashboard.py"
        echo "✅ Renamed: 1_Operator_Dashboard.py"
    fi
    
    rm -rf "$ROOT/streamlit_pages"
    echo "✅ Created pages/ directory"
else
    echo "ℹ️  pages/ already exists or streamlit_pages/ not found"
fi

# Step 6: Create Streamlit config
echo ""
echo "⚙️  STEP 6: Create .streamlit/config.toml"
echo "════════════════════════════════════════════════════════════════"
mkdir -p "$ROOT/.streamlit"
cat > "$ROOT/.streamlit/config.toml" << 'STREAMLIT_CONFIG'
[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "debug"

[cache]
maxMessageSize = 200

[server]
headless = true
runOnSave = true
fileWatcherType = "poll"
STREAMLIT_CONFIG
echo "✅ Created .streamlit/config.toml"

# Step 7: Verify structure
echo ""
echo "✅ VERIFICATION"
echo "════════════════════════════════════════════════════════════════"
echo "Directory structure:"
ls -la "$ROOT" | grep -E "streamlit|pages"

echo ""
echo "Main app:"
ls -lh "$ROOT/streamlit_app.py"

echo ""
echo "Pages directory:"
if [[ -d "$ROOT/pages" ]]; then
    ls -la "$ROOT/pages/" | grep -E "\.py"
else
    echo "No pages/ yet"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║ ✅ FIX COMPLETE                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo ""
echo "🚀 TO START THE APP:"
echo "   cd /workspaces/AICMO"
echo "   source .venv-1/bin/activate"
echo "   streamlit run streamlit_app.py --logger.level=debug"

echo ""
echo "📍 Expected behavior:"
echo "   ✓ Main app loads from streamlit_app.py"
echo "   ✓ Left sidebar shows 'Pages' dropdown"
echo "   ✓ Can select '1_Operator_Dashboard' page"
echo "   ✓ Debug logs show module loading"

echo ""
