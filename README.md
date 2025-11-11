### Gate Entry

An erpnext security gate module for recording material and people movement

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app gate_entry
```

### Configuration

- Assign the auto-created `Security Guard` role to guard users. The setup hooks harden this role with read-only access to `Sales Invoice`, `Delivery Note`, and `GST Settings`, while keeping Desk access disabled.
- Ensure outbound sales documents capture transport details: add or expose `vehicle_number`, `driver_name`, and `driver_contact` fields on `Sales Invoice` and `Delivery Note` so the gate pass can auto-populate them.
- Review `GST Settings` and configure `e_waybill_threshold` (and `enable_e_waybill_from_dn` if Delivery Notes should be blocked) to align compliance checks with your statutory requirements.
- Keep guard users on the streamlined Gate Pass form; they should not require additional financial roles or report permissions.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/gate_entry
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
