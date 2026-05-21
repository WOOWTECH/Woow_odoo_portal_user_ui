# Portal Alert Messages — Complete Catalog

## Alert Type Summary

| Type | Count | Purpose |
|------|-------|---------|
| `alert-warning` | 19 | Empty states, expired offers, pending actions |
| `alert-danger` | 11 | Errors, cancellations, payment blocks |
| `alert-success` | 5 | Confirmations (signed, paid, password changed) |
| `alert-info` | 3 | Preview mode banner, informational |

---

## 1. General Portal (all pages)

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "This is a preview of the customer portal. Back to edit mode" | `alert-info alert-dismissible` | Backend user previewing portal | `portal/views/portal_templates.xml:150-156` |
| Dynamic fullwidth alert | `alert-info` | `o_portal_fullwidth_alert` variable set | `portal/views/portal_templates.xml:36` |

---

## 2. Sale Order / Quotation

### List Pages

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "There are currently no quotations for your account." | `alert-warning` | `not quotations` | `sale/views/sale_portal_templates.xml:53` |
| "There are currently no sales orders for your account." | `alert-warning` | `not orders` | `sale/views/sale_portal_templates.xml:93` |

### Detail Page

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "This offer expired! Contact us to get a new quotation." | `alert-warning alert-dismissible` | `sale_order.is_expired` | `sale/views/sale_portal_templates.xml:335` |
| "This quotation has been cancelled. Contact us to get a new quotation." | `alert-danger alert-dismissible` | `sale_order.state == 'cancel'` | `sale/views/sale_portal_templates.xml:330` |
| "Thank You! Your order has been confirmed." | `alert-success alert-dismissible` | `message == 'sign_ok'` and order paid | `sale/views/sale_portal_templates.xml:307-310` |
| "Your order has been signed but still needs to be paid to be confirmed." | `alert-success alert-dismissible` | `message == 'sign_ok'` and order unpaid | `sale/views/sale_portal_templates.xml:312-316` |
| "Your order is not in a state to be rejected." | `alert-danger alert-dismissible` | `message == 'cant_reject'` | `sale/views/sale_portal_templates.xml:319` |
| "The order is not in a state requiring customer payment." | `alert-danger` | `not sale_order._has_to_be_paid()` | `sale/views/sale_portal_templates.xml:265` |

---

## 3. Invoice / Payment

### List Page

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "There are currently no invoices and payments for your account." | `alert-warning` | `not invoices` | `account/views/account_portal_templates.xml:48` |

### Detail Page

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "Already Paid: [amount]" | `alert-success` | `payment_state == 'partial'` | `account/views/account_portal_templates.xml:129` |
| "Left to Pay: [amount]" | `alert-warning` | `payment_state == 'partial'` | `account/views/account_portal_templates.xml:132` |
| Early payment discount message | `alert-warning` | `installment_state == 'epd'` | `account/views/account_portal_templates.xml:140` |
| Generic error message | `alert-danger` or `alert-warning` | `error` variable set | `account/views/account_portal_templates.xml:216` |
| Success notification | `alert-success alert-dismissible` | `success` variable set | `account/views/account_portal_templates.xml:227` |
| "A payment has already been made on this invoice, please make sure to not pay twice." | `alert-danger` | `payment_state == 'in_payment'` | `account_payment/views/account_portal_templates.xml:177` |
| "Early Payment Discount of [amount] has been applied." | `alert-success` | `show_epd` | `account_payment/views/account_portal_templates.xml:210, 238` |

---

## 4. Purchase Order

### List Pages

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "There are currently no requests for quotation for your account." | `alert-warning` | `not rfqs` | `purchase/views/portal_templates.xml:50` |
| "There are currently no purchase orders for your account." | `alert-warning` | `not orders` | `purchase/views/portal_templates.xml:87` |

### Detail Page

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "This purchase has been cancelled." | `alert-danger alert-dismissible` | `order.state == 'cancel'` | `purchase/views/portal_templates.xml:219` |
| "This quotation has been accepted." | `alert-success alert-dismissible` | `order.mail_reception_confirmed` and not purchased | `purchase/views/portal_templates.xml:223` |
| "This quotation has been declined." | `alert-warning alert-dismissible` | `order.mail_reception_declined` and not purchased | `purchase/views/portal_templates.xml:227` |

---

## 5. Project / Task

### List Pages

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "There are no projects." | `alert-warning` | `not projects` | `project/views/project_portal_project_project_templates.xml:71` |
| "There are no tasks." | `alert-warning` | `not grouped_tasks` | `project/views/project_portal_project_task_templates.xml:121` |

### Project Sharing

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "This is a preview of how the project will look when it's shared with customers..." | `alert-info alert-dismissible` | Backend user (`groups="base.group_user"`) | `project/views/project_sharing_project_task_views.xml:109` |

---

## 6. Timesheet

### List Page

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "There are no timesheets." | `alert-warning` | `not grouped_timesheets` | `hr_timesheet/views/hr_timesheet_portal_templates.xml:34` |

---

## 7. Security / Account Page

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "Password Updated!" | `alert-success` | `success and success.get('password')` | `portal/views/portal_templates.xml:569` |
| Password error | `alert-danger` | `get_error(errors, 'password')` | `portal/views/portal_templates.xml:572` |
| General security error | `alert-danger` | `get_error(errors)` | `portal/views/portal_templates.xml:559` |
| Account details form errors | `alert-danger` | `error_message` present | `portal/views/portal_templates.xml:445` |
| Account deactivation error | `alert-danger` | `get_error(errors, 'deactivate.other')` | `portal/views/portal_templates.xml:670` |

---

## 8. Payment Form

| Message | Type | Condition | Template |
|---------|------|-----------|----------|
| "There is nothing to pay." | `alert-info` | `not amount` | `payment/views/portal_templates.xml:30` |
| "Warning: The currency is missing or incorrect." | `alert-warning` | `not currency` | `payment/views/portal_templates.xml:33` |
| "Warning: You must be logged in to pay." | `alert-warning` | `not partner_id` | `payment/views/portal_templates.xml:36` |
| "Warning: Make sure you are logged in as the correct partner before making this payment." | `alert-warning` | `partner_is_different` | `payment/views/portal_templates.xml:43` |
| "Please switch to company [company_name] to make this payment." | `alert-warning` | `expected_company` set | `payment/views/portal_templates.xml:81` |
| Online payment error | `alert-warning` | Payment error modal | `account_payment/views/account_portal_templates.xml:280` |

---

## 9. Woow Portal UI — Empty State Alerts

Custom empty state messages in card grid templates:

| Message | Page | Template Line |
|---------|------|---------------|
| "There are currently no sales orders for your account." | Sales Orders | `portal_templates.xml:528` |
| "There are currently no invoices and payments for your account." | Invoices | `portal_templates.xml:604` |
| "There are currently no quotations for your account." | Quotations | `portal_templates.xml:684` |
| "There are currently no projects for your account." | Projects | `portal_templates.xml:714` |
| "There are currently no opportunities." | Opportunities | `portal_templates.xml:787` |
| "There are currently no manufacturing orders." | Manufacturing | `portal_templates.xml:825` |
| "There are currently no requests for quotation." | RFQs | `portal_templates.xml:859` |
| "There are currently no purchase orders." | Purchase Orders | `portal_templates.xml:896` |
| "There are no leads." | Leads | `portal_templates.xml:938` |

All use `alert-warning` type.
