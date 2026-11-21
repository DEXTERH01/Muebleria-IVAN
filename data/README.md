# Datos del proyecto

Los conjuntos de datos controlados para pruebas y ML vivirán en subcarpetas documentadas. No se almacenarán datos personales, exportaciones de producción ni secretos en Git.

## Dataset sintético `orders_v1.csv`

`synthetic/orders_v1.csv` contiene exactamente 500 pedidos anónimos marcados como datos de prueba. Se regenera con semilla `2026` mediante:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\generate_ml_dataset.py
```

Las columnas de entrada representan dimensiones en milímetros, importes en céntimos, configuración del mueble, carga del taller y resumen RFM del cliente. Los objetivos son `production_days` para regresión e `is_delayed` para clasificación. `customer_recency_days`, `customer_frequency`, `customer_total_spend_minor`, `customer_avg_ticket_minor` y `categories_bought` alimentan exclusivamente el clustering descriptivo.

Los identificadores `SYN-*` y `CUS-*` son artificiales. El archivo no contiene nombres, correos, teléfonos, direcciones ni exportaciones operativas.

