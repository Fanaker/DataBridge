"""Optional one-way export of the validated local warehouse to PostgreSQL."""
import os,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.pipeline import connect,seed

def main():
 try:import psycopg
 except ImportError:raise SystemExit('Install: pip install psycopg[binary]')
 seed()
 dsn=os.getenv('DATABASE_URL','postgresql://databridge:localdemo@localhost:5434/databridge')
 with connect() as src,psycopg.connect(dsn) as dst:
  with dst.cursor() as cur:
   for p in src.execute('SELECT sku,name,category,cost,price FROM products'):
    cur.execute('INSERT INTO databridge.products(sku,name,category,cost,price) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(sku) DO UPDATE SET name=EXCLUDED.name,category=EXCLUDED.category,cost=EXCLUDED.cost,price=EXCLUDED.price',tuple(p))
   for o in src.execute('SELECT order_id,order_date,sku,quantity,unit_price,channel,customer_id,source FROM orders'):
    cur.execute('INSERT INTO databridge.orders(order_id,order_date,sku,quantity,unit_price,channel,customer_id,source) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(order_id) DO NOTHING',tuple(o))
  dst.commit()
 print('Warehouse synchronized to PostgreSQL')
if __name__=='__main__':main()
