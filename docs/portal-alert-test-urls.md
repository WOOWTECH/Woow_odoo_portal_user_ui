# Portal Alert Test URLs

Test records created to verify each alert message styling.

## Sale Order / Quotation Detail

| # | Alert | Type | URL |
|---|-------|------|-----|
| 1 | "This offer expired!" | `alert-warning` | [SO-Expired S00115](http://192.168.2.254:8069/my/orders/115?access_token=cc8d8aaf-06c1-4766-934f-dc45bed50d2c) |
| 2 | "This quotation has been cancelled." | `alert-danger` | [SO-Cancelled S00116](http://192.168.2.254:8069/my/orders/116?access_token=2ad6bf65-7065-4be8-ab5f-233a1f3645bd) |
| 3 | "Thank You! Your order has been confirmed." | `alert-success` | [SO sign_ok](http://192.168.2.254:8069/my/orders/116?access_token=2ad6bf65-7065-4be8-ab5f-233a1f3645bd&message=sign_ok) |
| 4 | "Your order is not in a state to be rejected." | `alert-danger` | [SO cant_reject](http://192.168.2.254:8069/my/orders/116?access_token=2ad6bf65-7065-4be8-ab5f-233a1f3645bd&message=cant_reject) |

## Purchase Order Detail

| # | Alert | Type | URL |
|---|-------|------|-----|
| 5 | "This purchase has been cancelled." | `alert-danger` | [PO-Cancelled P00004](http://192.168.2.254:8069/my/purchase/4?access_token=115b1ec4-0c3f-40bf-8a4c-f034f221a7cb) |
| 6 | "This quotation has been accepted." | `alert-success` | [PO-Accepted P00005](http://192.168.2.254:8069/my/purchase/5?access_token=1c527bbc-0bfc-4969-9a70-08fe9a2b94a4) |
| 7 | "This quotation has been declined." | `alert-warning` | [PO-Declined P00006](http://192.168.2.254:8069/my/purchase/6?access_token=f5fc3042-d547-4724-9025-d5fa6d71e1fd) |

## Invoice Detail

| # | Alert | Type | URL |
|---|-------|------|-----|
| 8 | "Already Paid" + "Left to Pay" | `alert-success` + `alert-warning` | [INV-Partial INV/2026/00034](http://192.168.2.254:8069/my/invoices/88?access_token=5b3023c9-7f0e-41f5-b60e-30beff39be07) |
| 9 | "A payment has already been made..." | `alert-danger` | [INV-InPayment INV/2026/00035](http://192.168.2.254:8069/my/invoices/89?access_token=0abc5a6c-3bed-46b9-b4d3-da8537932a07) |

## General (no records needed)

| # | Alert | Type | How to trigger |
|---|-------|------|----------------|
| 10 | "This is a preview of the customer portal." | `alert-info` | Login as admin, visit any portal page |
| 11 | Empty state alerts | `alert-warning` | Visit list pages with no records for the user |

## Security / Account (triggered by form actions)

| # | Alert | Type | How to trigger |
|---|-------|------|----------------|
| 12 | "Password Updated!" | `alert-success` | Change password on Security page |
| 13 | Password error | `alert-danger` | Enter wrong current password on Security page |
| 14 | Account details errors | `alert-danger` | Submit invalid data on Account Details page |
