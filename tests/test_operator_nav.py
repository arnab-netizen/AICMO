import importlib


def test_nav_tabs_constant():
    op = importlib.import_module('operator_v2')
    expected = [
        "Lead Gen",
        "Campaigns",
        "Intake",
        "Strategy",
        "Creatives",
        "Execution",
        "Monitoring",
        "Delivery",
        "Autonomy",
        "Learn",
        "System",
    ]
    assert getattr(op, 'NAV_TABS') == expected


def test_intake_store_inmemory_roundtrip():
    store_mod = importlib.import_module('aicmo.ui.persistence.intake_store')
    store = store_mod.IntakeStore(mode='inmemory')
    client_id = store.create_client({'client_name': 'X', 'company_or_brand': 'Y', 'primary_email': 'a@b.com'})
    assert isinstance(client_id, str) and len(client_id) > 0
    eid = store.create_engagement(client_id, {'product_or_service': 'p'})
    assert isinstance(eid, str) and len(eid) > 0
