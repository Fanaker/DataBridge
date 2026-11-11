import sqlite3
from app.pipeline import validate,run_pos,run_partner,connect,seed,RAW
from app.main import app
from fastapi.testclient import TestClient

def test_invalid_sku():
 assert 'SKU' in validate(dict(order_id='x',sku='?',order_date='2026-10-01 12:00:00',quantity=1,unit_price=5,channel='Tienda',customer_id='c'),{'PRD-001'})
def test_invalid_quantity():
 assert 'Cantidad' in validate(dict(order_id='x',sku='PRD-001',order_date='2026-10-01 12:00:00',quantity=-2,unit_price=5,channel='Tienda',customer_id='c'),{'PRD-001'})
def test_idempotent_import():
 seed();before=connect().execute('SELECT COUNT(*) FROM orders').fetchone()[0];result=run_pos();after=connect().execute('SELECT COUNT(*) FROM orders').fetchone()[0]
 assert before==after and result['accepted']==0 and result['duplicates']>=1400

def test_api_data():
 with TestClient(app) as c:
  r=c.get('/api/overview');assert r.status_code==200;assert r.json()['metrics']['rows']>=1400
  assert c.get('/api/quality').status_code==200
  assert c.get('/api/export/orders.csv').text.startswith('order_id,')
