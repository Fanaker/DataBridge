"""A lightweight but real and idempotent data quality pipeline."""
from __future__ import annotations
import csv, io, json, sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT/'data'/'databridge.sqlite3'
RAW = ROOT/'data'/'raw'
SCHEMA='''
CREATE TABLE IF NOT EXISTS products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, cost REAL NOT NULL, price REAL NOT NULL);
CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, order_date TEXT NOT NULL, sku TEXT NOT NULL REFERENCES products(sku), quantity INTEGER NOT NULL, unit_price REAL NOT NULL, channel TEXT NOT NULL, customer_id TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS ix_orders_source ON orders(source);
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, source TEXT NOT NULL, read_count INT NOT NULL, accepted INT NOT NULL, duplicates INT NOT NULL, rejected INT NOT NULL, duration_ms INT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rejects (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INT REFERENCES runs(id), row_number INT, order_id TEXT, reason TEXT NOT NULL, raw_json TEXT NOT NULL);
'''
def connect():
 DB.parent.mkdir(parents=True,exist_ok=True)
 cx=sqlite3.connect(DB);cx.row_factory=sqlite3.Row;cx.execute('PRAGMA foreign_keys=ON');cx.executescript(SCHEMA);return cx

def initialize_products(cx):
 with (RAW/'products.csv').open(newline='',encoding='utf8') as f:
  for p in csv.DictReader(f):
   cx.execute('INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)',(p['sku'],p['product_name'],p['category'],float(p['unit_cost']),float(p['list_price'])))

def validate(row:dict,known:set):
 oid=str(row.get('order_id','')).strip();sku=str(row.get('sku','')).strip()
 if not oid: return 'ID de pedido vacío'
 if sku not in known:return 'SKU no encontrado en catálogo'
 try:datetime.strptime(str(row.get('order_date','')), '%Y-%m-%d %H:%M:%S')
 except (ValueError,TypeError):return 'Fecha inválida'
 try:
  qty=Decimal(str(row.get('quantity',''))); price=Decimal(str(row.get('unit_price','')))
  if qty != qty.to_integral_value() or qty<=0 or qty>10000:return 'Cantidad fuera de rango'
  if not price.is_finite() or price<=0 or price>100000:return 'Precio fuera de rango'
 except (ValueError,InvalidOperation):return 'Cantidad o precio no numérico'
 if str(row.get('channel','')).strip() not in {'Tienda','Online','WhatsApp','Marketplace'}:return 'Canal desconocido'
 if not str(row.get('customer_id','')).strip():return 'Cliente vacío'
 return None

def ingest(rows:Iterable[dict], source='POS / CSV'):
 import time
 started=time.monotonic();ts=datetime.now().isoformat(timespec='seconds')
 with connect() as cx:
  initialize_products(cx)
  known={x[0] for x in cx.execute('SELECT sku FROM products')}
  cx.execute('INSERT INTO runs(started_at,source,read_count,accepted,duplicates,rejected,duration_ms,status) VALUES (?,?,?,?,?,?,?,?)',(ts,source,0,0,0,0,0,'Ejecutando'))
  run_id=cx.execute('SELECT last_insert_rowid()').fetchone()[0]
  read=accepted=duplicates=rejected=0
  for index,row in enumerate(rows,start=2):
   read+=1;problem=validate(row,known)
   if problem:
    rejected+=1
    cx.execute('INSERT INTO rejects(run_id,row_number,order_id,reason,raw_json) VALUES(?,?,?,?,?)',(run_id,index,str(row.get('order_id','')),problem,json.dumps(row,ensure_ascii=False)))
    continue
   try:
    cx.execute('INSERT INTO orders(order_id,order_date,sku,quantity,unit_price,channel,customer_id,source) VALUES(?,?,?,?,?,?,?,?)',(row['order_id'].strip(),row['order_date'],row['sku'].strip(),int(row['quantity']),float(row['unit_price']),row['channel'].strip(),row['customer_id'].strip(),source))
    accepted+=1
   except sqlite3.IntegrityError:
    duplicates+=1
  elapsed=max(1,round((time.monotonic()-started)*1000))
  cx.execute('UPDATE runs SET read_count=?,accepted=?,duplicates=?,rejected=?,duration_ms=?,status=? WHERE id=?',(read,accepted,duplicates,rejected,elapsed,'Completado' if rejected==0 else 'Completado con alertas',run_id))
  return {'run_id':run_id,'read_count':read,'accepted':accepted,'duplicates':duplicates,'rejected':rejected,'duration_ms':elapsed}

def run_pos(file_content:bytes|None=None):
 if file_content is None:file_content=(RAW/'pos_orders.csv').read_bytes()
 reader=csv.DictReader(io.StringIO(file_content.decode('utf-8-sig')))
 required={'order_id','order_date','sku','quantity','unit_price','channel','customer_id'}
 if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
  raise ValueError('Columnas CSV requeridas: '+', '.join(sorted(required)))
 return ingest(reader,'POS / CSV')

def run_partner():
 return ingest(json.loads((RAW/'partner_feed.json').read_text(encoding='utf8')),'Partner / JSON API')

def seed():
 with connect() as cx:
  initialize_products(cx)
  has_runs=cx.execute('SELECT COUNT(*) FROM runs').fetchone()[0]
 if not has_runs:
  run_pos();run_partner()

def select(query,args=()):
 with connect() as cx:return [dict(x) for x in cx.execute(query,args).fetchall()]

if __name__=='__main__':
 seed();print('pipeline initialized',DB)
