# POS Credit Sales - Ventas a Crédito para Odoo POS

## Descripción

Este módulo extiende el Punto de Venta (POS) de Odoo v17 para permitir ventas a crédito con selección de plazos de pago y aplicación automática del método de pago "Cuenta de Cliente".

## Características Principales

### 🏪 Configuración Flexible
- Habilitar/deshabilitar ventas a crédito por configuración de POS
- Selección de términos de pago disponibles
- Configuración de método de pago específico para crédito
- Validación opcional de límites de crédito de clientes

### 💳 Funcionalidad en POS
- Botón dedicado para iniciar venta a crédito
- Popup intuitivo para selección de plazos de pago
- Aplicación automática del método de pago configurado
- Validaciones en tiempo real de límites de crédito
- Indicadores visuales para ventas a crédito

### 📊 Gestión y Seguimiento
- Vista dedicada para ventas a crédito
- Filtros y agrupaciones por términos de pago
- Integración completa con facturación
- Validaciones automáticas durante el cierre de sesión

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar la lista de módulos
3. Instalar el módulo "POS Credit Sales"

```bash
# Desde línea de comandos
./odoo-bin -d tu_base_datos -i pos_credit --stop-after-init
```

## Configuración

### 1. Configurar Términos de Pago

Ir a **Contabilidad > Configuración > Términos de Pago**:

- Crear o editar términos de pago existentes
- Marcar "Disponible en POS" para hacerlos disponibles
- Configurar las líneas de pago con días y porcentajes

### 2. Configurar Métodos de Pago

Ir a **Punto de Venta > Configuración > Métodos de Pago**:

- El módulo crea automáticamente "Cuenta de Cliente"
- Verificar que esté asociado a un diario apropiado

### 3. Configurar POS

Ir a **Punto de Venta > Configuración > Puntos de Venta**:

1. Abrir la configuración del POS deseado
2. En la sección "Ventas a Crédito":
   - ✅ Marcar "Permitir Ventas a Crédito"
   - Seleccionar "Términos de Pago para Crédito"
   - Elegir "Método de Pago a Crédito"
   - Configurar opciones adicionales según necesidad

### 4. Configurar Clientes (Opcional)

Para validación de límites de crédito:

- Ir a **Contactos**
- Editar clientes que comprarán a crédito
- Establecer "Límite de Crédito" en la pestaña "Ventas y Compras"

## Uso

### En el POS

1. **Iniciar Venta a Crédito**:
   - Agregar productos al carrito
   - En la pantalla de pagos, hacer clic en "Venta a Crédito"

2. **Seleccionar Plazo**:
   - Se abre popup con términos disponibles
   - Seleccionar el plazo apropiado
   - Confirmar selección

3. **Finalizar Venta**:
   - El sistema aplica automáticamente el método "Cuenta de Cliente"
   - Validar la orden normalmente
   - Se genera factura con términos de pago

### Funciones Adicionales

- **Cancelar Crédito**: Botón para volver a venta normal
- **Indicadores Visuales**: La interfaz muestra claramente ventas a crédito
- **Validaciones**: El sistema previene errores comunes

## Estructura del Módulo

```
pos_credit/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── pos_config.py          # Configuración POS
│   ├── pos_order.py           # Órdenes y validaciones
│   ├── pos_session.py         # Sesiones y datos UI
│   └── account_payment_term.py # Términos de pago
├── views/
│   ├── pos_config_views.xml   # Vistas configuración
│   ├── pos_order_views.xml    # Vistas órdenes
│   └── account_payment_term_views.xml
├── static/src/
│   ├── js/
│   │   ├── models.js          # Modelos JS/OWL
│   │   ├── pos_store.js       # Store POS
│   │   ├── payment_screen.js  # Pantalla pagos
│   │   └── payment_term_popup.js # Popup términos
│   ├── xml/
│   │   ├── payment_screen.xml # Templates pantalla
│   │   └── payment_term_popup.xml # Templates popup
│   └── css/
│       └── pos_credit.css     # Estilos
├── data/
│   └── pos_payment_method_data.xml # Datos iniciales
├── demo/
│   └── pos_config_demo.xml    # Datos demo
├── security/
│   └── ir.model.access.csv    # Permisos
├── tests/
│   └── test_pos_credit.py     # Pruebas unitarias
├── migrations/
│   └── 17.0.1.0.0/
│       └── post-migration.py  # Scripts migración
└── README.md
```

## Flujo de Trabajo

### Venta Normal vs. Venta a Crédito

**Venta Normal**:
```
Productos → Pagos → Método de Pago → Validar
```

**Venta a Crédito**:
```
Productos → Crédito → Seleccionar Plazo → Auto-aplicar Método → Validar
```

### Validaciones Implementadas

1. **Configuración**:
   - POS debe permitir ventas a crédito
   - Términos de pago configurados
   - Método de pago configurado

2. **Cliente**:
   - Cliente requerido (configurable)
   - Límite de crédito (configurable)

3. **Orden**:
   - Término de pago válido
   - Método de pago correcto aplicado

## API y Extensiones

### Métodos Principales

```python
# Configuración POS
pos_config._get_credit_data_for_pos()

# Órdenes
pos_order.set_payment_term(term_id, term_name)
pos_order.validate_credit_order()
pos_order._validate_credit_limit(partner_id, amount)

# Términos de pago
payment_term.get_days_to_pay()
payment_term.is_immediate_payment()
```

### JavaScript/OWL

```javascript
// Store
pos.isCreditSalesEnabled()
pos.getAvailablePaymentTerms()
pos.getCreditPaymentMethod()

// Orden
order.set_payment_term(id, name)
order.is_credit_order()
order.apply_credit_payment_method()
```

## Resolución de Problemas

### Problemas Comunes

1. **Botón de crédito no aparece**:
   - Verificar que "Permitir Ventas a Crédito" está marcado
   - Confirmar que hay términos de pago configurados

2. **Error al validar orden**:
   - Verificar límite de crédito del cliente
   - Confirmar método de pago configurado

3. **Método de pago no se aplica**:
   - Verificar que "Cuenta de Cliente" está en métodos disponibles
   - Confirmar configuración en POS

### Logs y Depuración

El módulo registra información útil en la consola del navegador:

```javascript
console.log('Credit config loaded:', {
    allow_credit_sales: true,
    payment_terms: 3,
    credit_payment_method: "Cuenta de Cliente"
});
```

## Compatibilidad

- **Odoo Version**: 17.0
- **Dependencias**: `point_of_sale`, `account`
- **Navegadores**: Chrome, Firefox, Safari (últimas versiones)

## Soporte y Contribuciones

Para reportar errores o solicitar características:

1. Revisar la documentación y configuración
2. Verificar logs de Odoo y consola del navegador
3. Crear issue con pasos para reproducir el problema

## Licencia

LGPL-3 - Ver archivo LICENSE para detalles.

## Changelog

### v17.0.1.0.0
- ✨ Implementación inicial
- 🔧 Configuración flexible de términos de pago
- 💡 Interface intuitiva con popup de selección
- ✅ Validaciones completas de límites de crédito
- 📊 Vistas dedicadas para seguimiento
- 🧪 Suite completa de pruebas unitarias