"""Reproducible synthetic retail feeds with intentionally dirty rows."""
from pathlib import Path
from datetime import datetime, timedelta
import csv, random, json
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'raw';OUT.mkdir(parents=True,exist_ok=True)
r=random.Random(607)
products=[('PRD-%03d'%i, name, group, round(cost,2), round(price,2)) for i,(name,group,cost,price) in enumerate([
 ('Café molido 250g','Abarrotes',12,19.9),('Arroz extra 1kg','Abarrotes',3.4,5.5),('Aceite vegetal 1L','Abarrotes',6.3,10.5),('Azúcar rubia 1kg','Abarrotes',2.9,4.4),('Leche evaporada','Lácteos',3.1,4.8),('Yogur natural 1L','Lácteos',6.8,10.0),('Queso fresco 500g','Lácteos',11.9,17.5),('Mantequilla 200g','Lácteos',7.3,12.5),('Papel toalla x2','Hogar',7.7,12.9),('Detergente 900g','Hogar',8.2,14.5),('Lavavajillas 750ml','Hogar',4.5,7.9),('Desinfectante 1L','Hogar',5.8,9.9),('Gaseosa 1.5L','Bebidas',5.1,8.5),('Agua mineral 625ml','Bebidas',1.4,2.8),('Jugo de naranja 1L','Bebidas',5.4,9.9),('Bebida energética','Bebidas',4.5,8.9),('Galletas integrales','Snacks',2.5,5.2),('Papas crocantes','Snacks',2.8,5.9),('Chocolate 80g','Snacks',3.0,6.7),('Mix de frutos secos','Snacks',6.4,11.9),('Shampoo 400ml','Cuidado',12,21.9),('Jabón líquido','Cuidado',7.9,13.9),('Pasta dental','Cuidado',4.9,8.9),('Pañitos húmedos','Cuidado',5.3,9.5)
],start=1)]
with (OUT/'products.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['sku','product_name','category','unit_cost','list_price']);w.writerows(products)
headers=['order_id','order_date','sku','quantity','unit_price','channel','customer_id','source']
rows=[];start=datetime(2026,7,1)
for i in range(1,1451):
 p=r.choice(products);q=r.randint(1,5);date=start+timedelta(days=r.randint(0,122),hours=r.randint(8,21),minutes=r.randint(0,59))
 rows.append([f'ORD-{i:06d}',date.strftime('%Y-%m-%d %H:%M:%S'),p[0],q,p[4],r.choice(['Tienda','Online','WhatsApp']),f'CLI-{r.randrange(1,270):04d}','pos'])
rows.extend([list(rows[i]) for i in [18,91,310,499,925]])
rows.extend([
 ['ORD-009990','2026-09-21 12:30:00','PRD-999',2,'10.50','Tienda','CLI-0045','pos'],
 ['ORD-009991','fecha-invalida','PRD-003',3,'10.50','Online','CLI-0045','pos'],
 ['ORD-009992','2026-09-21 12:30:00','PRD-012',-2,'9.90','Tienda','CLI-0045','pos'],
 ['ORD-009993','2026-09-21 12:30:00','PRD-014',2,'texto','Tienda','CLI-0045','pos']])
r.shuffle(rows)
with (OUT/'pos_orders.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(headers);w.writerows(rows)
partner=[]
for i in range(1451,1531):
 p=r.choice(products);date=start+timedelta(days=r.randint(30,122),hours=r.randint(9,20))
 partner.append(dict(zip(headers,[f'ORD-{i:06d}',date.strftime('%Y-%m-%d %H:%M:%S'),p[0],r.randint(1,4),p[4],'Marketplace',f'CLI-{r.randrange(1,270):04d}','partner_api'])))
partner.append(dict(partner[4])); partner.append({**partner[3],'order_id':'ORD-009994','quantity':0})
(OUT/'partner_feed.json').write_text(json.dumps(partner,ensure_ascii=False,indent=2),encoding='utf8')
print('Generated',len(rows),'CSV rows and',len(partner),'API feed records')
