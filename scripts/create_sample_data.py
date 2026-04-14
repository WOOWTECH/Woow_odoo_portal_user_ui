#!/usr/bin/env python3
"""
Create comprehensive sample data for portal user testing.
Run inside the Odoo container:
  podman exec odoo-portalui-web python3 /mnt/scripts/create_sample_data.py
"""
import xmlrpc.client
from datetime import date, timedelta

URL = 'http://localhost:8069'
DB = 'odooportalui'
LOGIN = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, LOGIN, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def x(model, method, *args, **kw):
    return models.execute_kw(DB, uid, PASSWORD, model, method, *args, **kw)

print("=" * 60)
print("Creating sample data for portal user testing")
print("=" * 60)

# ── Portal user partner ──
PORTAL_USER_ID = 7
PORTAL_PARTNER_ID = 8

# Make sure partner has customer rank
x('res.partner', 'write', [[PORTAL_PARTNER_ID], {'customer_rank': 1, 'supplier_rank': 1}])
print("[OK] Portal partner set as customer + vendor")

# ── Get some product IDs ──
products = x('product.product', 'search_read', [[('type', 'in', ['consu', 'service'])]], {'fields': ['id', 'name', 'list_price'], 'limit': 10})
if len(products) < 3:
    # Create products if needed
    for pname, pprice in [('筆記型電腦 Laptop Pro', 35000), ('辦公椅 Ergonomic Chair', 8500), ('顯示器 4K Monitor', 12000)]:
        pid = x('product.product', 'create', [{'name': pname, 'list_price': pprice, 'type': 'consu'}])
    products = x('product.product', 'search_read', [[('type', 'in', ['consu', 'service'])]], {'fields': ['id', 'name', 'list_price'], 'limit': 10})

print(f"[OK] Found {len(products)} products")

# ── Helper: today offset ──
def d(offset_days=0):
    return str(date.today() + timedelta(days=offset_days))

# ══════════════════════════════════════════════════════════
# 1. SALE ORDERS (報價單 / 銷售訂單)
# ══════════════════════════════════════════════════════════
print("\n--- Creating Sale Orders ---")

sale_orders = []
sale_configs = [
    {'name_suffix': '辦公設備採購', 'products_idx': [0, 1], 'confirm': True},
    {'name_suffix': '年度IT設備更新', 'products_idx': [0, 2], 'confirm': True},
    {'name_suffix': '新辦公室傢俱', 'products_idx': [1, 2, 0], 'confirm': False},  # quotation
    {'name_suffix': '緊急補貨', 'products_idx': [0], 'confirm': True},
    {'name_suffix': '員工福利品', 'products_idx': [1], 'confirm': False},  # quotation
]

for i, cfg in enumerate(sale_configs):
    lines = []
    for pi in cfg['products_idx']:
        p = products[pi % len(products)]
        lines.append((0, 0, {
            'product_id': p['id'],
            'product_uom_qty': (i + 1) * 2,
            'price_unit': p['list_price'],
        }))
    so_id = x('sale.order', 'create', [{
        'partner_id': PORTAL_PARTNER_ID,
        'order_line': lines,
        'note': f'Sample order - {cfg["name_suffix"]}',
    }])
    sale_orders.append(so_id)
    if cfg['confirm']:
        x('sale.order', 'action_confirm', [[so_id]])
    print(f"  [OK] SO #{so_id} - {cfg['name_suffix']} ({'confirmed' if cfg['confirm'] else 'quotation'})")

print(f"[OK] {len(sale_orders)} sale orders created")

# ══════════════════════════════════════════════════════════
# 2. INVOICES (發票)
# ══════════════════════════════════════════════════════════
print("\n--- Creating Invoices ---")

invoice_ids = []
invoice_configs = [
    {'ref': 'INV-2026-001', 'amount': 75000, 'post': True, 'narration': '辦公設備採購發票'},
    {'ref': 'INV-2026-002', 'amount': 35000, 'post': True, 'narration': '筆電採購款'},
    {'ref': 'INV-2026-003', 'amount': 12000, 'post': True, 'narration': '顯示器採購'},
    {'ref': 'INV-2026-004', 'amount': 8500, 'post': False, 'narration': '辦公椅（草稿）'},
]

for cfg in invoice_configs:
    inv_id = x('account.move', 'create', [{
        'move_type': 'out_invoice',
        'partner_id': PORTAL_PARTNER_ID,
        'ref': cfg['ref'],
        'narration': cfg['narration'],
        'invoice_line_ids': [(0, 0, {
            'name': cfg['narration'],
            'quantity': 1,
            'price_unit': cfg['amount'],
        })],
    }])
    invoice_ids.append(inv_id)
    if cfg['post']:
        x('account.move', 'action_post', [[inv_id]])
    print(f"  [OK] Invoice #{inv_id} - {cfg['ref']} ({'posted' if cfg['post'] else 'draft'})")

print(f"[OK] {len(invoice_ids)} invoices created")

# ══════════════════════════════════════════════════════════
# 3. PURCHASE ORDERS (採購單)
# ══════════════════════════════════════════════════════════
print("\n--- Creating Purchase Orders ---")

po_ids = []
po_configs = [
    {'name_suffix': '辦公耗材採購', 'products_idx': [0, 1], 'confirm': True},
    {'name_suffix': 'IT設備採購', 'products_idx': [2], 'confirm': True},
    {'name_suffix': '年度維護合約', 'products_idx': [0, 2], 'confirm': False},
]

for i, cfg in enumerate(po_configs):
    lines = []
    for pi in cfg['products_idx']:
        p = products[pi % len(products)]
        lines.append((0, 0, {
            'product_id': p['id'],
            'product_qty': (i + 1) * 3,
            'price_unit': p['list_price'] * 0.7,
            'name': p['name'],
        }))
    po_id = x('purchase.order', 'create', [{
        'partner_id': PORTAL_PARTNER_ID,
        'order_line': lines,
        'notes': f'Sample PO - {cfg["name_suffix"]}',
    }])
    po_ids.append(po_id)
    if cfg['confirm']:
        x('purchase.order', 'button_confirm', [[po_id]])
    print(f"  [OK] PO #{po_id} - {cfg['name_suffix']} ({'confirmed' if cfg['confirm'] else 'draft'})")

print(f"[OK] {len(po_ids)} purchase orders created")

# ══════════════════════════════════════════════════════════
# 4. PROJECTS & TASKS (專案 / 任務)
# ══════════════════════════════════════════════════════════
print("\n--- Creating Projects & Tasks ---")

# Create a portal-visible project
proj_id = x('project.project', 'create', [{
    'name': 'Woowtech 官網改版專案',
    'privacy_visibility': 'portal',
    'partner_id': PORTAL_PARTNER_ID,
}])
print(f"  [OK] Project #{proj_id} created")

proj2_id = x('project.project', 'create', [{
    'name': 'ERP 系統導入',
    'privacy_visibility': 'portal',
    'partner_id': PORTAL_PARTNER_ID,
}])
print(f"  [OK] Project #{proj2_id} created")

task_configs = [
    {'name': '需求訪談與文件撰寫', 'project_id': proj_id, 'stage': 'done'},
    {'name': 'UI/UX 線框稿設計', 'project_id': proj_id, 'stage': 'progress'},
    {'name': '前端切版 - 首頁', 'project_id': proj_id, 'stage': 'progress'},
    {'name': '前端切版 - 產品頁', 'project_id': proj_id, 'stage': 'todo'},
    {'name': '後端 API 開發', 'project_id': proj_id, 'stage': 'todo'},
    {'name': 'QA 測試與驗收', 'project_id': proj_id, 'stage': 'todo'},
    {'name': '資料庫遷移規劃', 'project_id': proj2_id, 'stage': 'progress'},
    {'name': '模組客製化需求', 'project_id': proj2_id, 'stage': 'progress'},
    {'name': '使用者教育訓練', 'project_id': proj2_id, 'stage': 'todo'},
    {'name': '上線前壓力測試', 'project_id': proj2_id, 'stage': 'todo'},
]

task_ids = []
for tcfg in task_configs:
    task_id = x('project.task', 'create', [{
        'name': tcfg['name'],
        'project_id': tcfg['project_id'],
        'partner_id': PORTAL_PARTNER_ID,
        'description': f'<p>任務說明：{tcfg["name"]}</p>',
    }])
    task_ids.append(task_id)
    print(f"  [OK] Task #{task_id} - {tcfg['name']}")

print(f"[OK] {len(task_ids)} tasks created across 2 projects")

# ══════════════════════════════════════════════════════════
# 5. MAIL.ACTIVITY — Diverse notifications for portal user
# ══════════════════════════════════════════════════════════
print("\n--- Creating Notifications (mail.activity) ---")

# Get activity type IDs
act_types = x('mail.activity.type', 'search_read', [[]], {'fields': ['id', 'name', 'category', 'icon']})
act_type_map = {t['name']: t for t in act_types}

# We need activity types: Email(1), Call(2), Meeting(3), To-Do(4), Upload Document(5)
AT_EMAIL = act_type_map.get('Email', {}).get('id', 1)
AT_CALL = act_type_map.get('Call', {}).get('id', 2)
AT_MEETING = act_type_map.get('Meeting', {}).get('id', 3)
AT_TODO = act_type_map.get('To-Do', {}).get('id', 4)
AT_UPLOAD = act_type_map.get('Upload Document', {}).get('id', 5)

# Create an Approval type (using 'default' category — grant_approval requires approvals module)
approval_types = x('mail.activity.type', 'search_read', [[('name', '=', 'Approval')]], {'fields': ['id']})
if approval_types:
    AT_APPROVAL = approval_types[0]['id']
else:
    AT_APPROVAL = x('mail.activity.type', 'create', [{
        'name': 'Approval',
        'category': 'default',
        'icon': 'fa-thumbs-up',
    }])
    print(f"  [OK] Created Approval activity type #{AT_APPROVAL}")

activity_count = 0

# ── Sale Order activities ──
if sale_orders:
    activities_so = [
        {'res_id': sale_orders[0], 'type': AT_EMAIL, 'summary': '請確認報價單金額', 'deadline': d(1), 'note': '客戶要求確認總金額是否含稅'},
        {'res_id': sale_orders[0], 'type': AT_APPROVAL, 'summary': '銷售主管審批 - 大額訂單', 'deadline': d(0), 'note': '超過 50,000 需主管審批'},
        {'res_id': sale_orders[1], 'type': AT_CALL, 'summary': '電話聯繫確認交期', 'deadline': d(2), 'note': '年度IT設備到貨時間需再確認'},
        {'res_id': sale_orders[2], 'type': AT_TODO, 'summary': '報價單待客戶確認簽回', 'deadline': d(3), 'note': '新辦公室傢俱報價已發出，等待回覆'},
        {'res_id': sale_orders[3], 'type': AT_EMAIL, 'summary': '緊急補貨出貨通知', 'deadline': d(0), 'note': '緊急單已安排出貨，需郵件通知客戶'},
    ]
    for a in activities_so:
        aid = x('mail.activity', 'create', [{
            'res_model_id': x('ir.model', 'search', [[('model', '=', 'sale.order')]])[0],
            'res_model': 'sale.order',
            'res_id': a['res_id'],
            'activity_type_id': a['type'],
            'summary': a['summary'],
            'date_deadline': a['deadline'],
            'note': f'<p>{a["note"]}</p>',
            'user_id': PORTAL_USER_ID,
        }])
        activity_count += 1
        print(f"  [OK] Activity #{aid} (SO) - {a['summary']}")

# ── Invoice activities ──
if invoice_ids:
    activities_inv = [
        {'res_id': invoice_ids[0], 'type': AT_APPROVAL, 'summary': '發票金額審批', 'deadline': d(1), 'note': '大額發票需財務主管核准'},
        {'res_id': invoice_ids[1], 'type': AT_TODO, 'summary': '確認付款條件', 'deadline': d(5), 'note': '筆電採購款 Net 30 付款條件確認'},
        {'res_id': invoice_ids[2], 'type': AT_EMAIL, 'summary': '發送發票至客戶信箱', 'deadline': d(0), 'note': '顯示器發票已開立，需郵寄'},
        {'res_id': invoice_ids[0], 'type': AT_UPLOAD, 'summary': '上傳匯款證明', 'deadline': d(2), 'note': '請上傳銀行轉帳截圖'},
    ]
    for a in activities_inv:
        aid = x('mail.activity', 'create', [{
            'res_model_id': x('ir.model', 'search', [[('model', '=', 'account.move')]])[0],
            'res_model': 'account.move',
            'res_id': a['res_id'],
            'activity_type_id': a['type'],
            'summary': a['summary'],
            'date_deadline': a['deadline'],
            'note': f'<p>{a["note"]}</p>',
            'user_id': PORTAL_USER_ID,
        }])
        activity_count += 1
        print(f"  [OK] Activity #{aid} (Invoice) - {a['summary']}")

# ── Purchase Order activities ──
if po_ids:
    activities_po = [
        {'res_id': po_ids[0], 'type': AT_APPROVAL, 'summary': '採購單審批 - 辦公耗材', 'deadline': d(1), 'note': '辦公耗材季度採購需部門主管核准'},
        {'res_id': po_ids[0], 'type': AT_CALL, 'summary': '聯繫供應商確認到貨日', 'deadline': d(3), 'note': '電話確認耗材供應商出貨排程'},
        {'res_id': po_ids[1], 'type': AT_EMAIL, 'summary': '催促IT設備交貨', 'deadline': d(-1), 'note': '已逾期一天，需發郵件催促'},
        {'res_id': po_ids[2], 'type': AT_TODO, 'summary': '維護合約條款確認', 'deadline': d(7), 'note': '年度維護合約需法務審閱'},
    ]
    for a in activities_po:
        aid = x('mail.activity', 'create', [{
            'res_model_id': x('ir.model', 'search', [[('model', '=', 'purchase.order')]])[0],
            'res_model': 'purchase.order',
            'res_id': a['res_id'],
            'activity_type_id': a['type'],
            'summary': a['summary'],
            'date_deadline': a['deadline'],
            'note': f'<p>{a["note"]}</p>',
            'user_id': PORTAL_USER_ID,
        }])
        activity_count += 1
        print(f"  [OK] Activity #{aid} (PO) - {a['summary']}")

# ── Project Task activities ──
if task_ids:
    activities_task = [
        {'res_id': task_ids[1], 'type': AT_TODO, 'summary': 'UI 線框稿修改第三版', 'deadline': d(2), 'note': '根據客戶回饋修改首頁排版'},
        {'res_id': task_ids[2], 'type': AT_MEETING, 'summary': '前端進度討論會議', 'deadline': d(1), 'note': '每週一前端開發同步會議'},
        {'res_id': task_ids[3], 'type': AT_UPLOAD, 'summary': '上傳產品頁設計稿', 'deadline': d(4), 'note': '設計師完成後需上傳 Figma 連結'},
        {'res_id': task_ids[4], 'type': AT_TODO, 'summary': 'API 規格文件審查', 'deadline': d(3), 'note': 'REST API 端點文件需 Tech Lead 審閱'},
        {'res_id': task_ids[6], 'type': AT_APPROVAL, 'summary': '資料庫架構核准', 'deadline': d(0), 'note': 'ERD 設計需 DBA 審批後才能進行遷移'},
        {'res_id': task_ids[7], 'type': AT_CALL, 'summary': '客製需求電話討論', 'deadline': d(1), 'note': '與客戶確認模組客製細節'},
        {'res_id': task_ids[8], 'type': AT_EMAIL, 'summary': '寄送教育訓練邀請', 'deadline': d(5), 'note': '發送訓練課程邀請給所有使用者'},
        {'res_id': task_ids[9], 'type': AT_TODO, 'summary': '壓力測試腳本準備', 'deadline': d(7), 'note': 'JMeter 測試腳本需提前準備'},
    ]
    for a in activities_task:
        aid = x('mail.activity', 'create', [{
            'res_model_id': x('ir.model', 'search', [[('model', '=', 'project.task')]])[0],
            'res_model': 'project.task',
            'res_id': a['res_id'],
            'activity_type_id': a['type'],
            'summary': a['summary'],
            'date_deadline': a['deadline'],
            'note': f'<p>{a["note"]}</p>',
            'user_id': PORTAL_USER_ID,
        }])
        activity_count += 1
        print(f"  [OK] Activity #{aid} (Task) - {a['summary']}")

# ── Generic partner activities (miscellaneous) ──
generic_activities = [
    {'type': AT_MEETING, 'summary': '季度業務檢討會議', 'deadline': d(2), 'note': '與管理層一起回顧 Q1 成果'},
    {'type': AT_EMAIL, 'summary': '合約到期提醒', 'deadline': d(0), 'note': '服務合約即將到期，需聯繫續約'},
    {'type': AT_TODO, 'summary': '更新公司聯絡資訊', 'deadline': d(1), 'note': '電話號碼和地址需要更新'},
]
for a in generic_activities:
    aid = x('mail.activity', 'create', [{
        'res_model_id': x('ir.model', 'search', [[('model', '=', 'res.partner')]])[0],
        'res_model': 'res.partner',
        'res_id': PORTAL_PARTNER_ID,
        'activity_type_id': a['type'],
        'summary': a['summary'],
        'date_deadline': a['deadline'],
        'note': f'<p>{a["note"]}</p>',
        'user_id': PORTAL_USER_ID,
    }])
    activity_count += 1
    print(f"  [OK] Activity #{aid} (Partner) - {a['summary']}")

# ══════════════════════════════════════════════════════════
# 6. Grant portal access to ensure records visible
# ══════════════════════════════════════════════════════════
print("\n--- Granting Portal Access ---")

# For sale orders — portal access is automatic via partner
# For invoices — ensure portal visibility
for inv_id in invoice_ids:
    try:
        x('account.move', 'write', [[inv_id], {'access_token': None}])
    except Exception:
        pass

# For projects — add portal user as follower
for pid in [proj_id, proj2_id]:
    try:
        x('project.project', 'message_subscribe', [[pid]], {'partner_ids': [PORTAL_PARTNER_ID]})
    except Exception:
        pass

# For tasks — add portal user as follower
for tid in task_ids:
    try:
        x('project.task', 'message_subscribe', [[tid]], {'partner_ids': [PORTAL_PARTNER_ID]})
    except Exception:
        pass

print("[OK] Portal access configured")

# ══════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SAMPLE DATA CREATED SUCCESSFULLY")
print("=" * 60)
print(f"  Sale Orders:      {len(sale_orders)} (3 confirmed + 2 quotations)")
print(f"  Invoices:         {len(invoice_ids)} (3 posted + 1 draft)")
print(f"  Purchase Orders:  {len(po_ids)} (2 confirmed + 1 draft)")
print(f"  Projects:         2 (portal-visible)")
print(f"  Tasks:            {len(task_ids)}")
print(f"  Notifications:    {activity_count} (across all modules)")
print(f"")
print(f"Portal login:  portal / portal")
print(f"Admin login:   admin / admin")
print(f"URL:           http://localhost:9097")
print("=" * 60)
