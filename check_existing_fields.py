from backend.db.session import get_session
from sqlalchemy import inspect

with get_session() as session:
    inspector = inspect(session.bind)
    columns = [col['name'] for col in inspector.get_columns('cam_leads')]
    
    needed_fields = [
        'routing_sequence', 'sequence_start_at', 'engagement_notes',
        'first_name', 'title', 'company_size', 'industry', 'growth_rate',
        'annual_revenue', 'employee_count', 'company_website', 'company_headquarters',
        'founding_year', 'funding_status', 'decision_maker_name', 'decision_maker_email',
        'decision_maker_role', 'decision_maker_linkedin', 'budget_estimate_range',
        'timeline_months', 'pain_points', 'buying_signals', 'lead_grade',
        'conversion_probability', 'fit_score_for_service', 'graded_at', 'grade_reason',
        'proposal_generated_at', 'proposal_content_id', 'contract_signed_at',
        'referral_source', 'referred_by_name', 'linkedin_status', 'contact_form_url',
        'contact_form_last_submitted_at', 'qualification_notes', 'email_valid',
        'intent_signals'
    ]
    
    missing = [f for f in needed_fields if f not in columns]
    existing = [f for f in needed_fields if f in columns]
    
    print("✅ Existing fields:")
    for f in existing:
        print(f"   {f}")
    
    print("\n❌ Missing fields:")
    for f in missing:
        print(f"   {f}")
