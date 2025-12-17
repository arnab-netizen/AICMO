UI Verification Checklist

Manual steps to verify the operator UI behavior when Playwright/E2E tooling is not present.

1) Start the UI

   ```bash
   streamlit run operator.py
   ```

2) Confirm tab order (left-to-right):
   - Lead Gen → Campaigns → Intake → Strategy → Creatives → Execution → Monitoring → Delivery → Autonomy → Learn → System

3) Intake behavior
   - Open Intake tab, fill required fields. Submit. You should see a success panel with client_id and engagement_id.
   - `st.session_state` keys set: `active_client_id`, `active_engagement_id`, `active_client_profile`, `active_engagement`.

4) Gating behavior
   - Strategy tab should be blocked until Intake is submitted (disabled panel showing missing keys).
   - After Intake, Strategy Generate button should be enabled and should write to `artifact_strategy`.
   - Creatives tab should be blocked until `artifact_strategy` exists.
   - Execution blocked until `artifact_creatives` exists.
   - Monitoring blocked until `artifact_execution` exists.
   - Delivery blocked until `artifact_strategy` and `artifact_creatives` exist and active context present.

5) Artifacts
   - Each Generate/Run must write a canonical artifact like: `{"id": "<uuid>", "data": {...}}` into session_state keys `artifact_*`.

6) Additional checks
   - Clear Active Client button clears active context keys and re-blocks downstream tabs.
