## Relevant Files

- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/gate_entry/gate_entry/doctype/gate_pass/gate_pass.py` - Server-side logic for gate pass lifecycle, validations, and doc event handlers.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/gate_entry/gate_entry/doctype/gate_pass/gate_pass.json` - Gate Pass DocType schema; add discrepancy tracking and linkage fields.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/gate_entry/gate_entry/doctype/gate_pass/gate_pass.js` - Client-side logic for gate pass forms.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/public/js/gate_pass_custom_ui.js` - Custom UI logic for gate pass item tables and Material Transfer selection.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/public/css/gate_pass.css` - Styling to support the custom gate pass UI.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/hooks.py` - Register Stock Entry doc events and background jobs without altering core ERPNext files.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/fixtures/custom_field.json` - Fixture defining Stock Entry custom fields (e.g., External Transfer checkbox) managed entirely within the module.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/fixtures/property_setter.json` - Fixture for form layout tweaks tied to custom fields (if required).
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/gate_entry/constants.py` - Shared status labels and configuration flags.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/gate_entry/setup/permissions.py` - Confirm existing permissions align with new flows.
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/gate_entry/doctype/gate_pass/test_gate_pass.py` - Automated tests for gate pass flows (create or extend).
- `/Users/gurudattkulkarni/Workspace/bench_apps/frappe-bench/apps/gate_entry/tests/test_stock_entry_integration.py` - New integration tests ensuring Stock Entry events trigger gate passes via hooks.

### Notes

- Unit tests should typically be placed alongside the code files they are testing.
- Use `bench --site <site_name> run-tests --doctype "Gate Pass"` or targeted pytest modules to validate the module without touching core ERPNext.
- All behaviour must be delivered through the `gate_entry` app (fixtures, hooks, client scripts) so the core ERPNext installation remains unchanged after install/uninstall.

## Tasks

- [x] 1.0 Review existing gate pass flows and identify hook points for integrating Stock Entry events solely through module-level functionality.
  - [x] 1.1 Audit current gate pass DocType workflow, status transitions, and quantity checks in `gate_pass.py`.
  - [x] 1.2 Map existing hooks defined in `hooks.py` and confirm where Stock Entry events can be intercepted.
  - [x] 1.3 Review current usage of public JS/CSS assets to understand entry points for UI changes.
- [ ] 2.0 Define and deliver Stock Entry customisations via fixtures and client scripts (External Transfer checkbox, validation prompts, UI hints).
  - [x] 2.1 Design the External Transfer checkbox and helper fields required on Stock Entry; document field specs.
  - [x] 2.2 Add custom fields via `setup_custom_fields.py`/install hooks so ERPNext core stays untouched.
  - [x] 2.3 Implement client-side logic (e.g., form script or query report) to suggest gate pass creation when the checkbox is selected.
  - [x] 2.4 Register Stock Entry doc events in `hooks.py` to enqueue gate pass creation without touching ERPNext core.
- [ ] 3.0 Enhance the Gate Pass DocType, server logic, and UI assets (including `gate_pass_custom_ui.js` and `gate_pass.css`) to support multi-pass allocations, discrepancy logging, and status lifecycle updates.
  - [x] 3.1 Update `gate_pass.json` to add discrepancy fields, Material Transfer reference, and vehicle details if missing.
  - [x] 3.2 Extend `gate_pass.py` with quantity allocation logic, discrepancy handling, and cancellation rules.
  - [x] 3.3 Modify `gate_pass.js` and `gate_pass_custom_ui.js` to manage partial allocations, checkbox-driven defaults, and UI alerts.
  - [x] 3.4 Refresh `gate_pass.css` for any new layout requirements (e.g., custom table styling, alerts).
  - [x] 3.5 Ensure new fields and UI elements respect existing permission checks from `setup/permissions.py`.
- [x] 4.0 Implement inbound handling logic and doc events that reference prior Material Transfers without modifying ERPNext core files.
  - [x] 4.1 Build logic to select prior outbound Material Transfer entries when creating inbound gate passes.
  - [x] 4.2 Add server-side validations ensuring inbound quantities respect remaining balances against the reference transfer.
  - [x] 4.3 Provide UI cues (JS/dialogues) guiding users to link inbound passes correctly when no Stock Entry exists yet.
  - [x] 4.4 Handle scenarios where the inbound Stock Entry is submitted later and should link back to the gate pass.
- [ ] 5.0 Add or extend automated tests and documentation to cover gate–stock integration and ensure uninstall leaves ERPNext unchanged.
  - [ ] 5.1 Write/extend tests in `test_gate_pass.py` to cover multi-pass allocations, discrepancy logging, and cancellations.
  - [ ] 5.2 Create integration tests in `tests/test_stock_entry_integration.py` for auto-created gate passes via Stock Entry events and inbound references.
  - [ ] 5.3 Document installation/uninstallation steps and confirm fixtures restore ERPNext to original state after uninstall.
  - [ ] 5.4 Update README or module docs summarising the new Stock Entry integration.

