from pathlib import Path
import csv, io
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .pipeline import ROOT,seed,connect,select,run_pos,run_partner

app=FastAPI(title='DataBridge API',version='1.0.0',description='Retail data ingestion & quality control')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['GET','POST'],allow_headers=['*'])
@app.on_event('startup')
def startup(): seed()

@app.get('/api/overview')
def overview():
 with connect() as cx:
  q=lambda s:cx.execute(s).fetchone()[0]
  runs=[dict(r) for r in cx.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 8')]
  trend=[dict(x) for x in cx.execute("SELECT substr(order_date,1,7) period, ROUND(SUM(quantity*unit_price),2) value, COUNT(*) orders FROM orders GROUP BY 1 ORDER BY 1")]
  sources=[dict(x) for x in cx.execute('SELECT source,COUNT(*) records FROM orders GROUP BY source ORDER BY records DESC')]
  categories=[dict(x) for x in cx.execute('SELECT p.category name,COUNT(*) orders,ROUND(SUM(o.quantity*o.unit_price),2) revenue FROM orders o JOIN products p ON o.sku=p.sku GROUP BY 1 ORDER BY revenue DESC')]
  return {'metrics':{'rows':q('SELECT COUNT(*) FROM orders'),'products':q('SELECT COUNT(*) FROM products'),'runs':q('SELECT COUNT(*) FROM runs'),'rejected':q('SELECT COUNT(*) FROM rejects'),'duplicates':q('SELECT COALESCE(SUM(duplicates),0) FROM runs'),'revenue':round(q('SELECT COALESCE(SUM(quantity*unit_price),0) FROM orders'),2)},'runs':runs,'trend':trend,'sources':sources,'categories':categories}
@app.get('/api/quality')
def quality():
 return {'reasons':select('SELECT reason,COUNT(*) count FROM rejects GROUP BY 1 ORDER BY count DESC'),'rejects':select('SELECT id,run_id,row_number,order_id,reason FROM rejects ORDER BY id DESC LIMIT 80'),'runs':select('SELECT id,started_at,source,read_count,accepted,duplicates,rejected FROM runs ORDER BY id DESC LIMIT 30')}
@app.get('/api/orders')
def orders():
 return {'orders':select('SELECT o.order_id,o.order_date,p.name product,p.category,o.quantity,o.unit_price,ROUND(o.quantity*o.unit_price,2) total,o.channel,o.source FROM orders o JOIN products p ON o.sku=p.sku ORDER BY o.order_date DESC LIMIT 160')}
@app.get('/api/catalog')
def catalog():return {'products':select('SELECT sku,name,category,cost,price FROM products ORDER BY category,name')}
@app.get('/api/schema')
def schema():
 return {'tables':[{'name':'stg_pos_orders','columns':8,'role':'Fuente CSV'},{'name':'stg_partner_api','columns':8,'role':'Fuente JSON'},{'name':'products','columns':5,'role':'Dimensión'},{'name':'orders','columns':9,'role':'Hechos'},{'name':'runs','columns':9,'role':'Auditoría'},{'name':'rejects','columns':6,'role':'Calidad'}]}
@app.post('/api/pipelines/pos')
def execute_pos():return run_pos()
@app.post('/api/pipelines/partner')
def execute_partner():return run_partner()
@app.post('/api/pipelines/upload')
async def upload(file:UploadFile=File(...)):
 if not file.filename or not file.filename.lower().endswith('.csv'):raise HTTPException(400,'Solo CSV')
 content=await file.read()
 if len(content)>5_000_000:raise HTTPException(413,'Archivo demasiado grande')
 try:return run_pos(content)
 except (ValueError,UnicodeError,csv.Error) as exc:raise HTTPException(422,str(exc))
@app.get('/api/export/orders.csv')
def export_orders():
 records=select('SELECT * FROM orders ORDER BY order_date')
 stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=records[0].keys() if records else ['order_id']);writer.writeheader();writer.writerows(records)
 return Response(stream.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=databridge_clean_orders.csv'})
@app.get('/api/export/rejects.csv')
def export_rejects():
 records=select('SELECT run_id,row_number,order_id,reason,raw_json FROM rejects ORDER BY id')
 stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=records[0].keys() if records else ['run_id']);writer.writeheader();writer.writerows(records)
 return Response(stream.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=databridge_rejects.csv'})
@app.get('/api/health')
def health():return {'status':'ok'}
app.mount('/',StaticFiles(directory=ROOT/'frontend',html=True),name='frontend')
