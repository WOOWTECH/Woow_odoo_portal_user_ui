#!/usr/bin/env python3
"""
Create diverse mail.activity notifications for portal user testing.
Run inside the Odoo container after business data already exists.
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

def d(offset_days=0):
    return str(date.today() + timedelta(days=offset_days))

def model_id(model_name):
    return x('ir.model', 'search', [[('model', '=', model_name)]])[0]

PORTAL_USER_ID = 7
PORTAL_PARTNER_ID = 8

print("=" * 60)
print("Creating notifications for portal user")
print("=" * 60)

# ── Get activity types ──
act_types = x('mail.activity.type', 'search_read', [[]], {'fields': ['id', 'name', 'category', 'icon']})
at = {t['name']: t['id'] for t in act_types}

AT_EMAIL = at.get('Email', 1)
AT_CALL = at.get('Call', 2)
AT_MEETING = at.get('Meeting', 3)
AT_TODO = at.get('To-Do', 4)
AT_UPLOAD = at.get('Upload Document', 5)

# Create Approval type if not exists
if 'Approval' not in at:
    AT_APPROVAL = x('mail.activity.type', 'create', [{
        'name': 'Approval',
        'category': 'default',
        'icon': 'fa-thumbs-up',
    }])
    print(f"  Created Approval activity type #{AT_APPROVAL}")
else:
    AT_APPROVAL = at['Approval']

# ── Get existing records ──
sale_orders = x('sale.order', 'search', [[('partner_id', '=', PORTAL_PARTNER_ID)]], {'order': 'id asc'})
invoices = x('account.move', 'search', [[('partner_id', '=', PORTAL_PARTNER_ID), ('move_type', '=', 'out_invoice')]], {'order': 'id asc'})
po_ids = x('purchase.order', 'search', [[('partner_id', '=', PORTAL_PARTNER_ID)]], {'order': 'id asc'})
tasks = x('project.task', 'search', [[('partner_id', '=', PORTAL_PARTNER_ID)]], {'order': 'id asc'})

print(f"  Found: {len(sale_orders)} SOs, {len(invoices)} invoices, {len(po_ids)} POs, {len(tasks)} tasks")

activity_count = 0

def create_act(res_model, res_id, act_type, summary, deadline, note):
    global activity_count
    aid = x('mail.activity', 'create', [{
        'res_model_id': model_id(res_model),
        'res_model': res_model,
        'res_id': res_id,
        'activity_type_id': act_type,
        'summary': summary,
        'date_deadline': deadline,
        'note': f'<p>{note}</p>',
        'user_id': PORTAL_USER_ID,
    }])
    activity_count += 1
    icon_map = {AT_EMAIL: 'Email', AT_CALL: 'Call', AT_MEETING: 'Meeting', AT_TODO: 'To-Do', AT_UPLOAD: 'Upload', AT_APPROVAL: 'Approval'}
    act_name = icon_map.get(act_type, '?')
    print(f"  [OK] #{aid} [{act_name}] {summary}")
    return aid

# ══════════════════════════════════════════════════════════
# Sale Order Notifications
# ══════════════════════════════════════════════════════════
print("\n--- Sale Order 通知 ---")
if len(sale_orders) >= 4:
    create_act('sale.order', sale_orders[0], AT_EMAIL,    '請確認報價單金額',           d(1),  '客戶要求確認總金額是否含稅')
    create_act('sale.order', sale_orders[0], AT_APPROVAL, '銷售主管審批 - 大額訂單',     d(0),  '超過 50,000 需主管審批')
    create_act('sale.order', sale_orders[1], AT_CALL,     '電話聯繫確認交期',            d(2),  '年度IT設備到貨時間需再確認')
    create_act('sale.order', sale_orders[2], AT_TODO,     '報價單待客戶確認簽回',         d(3),  '新辦公室傢俱報價已發出，等待回覆')
    create_act('sale.order', sale_orders[3], AT_EMAIL,    '緊急補貨出貨通知',            d(0),  '緊急單已安排出貨，需郵件通知客戶')

# ══════════════════════════════════════════════════════════
# Invoice Notifications
# ══════════════════════════════════════════════════════════
print("\n--- Invoice 通知 ---")
if len(invoices) >= 3:
    create_act('account.move', invoices[0], AT_APPROVAL, '發票金額審批',              d(1),  '大額發票需財務主管核准')
    create_act('account.move', invoices[1], AT_TODO,     '確認付款條件',              d(5),  '筆電採購款 Net 30 付款條件確認')
    create_act('account.move', invoices[2], AT_EMAIL,    '發送發票至客戶信箱',         d(0),  '顯示器發票已開立，需郵寄')
    create_act('account.move', invoices[0], AT_UPLOAD,   '上傳匯款證明',              d(2),  '請上傳銀行轉帳截圖')

# ══════════════════════════════════════════════════════════
# Purchase Order Notifications
# ══════════════════════════════════════════════════════════
print("\n--- Purchase Order 通知 ---")
if len(po_ids) >= 3:
    create_act('purchase.order', po_ids[0], AT_APPROVAL, '採購單審批 - 辦公耗材',      d(1),  '辦公耗材季度採購需部門主管核准')
    create_act('purchase.order', po_ids[0], AT_CALL,     '聯繫供應商確認到貨日',        d(3),  '電話確認耗材供應商出貨排程')
    create_act('purchase.order', po_ids[1], AT_EMAIL,    '催促IT設備交貨',             d(-1), '已逾期一天，需發郵件催促')
    create_act('purchase.order', po_ids[2], AT_TODO,     '維護合約條款確認',            d(7),  '年度維護合約需法務審閱')

# ══════════════════════════════════════════════════════════
# Project Task Notifications
# ══════════════════════════════════════════════════════════
print("\n--- Project Task 通知 ---")
if len(tasks) >= 10:
    create_act('project.task', tasks[1], AT_TODO,     'UI 線框稿修改第三版',         d(2),  '根據客戶回饋修改首頁排版')
    create_act('project.task', tasks[2], AT_MEETING,  '前端進度討論會議',            d(1),  '每週一前端開發同步會議')
    create_act('project.task', tasks[3], AT_UPLOAD,   '上傳產品頁設計稿',            d(4),  '設計師完成後需上傳 Figma 連結')
    create_act('project.task', tasks[4], AT_TODO,     'API 規格文件審查',            d(3),  'REST API 端點文件需 Tech Lead 審閱')
    create_act('project.task', tasks[5], AT_APPROVAL, '資料庫架構核准',              d(0),  'ERD 設計需 DBA 審批後才能進行遷移')
    create_act('project.task', tasks[6], AT_CALL,     '客製需求電話討論',            d(1),  '與客戶確認模組客製細節')
    create_act('project.task', tasks[7], AT_EMAIL,    '寄送教育訓練邀請',            d(5),  '發送訓練課程邀請給所有使用者')
    create_act('project.task', tasks[8], AT_TODO,     '壓力測試腳本準備',            d(7),  'JMeter 測試腳本需提前準備')
    create_act('project.task', tasks[9], AT_MEETING,  'QA 驗收會議排定',             d(6),  '邀請 PM 與客戶參加最終驗收')

# ══════════════════════════════════════════════════════════
# Partner / General Notifications
# ══════════════════════════════════════════════════════════
print("\n--- General 通知 ---")
create_act('res.partner', PORTAL_PARTNER_ID, AT_MEETING, '季度業務檢討會議',          d(2),  '與管理層一起回顧 Q1 成果')
create_act('res.partner', PORTAL_PARTNER_ID, AT_EMAIL,   '合約到期提醒',              d(0),  '服務合約即將到期，需聯繫續約')
create_act('res.partner', PORTAL_PARTNER_ID, AT_TODO,    '更新公司聯絡資訊',          d(1),  '電話號碼和地址需要更新')
create_act('res.partner', PORTAL_PARTNER_ID, AT_CALL,    '供應商年度評鑑電話',         d(4),  '與採購部門一起完成年度供應商評鑑')
create_act('res.partner', PORTAL_PARTNER_ID, AT_UPLOAD,  '上傳最新營業登記證',         d(3),  '營業登記證即將到期，請上傳更新版本')

# ══════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════
total = x('mail.activity', 'search_count', [[('user_id', '=', PORTAL_USER_ID)]])
print(f"\n{'=' * 60}")
print(f"DONE — {activity_count} notifications created")
print(f"Total activities for portal user: {total}")
print(f"{'=' * 60}")
print(f"\nPortal login:  portal / portal")
print(f"Admin login:   admin / admin")
print(f"URL:           http://localhost:9097")
