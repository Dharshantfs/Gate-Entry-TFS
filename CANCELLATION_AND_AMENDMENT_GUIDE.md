# Gate Pass Cancellation and Amendment Guide

## Overview

This document explains how Gate Pass cancellation and amendment are handled when linked to Purchase Receipts or Subcontracting Receipts.

## Implemented Approach

### ✅ Recommended Approach: **Prevent with Clear Guidance**

We've implemented a strict but user-friendly approach that maintains data integrity while providing clear guidance to users.

---

## Features

### 1. **Receipt Deletion/Cancellation Handling**

#### What Happens:
- Purchase Receipt or Subcontracting Receipt **can be deleted or cancelled** even if linked to Gate Pass
- The link is automatically cleared from the Gate Pass when receipt is deleted/cancelled
- User receives a notification that the Gate Pass has been updated

#### User Experience:
When deleting a Purchase Receipt linked to a Gate Pass:

```
✅ Purchase Receipt Deleted

Gate Pass GP-FY-2024-00001 has been updated. The receipt reference has been cleared.
```

#### Technical Implementation:
- Hooks: `on_trash()` and `on_cancel()` on Purchase Receipt and Subcontracting Receipt
- Methods: `on_purchase_receipt_trash()`, `on_purchase_receipt_cancel()`, etc.
- Configuration: `ignore_links_on_delete` in hooks.py
- Automatically clears the receipt reference field in Gate Pass
- Allows you to delete draft receipts without cancelling Gate Pass first

---

### 2. **Cancellation Protection**

#### What Happens:
- Gate Pass **cannot be cancelled** if it has linked Purchase Receipt or Subcontracting Receipt (whether Draft or Submitted)

#### User Experience:
When attempting to cancel a Gate Pass with linked receipts, users see:

```
❌ Cannot Cancel Gate Pass

Cannot cancel this Gate Pass because the following receipt(s) are linked to it:

• Purchase Receipt MAT-PRE-2024-00001 - Status: Submitted

Action Required:
Please cancel the linked receipt(s) first, then you can cancel this Gate Pass.
```

#### Technical Implementation:
- Hook: `before_cancel()`
- Method: `check_linked_receipts_before_cancel()`
- Checks both `purchase_receipt` and `subcontracting_receipt` fields
- Validates docstatus (0 = Draft, 1 = Submitted)
- Provides clickable links to the receipts in the error message

---

### 3. **Amendment Protection**

#### What Happens:
- Gate Pass **cannot be amended** if the original has linked receipts

#### User Experience:
When attempting to amend (submit an amended Gate Pass), users see:

```
❌ Cannot Amend Gate Pass

Cannot amend this Gate Pass because the following receipt(s) were created from it:

• Purchase Receipt MAT-PRE-2024-00001 - Status: Submitted

Action Required:
To amend this Gate Pass, please follow these steps:
1. Cancel the linked receipt(s)
2. Cancel this Gate Pass
3. Create a new Gate Pass with the correct details
4. Create a new receipt from the new Gate Pass
```

#### Technical Implementation:
- Hook: `on_submit()` (checks `amended_from` field)
- Method: `check_receipts_in_amended_document()`
- Prevents submission of amended document if original has receipts
- Provides step-by-step instructions

---

## Code Structure

### Methods Added to `GatePass` Class:

1. **`before_cancel()`**
   - Called automatically before cancellation
   - Triggers validation

2. **`check_linked_receipts_before_cancel()`**
   - Queries Purchase Receipt and Subcontracting Receipt fields
   - Checks document status
   - Builds list of linked receipts

3. **`on_submit()`** (modified)
   - Added check for amended documents
   - Validates against original document's receipts

4. **`check_receipts_in_amended_document()`**
   - Looks up the original Gate Pass (from `amended_from`)
   - Checks if original has linked receipts
   - Prevents submission if receipts exist

5. **`throw_cancellation_error(linked_receipts)`**
   - Formats user-friendly error message
   - Creates clickable links using `frappe.utils.get_link_to_form()`
   - Shows status of each receipt

6. **`throw_amendment_error(linked_receipts)`**
   - Similar to cancellation error
   - Provides step-by-step remediation instructions

### Document Event Handlers (for Purchase Receipt & Subcontracting Receipt):

7. **`on_purchase_receipt_trash(doc, method)`**
   - Called when Purchase Receipt is deleted
   - Clears the reference from Gate Pass

8. **`on_purchase_receipt_cancel(doc, method)`**
   - Called when Purchase Receipt is cancelled
   - Clears the reference from Gate Pass

9. **`on_subcontracting_receipt_trash(doc, method)`**
   - Called when Subcontracting Receipt is deleted
   - Clears the reference from Gate Pass

10. **`on_subcontracting_receipt_cancel(doc, method)`**
    - Called when Subcontracting Receipt is cancelled
    - Clears the reference from Gate Pass

11. **`clear_gate_pass_reference(receipt_doc, field_name)`**
    - Common utility to clear Gate Pass references
    - Updates Gate Pass without modifying timestamp
    - Shows success message with link to updated Gate Pass

---

## Workflow Examples

### Scenario 1: Normal Cancellation (No Receipts)

1. User creates Gate Pass GP-FY-2024-0001 ✅
2. User submits Gate Pass ✅
3. User cancels Gate Pass ✅
   - **Result:** Cancelled successfully

### Scenario 2: Deleting Draft Receipt (NEW!)

1. User creates Gate Pass GP-FY-2024-0002 ✅
2. User submits Gate Pass ✅
3. User creates Purchase Receipt (Draft) ✅
4. User realizes mistake and wants to delete the Draft Purchase Receipt
5. User clicks "Delete" on Purchase Receipt ✅
   - **Result:** Receipt deleted successfully
   - **Notification:** "Gate Pass GP-FY-2024-0002 has been updated. The receipt reference has been cleared."
6. Gate Pass is now free to be cancelled or new receipt can be created ✅

### Scenario 3: Cancellation with Draft Receipt (Alternative Method)

1. User creates Gate Pass GP-FY-2024-0003 ✅
2. User submits Gate Pass ✅
3. User creates Purchase Receipt (Draft) ✅
4. User attempts to cancel Gate Pass ❌
   - **Error:** "Cannot cancel... Purchase Receipt MAT-PRE-2024-00001 - Status: Draft"
5. User cancels or deletes Purchase Receipt first ✅
   - **Notification:** Gate Pass reference cleared automatically
6. User cancels Gate Pass ✅
   - **Result:** Cancelled successfully

### Scenario 3: Cancellation with Submitted Receipt (was Scenario 4)

1. User creates Gate Pass GP-FY-2024-0004 ✅
2. User submits Gate Pass ✅
3. User creates Purchase Receipt ✅
4. User submits Purchase Receipt ✅
5. User attempts to cancel Gate Pass ❌
   - **Error:** "Cannot cancel... Purchase Receipt MAT-PRE-2024-00002 - Status: Submitted"
6. User cancels Purchase Receipt first ✅
   - **Notification:** Gate Pass reference cleared automatically
7. User cancels Gate Pass ✅
   - **Result:** Cancelled successfully

### Scenario 4: Amendment with Receipt

1. User creates Gate Pass GP-FY-2024-0005 ✅
2. User submits Gate Pass ✅
3. User creates and submits Purchase Receipt ✅
4. User clicks "Amend" on Gate Pass ✅
5. User modifies fields and clicks "Submit" ❌
   - **Error:** "Cannot amend... Purchase Receipt MAT-PRE-2024-00003 - Status: Submitted"
   - **Guidance:** Follow 4-step process
6. User follows the steps:
   - Cancels Purchase Receipt ✅
     - **Notification:** Gate Pass reference cleared automatically
   - Cancels original Gate Pass ✅
   - Creates new Gate Pass with correct details ✅
   - Creates new Purchase Receipt ✅
   - **Result:** New documents created properly

---

## Benefits

### ✅ Data Integrity
- Prevents orphaned stock entries
- Maintains proper audit trail
- Follows accounting best practices

### ✅ User Experience
- Clear, actionable error messages
- Clickable links to related documents
- Step-by-step guidance
- Shows document status for context

### ✅ Compliance
- Ensures proper cancellation sequence
- Prevents backdated corrections
- Maintains complete transaction history

### ✅ Prevents Common Errors
- Can't cancel source after stock entry
- Can't modify quantities after receipt
- Can't create duplicate receipts

---

## Field Configuration

### Gate Pass DocType

```json
{
  "fieldname": "purchase_receipt",
  "fieldtype": "Link",
  "options": "Purchase Receipt",
  "read_only": 1,
  "no_copy": 1,
  "allow_on_submit": 1
}

{
  "fieldname": "subcontracting_receipt",
  "fieldtype": "Link",
  "options": "Subcontracting Receipt",
  "read_only": 1,
  "no_copy": 1,
  "allow_on_submit": 1
}
```

### Custom Fields (Purchase Receipt & Subcontracting Receipt)

```json
{
  "fieldname": "gate_pass",
  "fieldtype": "Link",
  "options": "Gate Pass",
  "read_only": 1,
  "no_copy": 1,
  "search_index": 1
}
```

---

## Testing Checklist

- [ ] Cancel Gate Pass without receipts (should succeed)
- [ ] Delete Draft Purchase Receipt linked to Gate Pass (should succeed with notification)
- [ ] Delete Draft Subcontracting Receipt linked to Gate Pass (should succeed with notification)
- [ ] Verify Gate Pass reference is cleared after deleting receipt
- [ ] Cancel Gate Pass with Draft Purchase Receipt (should fail)
- [ ] Cancel Gate Pass with Submitted Purchase Receipt (should fail)
- [ ] Cancel Gate Pass with Draft Subcontracting Receipt (should fail)
- [ ] Cancel Gate Pass with Submitted Subcontracting Receipt (should fail)
- [ ] Cancel Purchase Receipt and verify Gate Pass reference is cleared
- [ ] Cancel Subcontracting Receipt and verify Gate Pass reference is cleared
- [ ] Amend Gate Pass without receipts (should succeed)
- [ ] Amend Gate Pass with receipts (should fail on submit)
- [ ] Verify error messages show clickable links
- [ ] Verify error messages show correct status
- [ ] Complete full cancellation workflow (cancel receipt → cancel gate pass)
- [ ] Complete full amendment workflow (follow 4-step process)

---

## Future Enhancements (Optional)

These are **NOT** implemented but could be considered:

1. **Email Notifications**: Alert users when trying to cancel
2. **Batch Cancellation**: Tool to cancel Gate Pass + all linked receipts in one go
3. **Cancellation Log**: Track all cancellation attempts and reasons
4. **Role-Based Override**: Allow specific roles to force cancellation with reason
5. **Automatic Draft Deletion**: Auto-delete draft receipts when cancelling Gate Pass

---

## Support & Troubleshooting

### Q: Can I force cancel a Gate Pass?
**A:** No, by design. This maintains data integrity. Always cancel receipts first.

### Q: What if Purchase Invoice is created from Purchase Receipt?
**A:** Purchase Receipt will prevent cancellation if invoiced. Cancel in reverse order:
1. Cancel Purchase Invoice
2. Cancel Purchase Receipt
3. Cancel Gate Pass

### Q: Can I delete the receipt link manually?
**A:** No, the fields are read-only. This is intentional to prevent data corruption.

### Q: I made a mistake in quantities. What should I do?
**A:** Follow the amendment workflow:
1. Cancel all downstream documents (Invoice → Receipt → Gate Pass)
2. Create new Gate Pass with correct quantities
3. Create new Receipt and Invoice

---

## Related Files

- `/gate_entry/gate_entry/doctype/gate_pass/gate_pass.py` - Main controller
- `/gate_entry/gate_entry/doctype/gate_pass/gate_pass.json` - DocType definition
- `/gate_entry/hooks.py` - Document links configuration
- `/gate_entry/setup/setup_custom_fields.py` - Custom field creation

---

**Last Updated:** January 2025
**Version:** 1.0
**Status:** ✅ Production Ready

