# Gate Pass Custom Fields Setup

This module adds custom fields to Purchase Receipt and Subcontracting Receipt to enable bidirectional linking with Gate Pass.

## What It Does

- Adds a `gate_pass` field to **Purchase Receipt**
- Adds a `gate_pass` field to **Subcontracting Receipt**
- Enables connections between Gate Pass and receipts to appear in the Connections sidebar

## Installation

### For New Installations

The custom fields will be automatically created when the Gate Entry app is installed via the `after_install` hook.

### For Existing Installations

If you already have the Gate Entry app installed, run this command to create the custom fields:

```bash
bench execute gate_entry.setup.setup_custom_fields.setup
```

Or from the Frappe console:

```bash
bench console
```

Then in the console:

```python
from gate_entry.setup.setup_custom_fields import setup
setup()
```

## Clear Cache and Restart

After creating the custom fields, clear the cache and restart the bench:

```bash
bench clear-cache
bench restart
```

## How It Works

1. When you create a Purchase Receipt or Subcontracting Receipt from a Gate Pass, the `gate_pass` field is automatically populated.
2. The bidirectional links are configured in `hooks.py` using the `document_links` configuration.
3. Both documents will show each other in the Connections sidebar.

## Testing

1. Create a Gate Pass from a Purchase Order
2. Submit the Gate Pass
3. Create a Purchase Receipt from the Gate Pass
4. Open either document and check the Connections sidebar - you should see the linked document

## Custom Fields Details

### Purchase Receipt
- **Field Name**: `gate_pass`
- **Field Type**: Link
- **Options**: Gate Pass
- **Location**: After `supplier_delivery_note` field
- **Read Only**: Yes

### Subcontracting Receipt
- **Field Name**: `gate_pass`
- **Field Type**: Link
- **Options**: Gate Pass
- **Location**: After `supplier_delivery_note` field
- **Read Only**: Yes

