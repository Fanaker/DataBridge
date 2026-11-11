# Diccionario de datos

**Fuente de prueba:** negocio ficticio Northstar Retail. Registros generados por `tools/generate_data.py`, semilla fija, julio–octubre de 2026.

## `products`

| Campo | Tipo | Descripción |
|---|---|---|
| `sku` | TEXT, PK | Identificador único del producto |
| `name` | TEXT | Nombre comercial |
| `category` | TEXT | Grupo de productos |
| `cost` | REAL | Costo unitario |
| `price` | REAL | Precio de lista |

## `orders`

| Campo | Tipo | Descripción |
|---|---|---|
| `order_id` | TEXT, PK | ID global para deduplicación |
| `order_date` | TEXT | Fecha/hora formato ISO, ordenable |
| `sku` | TEXT, FK | Producto (referencia a `products`) |
| `quantity` | INTEGER | Cantidad positiva |
| `unit_price` | REAL | Precio unitario del pedido |
| `channel` | TEXT | Tienda, Online, WhatsApp, Marketplace |
| `customer_id` | TEXT | Cliente pseudónimo generado |
| `source` | TEXT | Fuente de ingesta |
| `created_at` | TEXT | Hora de carga a la base |

## `runs` y `rejects`

`runs` registra ID de ejecución, fuente, lecturas, aceptados, duplicados, rechazados, duración y estado. `rejects` conserva ID de run, número de fila, ID de pedido, motivo y registro crudo JSON.

**Nota:** las cifras de negocio son sintéticas, se calculan desde los registros validados y no deben interpretarse como ingresos reales de ningún comercio.
