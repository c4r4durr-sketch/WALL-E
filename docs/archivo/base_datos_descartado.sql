-- =====================================================================
-- ARCHIVO DESCARTADO - NO EJECUTAR
-- =====================================================================
-- Primer diseño del esquema en SQL puro. Se descartó porque sus tablas
-- (sucursales, herramientas, ...) no coinciden con las que genera Django
-- (usuarios_sucursal, catalogo_herramienta, ...): ejecutarlo crearía un
-- segundo esquema paralelo que la aplicación nunca usaría. Además empieza
-- con DROP SCHEMA public CASCADE, que BORRA toda la base.
--
-- La única fuente de verdad del esquema son los modelos y migraciones de
-- Django. Lo que este script resolvía en SQL ahora vive en Python:
--   fn_calcular_eoq / fn_calcular_rop / fn_ajustar_a_cajas
--       -> backend/apps/indicadores/domain/formulas.py
--   fn_registrar_historial (HU13, trigger de auditoría)
--       -> backend/apps/auditoria (signals de Django + tabla ORM)
--
-- Se conserva solo como referencia de las reglas de negocio originales.
-- =====================================================================

-- ====
-- BASE DE DATOS: Walle-Importaciones
-- Sistema de seguimiento de inventarios multisucursal
-- Universidad Privada Franz Tamayo - Ing. de Sistemas
-- Motor: PostgreSQL 14+
-- ====
-- ====
-- 0. EXTENSIONES Y LIMPIEZA
-- ====
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; 

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE rol_usuario AS ENUM ('ADMINISTRADOR', 'SUPERVISOR', 'EMPLEADO');

CREATE TYPE tipo_movimiento AS ENUM (
    'ENTRADA',               
    'SALIDA',                
    'TRANSFERENCIA_SALIDA',  
    'TRANSFERENCIA_ENTRADA', 
    'AJUSTE'                 
);

-- HU13: tipo de acción para el log de auditoría
CREATE TYPE accion_auditoria AS ENUM ('INSERT', 'UPDATE', 'DELETE');

CREATE SEQUENCE seq_sucursales;

CREATE TABLE sucursales (
    cod_sucursal    VARCHAR(8) PRIMARY KEY DEFAULT ('su-' || LPAD(NEXTVAL('seq_sucursales')::TEXT, 5, '0')),
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    direccion       VARCHAR(255),
    telefono        VARCHAR(30),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE sucursales IS 'Sucursales físicas de Walle-Importaciones (actualmente 2)';


CREATE SEQUENCE seq_usuarios;

CREATE TABLE usuarios (
    cod_usuario         VARCHAR(8) PRIMARY KEY DEFAULT ('us-' || LPAD(NEXTVAL('seq_usuarios')::TEXT, 5, '0')),
    nombre_completo     VARCHAR(150) NOT NULL,
    nombre_usuario      VARCHAR(50)  NOT NULL UNIQUE,
    contrasena          VARCHAR(255) NOT NULL,         
    rol                 rol_usuario  NOT NULL,          
    cod_sucursal        VARCHAR(8) REFERENCES sucursales(cod_sucursal) ON DELETE RESTRICT, -- HU5
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    cod_creado_por      VARCHAR(8) REFERENCES usuarios(cod_usuario), 
    creado_en           TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en      TIMESTAMP NOT NULL DEFAULT NOW(),

    
    CONSTRAINT chk_sucursal_obligatoria CHECK (
        (rol = 'ADMINISTRADOR') OR (cod_sucursal IS NOT NULL)
    )
);
COMMENT ON TABLE usuarios IS 'Cuentas del sistema; solo el Administrador puede crearlas (HU4)';
COMMENT ON COLUMN usuarios.contrasena IS 'Guardar aquí el hash (bcrypt/argon2), nunca la contraseña en texto plano; HU3 permite al admin resetearla';

-- HU1, HU2: bitácora de inicio/cierre de sesión (control de acceso a mostradores)
CREATE SEQUENCE seq_sesiones_usuario;

CREATE TABLE sesiones_usuario (
    cod_sesion      VARCHAR(8) PRIMARY KEY DEFAULT ('se-' || LPAD(NEXTVAL('seq_sesiones_usuario')::TEXT, 5, '0')),
    cod_usuario     VARCHAR(8) NOT NULL REFERENCES usuarios(cod_usuario),
    inicio_sesion   TIMESTAMP NOT NULL DEFAULT NOW(),   -- HU1
    cierre_sesion   TIMESTAMP,                          -- HU2
    direccion_ip    VARCHAR(45)
);
COMMENT ON TABLE sesiones_usuario IS 'HU1 inicio de sesión / HU2 cierre de sesión';

CREATE SEQUENCE seq_proveedores;

CREATE TABLE proveedores (
    cod_proveedor           VARCHAR(8) PRIMARY KEY DEFAULT ('pr-' || LPAD(NEXTVAL('seq_proveedores')::TEXT, 5, '0')),
    nombre_empresa          VARCHAR(150) NOT NULL,
    nombre_contacto         VARCHAR(150),
    telefono                VARCHAR(30),
    email                   VARCHAR(150),
    direccion               VARCHAR(255),
    tiempo_entrega_dias     INTEGER CHECK (tiempo_entrega_dias >= 0), -- HU16: días que tarda en llegar un pedido
    activo                  BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE proveedores IS 'HU8 directorio de proveedores; tiempo_entrega_dias soporta HU16 (ROP)';


CREATE SEQUENCE seq_herramientas;

CREATE TABLE herramientas (
    cod_herramienta                 VARCHAR(8) PRIMARY KEY DEFAULT ('he-' || LPAD(NEXTVAL('seq_herramientas')::TEXT, 5, '0')),
    codigo_caja                     VARCHAR(50)  NOT NULL UNIQUE,   
    nombre                          VARCHAR(150) NOT NULL,          
    modelo                          VARCHAR(100),                   
    cod_proveedor                   VARCHAR(8) REFERENCES proveedores(cod_proveedor),
    costo_unitario                  NUMERIC(12,2) NOT NULL CHECK (costo_unitario >= 0),
    unidades_por_caja               INTEGER NOT NULL DEFAULT 1 CHECK (unidades_por_caja > 0),

   
    demanda_anual_estimada          NUMERIC(12,2) CHECK (demanda_anual_estimada >= 0),     
    costo_fijo_pedido               NUMERIC(12,2) CHECK (costo_fijo_pedido >= 0),            
    costo_almacenamiento_unitario   NUMERIC(12,2) CHECK (costo_almacenamiento_unitario >= 0),

    
    tiempo_entrega_dias             INTEGER CHECK (tiempo_entrega_dias >= 0),

    
    dias_para_estancamiento         INTEGER NOT NULL DEFAULT 40,

    activo                          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en                       TIMESTAMP NOT NULL DEFAULT NOW(),
    actualizado_en                  TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE herramientas IS 'HU6 catálogo, HU7 precios, HU15 costos EOQ, HU26 conversión caja-unidad';
COMMENT ON COLUMN herramientas.unidades_por_caja IS 'HU26: ej. 1 caja = 12 unidades; aísla la conversión matemática';


CREATE SEQUENCE seq_inventario_sucursal;

CREATE TABLE inventario_sucursal (
    cod_inventario      VARCHAR(8) PRIMARY KEY DEFAULT ('in-' || LPAD(NEXTVAL('seq_inventario_sucursal')::TEXT, 5, '0')),
    cod_herramienta     VARCHAR(8) NOT NULL REFERENCES herramientas(cod_herramienta),
    cod_sucursal        VARCHAR(8) NOT NULL REFERENCES sucursales(cod_sucursal),
    stock_unidades      INTEGER NOT NULL DEFAULT 0 CHECK (stock_unidades >= 0),
    fecha_ultima_salida DATE,                        -- HU22: base del reporte de antigüedad
    en_promocion        BOOLEAN NOT NULL DEFAULT FALSE, -- HU23: etiquetado visual de promoción
    actualizado_en      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (cod_herramienta, cod_sucursal)
);
COMMENT ON TABLE inventario_sucursal IS 'HU11 consulta de stock global; HU22/HU23 estancamiento y promoción';


CREATE SEQUENCE seq_movimientos_inventario;

CREATE TABLE movimientos_inventario (
    cod_movimiento          VARCHAR(8) PRIMARY KEY DEFAULT ('mo-' || LPAD(NEXTVAL('seq_movimientos_inventario')::TEXT, 5, '0')),
    cod_herramienta         VARCHAR(8) NOT NULL REFERENCES herramientas(cod_herramienta),
    cod_sucursal            VARCHAR(8) NOT NULL REFERENCES sucursales(cod_sucursal), -- sucursal donde ocurre el movimiento
    tipo_movimiento         tipo_movimiento NOT NULL,
    cantidad_unidades       INTEGER NOT NULL CHECK (cantidad_unidades > 0),
    cantidad_cajas          NUMERIC(10,2),              
  
    cod_sucursal_destino    VARCHAR(8) REFERENCES sucursales(cod_sucursal),
    cod_autorizado_por      VARCHAR(8) REFERENCES usuarios(cod_usuario), 

    
    cod_proveedor           VARCHAR(8) REFERENCES proveedores(cod_proveedor),
    referencia_lote         VARCHAR(100),

    cod_usuario             VARCHAR(8) NOT NULL REFERENCES usuarios(cod_usuario), -- quién registró el movimiento
    fecha_movimiento        TIMESTAMP NOT NULL DEFAULT NOW(),
    observaciones           TEXT,

    CONSTRAINT chk_transferencia_destino CHECK (
        (tipo_movimiento IN ('TRANSFERENCIA_SALIDA', 'TRANSFERENCIA_ENTRADA') AND cod_sucursal_destino IS NOT NULL)
        OR (tipo_movimiento NOT IN ('TRANSFERENCIA_SALIDA', 'TRANSFERENCIA_ENTRADA') AND cod_sucursal_destino IS NULL)
    ),
    CONSTRAINT chk_destino_distinto_origen CHECK (
        cod_sucursal_destino IS NULL OR cod_sucursal_destino <> cod_sucursal
    )
);
COMMENT ON TABLE movimientos_inventario IS 'HU9 registro de movimientos, HU10 ingreso masivo, HU12 transferencias';
CREATE INDEX idx_movimientos_herramienta ON movimientos_inventario(cod_herramienta);
CREATE INDEX idx_movimientos_sucursal_fecha ON movimientos_inventario(cod_sucursal, fecha_movimiento);

-- HU13: historial oculto de modificaciones (auditoría genérica multi-tabla)
CREATE SEQUENCE seq_historial_modificaciones;

CREATE TABLE historial_modificaciones (
    cod_historial       VARCHAR(8) PRIMARY KEY DEFAULT ('hi-' || LPAD(NEXTVAL('seq_historial_modificaciones')::TEXT, 5, '0')),
    tabla_afectada      VARCHAR(50) NOT NULL,
    cod_registro        VARCHAR(8) NOT NULL,
    cod_usuario         VARCHAR(8) REFERENCES usuarios(cod_usuario),
    accion              accion_auditoria NOT NULL,
    datos_anteriores    JSONB,
    datos_nuevos        JSONB,
    fecha               TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE historial_modificaciones IS 'HU13: log oculto de quién y cuándo edita un registro';
CREATE INDEX idx_historial_tabla_registro ON historial_modificaciones(tabla_afectada, cod_registro);

-- =====================================================================
-- 5. MÓDULO: ASISTENTE DE COMPRAS - EOQ / ROP (HU17-HU21)
-- =====================================================================

-- HU17-HU21: snapshot histórico de cada cálculo, para trazar sugerencias y alertas
CREATE SEQUENCE seq_calculo_eoq_rop;

CREATE TABLE calculo_eoq_rop (
    cod_calculo                 VARCHAR(8) PRIMARY KEY DEFAULT ('ca-' || LPAD(NEXTVAL('seq_calculo_eoq_rop')::TEXT, 5, '0')),
    cod_herramienta             VARCHAR(8) NOT NULL REFERENCES herramientas(cod_herramienta),
    fecha_calculo               TIMESTAMP NOT NULL DEFAULT NOW(),
    demanda_anual_usada         NUMERIC(12,2) NOT NULL,   -- HU21: puede actualizarse según ventas recientes
    eoq_calculado                NUMERIC(12,2) NOT NULL,   -- HU17: cantidad ideal (unidades)
    eoq_ajustado_cajas          NUMERIC(12,2),             -- HU20: redondeado a cajas cerradas
    rop_calculado               NUMERIC(12,2),             -- HU18: punto de reorden
    stock_al_momento            INTEGER,                   -- stock consolidado al calcular
    alerta_generada             BOOLEAN NOT NULL DEFAULT FALSE, -- HU18: stock <= ROP
    cantidad_sugerida_pedido    NUMERIC(12,2)              -- HU19: sugerencia final al proveedor
);
COMMENT ON TABLE calculo_eoq_rop IS 'HU17 EOQ, HU18 alerta ROP, HU19 sugerencia de pedido, HU20 ajuste por caja, HU21 tendencia';
CREATE INDEX idx_eoq_rop_herramienta_fecha ON calculo_eoq_rop(cod_herramienta, fecha_calculo);

-- =====================================================================
-- 6. MÓDULO: REPORTES Y AUDITORÍA (HU14, HU22, HU23, HU24, HU25)
-- =====================================================================
-- (HU14 cierre diario, HU22 antigüedad y HU24 panel se resuelven con VISTAS
--  en la sección 8, ya que son datos derivados y no deben duplicarse.
--  HU23 etiquetado ya está en inventario_sucursal.en_promocion.
--  HU25 "descarga en Excel" es una función de la capa de aplicación,
--  que exporta el resultado de las vistas/consultas de este script.)

-- =====================================================================
-- 7. FUNCIONES Y TRIGGERS
-- =====================================================================

-- 7.1 Actualiza automáticamente "actualizado_en" en cada UPDATE
CREATE OR REPLACE FUNCTION fn_set_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_usuarios_actualizado_en
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_set_actualizado_en();

CREATE TRIGGER trg_herramientas_actualizado_en
    BEFORE UPDATE ON herramientas
    FOR EACH ROW EXECUTE FUNCTION fn_set_actualizado_en();

-- 7.2 HU13: auditoría genérica -- registra INSERT/UPDATE/DELETE en historial_modificaciones
-- Como cada tabla auditada tiene su propio nombre de llave primaria (cod_herramienta,
-- cod_inventario, cod_usuario), el código de registro se extrae dinámicamente vía
-- to_jsonb() según la tabla de origen (TG_TABLE_NAME).
CREATE OR REPLACE FUNCTION fn_registrar_historial()
RETURNS TRIGGER AS $$
DECLARE
    v_cod_usuario VARCHAR(8) := NULLIF(current_setting('app.usuario_actual', TRUE), '');
    v_cod_registro VARCHAR(8);
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_cod_registro := CASE TG_TABLE_NAME
            WHEN 'herramientas' THEN to_jsonb(OLD)->>'cod_herramienta'
            WHEN 'inventario_sucursal' THEN to_jsonb(OLD)->>'cod_inventario'
            WHEN 'usuarios' THEN to_jsonb(OLD)->>'cod_usuario'
        END;
    ELSE
        v_cod_registro := CASE TG_TABLE_NAME
            WHEN 'herramientas' THEN to_jsonb(NEW)->>'cod_herramienta'
            WHEN 'inventario_sucursal' THEN to_jsonb(NEW)->>'cod_inventario'
            WHEN 'usuarios' THEN to_jsonb(NEW)->>'cod_usuario'
        END;
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO historial_modificaciones(tabla_afectada, cod_registro, cod_usuario, accion, datos_nuevos)
        VALUES (TG_TABLE_NAME, v_cod_registro, v_cod_usuario, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO historial_modificaciones(tabla_afectada, cod_registro, cod_usuario, accion, datos_anteriores, datos_nuevos)
        VALUES (TG_TABLE_NAME, v_cod_registro, v_cod_usuario, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO historial_modificaciones(tabla_afectada, cod_registro, cod_usuario, accion, datos_anteriores)
        VALUES (TG_TABLE_NAME, v_cod_registro, v_cod_usuario, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION fn_registrar_historial IS
    'HU13: la app debe ejecutar SET app.usuario_actual = ''<cod_usuario>''; antes de cada operación para identificar al autor';

CREATE TRIGGER trg_auditoria_herramientas
    AFTER INSERT OR UPDATE OR DELETE ON herramientas
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_historial();

CREATE TRIGGER trg_auditoria_inventario
    AFTER INSERT OR UPDATE OR DELETE ON inventario_sucursal
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_historial();

CREATE TRIGGER trg_auditoria_usuarios
    AFTER UPDATE OR DELETE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_registrar_historial();

-- 7.3 HU9, HU10, HU12: actualiza inventario_sucursal automáticamente al registrar un movimiento
CREATE OR REPLACE FUNCTION fn_aplicar_movimiento_inventario()
RETURNS TRIGGER AS $$
BEGIN
    -- Asegura que exista la fila de stock para herramienta+sucursal
    INSERT INTO inventario_sucursal (cod_herramienta, cod_sucursal, stock_unidades)
    VALUES (NEW.cod_herramienta, NEW.cod_sucursal, 0)
    ON CONFLICT (cod_herramienta, cod_sucursal) DO NOTHING;

    IF NEW.cod_sucursal_destino IS NOT NULL THEN
        INSERT INTO inventario_sucursal (cod_herramienta, cod_sucursal, stock_unidades)
        VALUES (NEW.cod_herramienta, NEW.cod_sucursal_destino, 0)
        ON CONFLICT (cod_herramienta, cod_sucursal) DO NOTHING;
    END IF;

    IF NEW.tipo_movimiento = 'ENTRADA' THEN
        UPDATE inventario_sucursal
           SET stock_unidades = stock_unidades + NEW.cantidad_unidades,
               actualizado_en = NOW()
         WHERE cod_herramienta = NEW.cod_herramienta AND cod_sucursal = NEW.cod_sucursal;

    ELSIF NEW.tipo_movimiento = 'SALIDA' THEN
        UPDATE inventario_sucursal
           SET stock_unidades = stock_unidades - NEW.cantidad_unidades,
               fecha_ultima_salida = CURRENT_DATE,   -- HU22: reinicia el conteo de antigüedad
               actualizado_en = NOW()
         WHERE cod_herramienta = NEW.cod_herramienta AND cod_sucursal = NEW.cod_sucursal;

    ELSIF NEW.tipo_movimiento = 'TRANSFERENCIA_SALIDA' THEN
        UPDATE inventario_sucursal
           SET stock_unidades = stock_unidades - NEW.cantidad_unidades,
               actualizado_en = NOW()
         WHERE cod_herramienta = NEW.cod_herramienta AND cod_sucursal = NEW.cod_sucursal;

    ELSIF NEW.tipo_movimiento = 'TRANSFERENCIA_ENTRADA' THEN
        UPDATE inventario_sucursal
           SET stock_unidades = stock_unidades + NEW.cantidad_unidades,
               actualizado_en = NOW()
         WHERE cod_herramienta = NEW.cod_herramienta AND cod_sucursal = NEW.cod_sucursal_destino;

    ELSIF NEW.tipo_movimiento = 'AJUSTE' THEN
        UPDATE inventario_sucursal
           SET stock_unidades = NEW.cantidad_unidades,
               actualizado_en = NOW()
         WHERE cod_herramienta = NEW.cod_herramienta AND cod_sucursal = NEW.cod_sucursal;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aplicar_movimiento
    AFTER INSERT ON movimientos_inventario
    FOR EACH ROW EXECUTE FUNCTION fn_aplicar_movimiento_inventario();

-- 7.4 HU17: función pura para calcular el EOQ = raíz(2DS/H)
CREATE OR REPLACE FUNCTION fn_calcular_eoq(
    p_demanda_anual NUMERIC,
    p_costo_pedido NUMERIC,
    p_costo_almacenamiento NUMERIC
) RETURNS NUMERIC AS $$
BEGIN
    IF p_costo_almacenamiento IS NULL OR p_costo_almacenamiento <= 0 THEN
        RETURN NULL;
    END IF;
    RETURN SQRT((2 * p_demanda_anual * p_costo_pedido) / p_costo_almacenamiento);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 7.5 HU18: función pura para calcular el ROP (demanda diaria * tiempo de entrega)
CREATE OR REPLACE FUNCTION fn_calcular_rop(
    p_demanda_anual NUMERIC,
    p_tiempo_entrega_dias INTEGER
) RETURNS NUMERIC AS $$
BEGIN
    IF p_tiempo_entrega_dias IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN (p_demanda_anual / 365.0) * p_tiempo_entrega_dias;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 7.6 HU20: redondea la cantidad EOQ sugerida al múltiplo de caja más cercano hacia arriba
CREATE OR REPLACE FUNCTION fn_ajustar_a_cajas(
    p_cantidad_unidades NUMERIC,
    p_unidades_por_caja INTEGER
) RETURNS NUMERIC AS $$
BEGIN
    IF p_unidades_por_caja IS NULL OR p_unidades_por_caja <= 0 THEN
        RETURN p_cantidad_unidades;
    END IF;
    RETURN CEIL(p_cantidad_unidades / p_unidades_por_caja) * p_unidades_por_caja;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================================
-- 8. VISTAS (reportes derivados, sin duplicar datos)
-- =====================================================================

-- HU11: consulta de stock global por herramienta en ambas sucursales
CREATE OR REPLACE VIEW vw_stock_global AS
SELECT
    h.cod_herramienta,
    h.codigo_caja,
    h.nombre,
    h.modelo,
    s.cod_sucursal,
    s.nombre        AS sucursal_nombre,
    COALESCE(i.stock_unidades, 0) AS stock_unidades,
    i.en_promocion
FROM herramientas h
CROSS JOIN sucursales s
LEFT JOIN inventario_sucursal i
       ON i.cod_herramienta = h.cod_herramienta AND i.cod_sucursal = s.cod_sucursal
WHERE h.activo = TRUE
ORDER BY h.nombre, s.nombre;
COMMENT ON VIEW vw_stock_global IS 'HU11: buscar herramienta y ver stock en ambas sucursales';

CREATE OR REPLACE VIEW vw_herramientas_estancadas AS
SELECT
    h.cod_herramienta,
    h.codigo_caja,
    h.nombre,
    i.cod_sucursal,
    s.nombre        AS sucursal_nombre,
    i.stock_unidades,
    i.fecha_ultima_salida,
    COALESCE(CURRENT_DATE - i.fecha_ultima_salida, 9999) AS dias_sin_venta,
    i.en_promocion
FROM inventario_sucursal i
JOIN herramientas h ON h.cod_herramienta = i.cod_herramienta
JOIN sucursales s ON s.cod_sucursal = i.cod_sucursal
WHERE i.stock_unidades > 0
  AND (i.fecha_ultima_salida IS NULL
       OR CURRENT_DATE - i.fecha_ultima_salida > h.dias_para_estancamiento);
COMMENT ON VIEW vw_herramientas_estancadas IS 'HU22: reporte de antigüedad (umbral configurable por herramienta, default 40 días)';

CREATE OR REPLACE VIEW vw_cierre_diario AS
SELECT
    cod_sucursal,
    DATE(fecha_movimiento) AS fecha,
    COUNT(*) FILTER (WHERE tipo_movimiento = 'SALIDA') AS total_movimientos_salida,
    SUM(cantidad_unidades) FILTER (WHERE tipo_movimiento = 'SALIDA') AS total_unidades_salida,
    SUM(cantidad_unidades) FILTER (WHERE tipo_movimiento = 'ENTRADA') AS total_unidades_entrada,
    SUM(cantidad_unidades) FILTER (WHERE tipo_movimiento = 'TRANSFERENCIA_SALIDA') AS total_unidades_transferidas
FROM movimientos_inventario
GROUP BY cod_sucursal, DATE(fecha_movimiento);
COMMENT ON VIEW vw_cierre_diario IS 'HU14: resumen de salidas diarias filtrado por sucursal, para cuadrar caja';

CREATE OR REPLACE VIEW vw_alertas_reorden AS
SELECT
    h.cod_herramienta,
    h.codigo_caja,
    h.nombre,
    SUM(i.stock_unidades) AS stock_total_todas_sucursales,
    fn_calcular_rop(h.demanda_anual_estimada, h.tiempo_entrega_dias) AS rop_calculado,
    fn_calcular_eoq(h.demanda_anual_estimada, h.costo_fijo_pedido, h.costo_almacenamiento_unitario) AS eoq_calculado
FROM herramientas h
JOIN inventario_sucursal i ON i.cod_herramienta = h.cod_herramienta
WHERE h.activo = TRUE
GROUP BY h.cod_herramienta, h.codigo_caja, h.nombre, h.demanda_anual_estimada, h.tiempo_entrega_dias,
         h.costo_fijo_pedido, h.costo_almacenamiento_unitario
HAVING SUM(i.stock_unidades) <= fn_calcular_rop(h.demanda_anual_estimada, h.tiempo_entrega_dias);
COMMENT ON VIEW vw_alertas_reorden IS 'HU18: herramientas cuyo stock consolidado ya tocó su punto de reorden';

-- HU24: panel de auditoría / dashboard consolidado
CREATE OR REPLACE VIEW vw_panel_auditoria AS
SELECT
    (SELECT COUNT(*) FROM vw_alertas_reorden)          AS total_alertas_stock,
    (SELECT COUNT(*) FROM vw_herramientas_estancadas)  AS total_herramientas_estancadas,
    (SELECT COUNT(*) FROM herramientas WHERE activo)   AS total_herramientas_activas,
    (SELECT COUNT(*) FROM sucursales WHERE activo)     AS total_sucursales_activas;
COMMENT ON VIEW vw_panel_auditoria IS 'HU24: dashboard principal consolidado';

INSERT INTO sucursales (nombre, direccion) VALUES
    ('Sucursal Central', 'Por definir'),
    ('Sucursal 2', 'Por definir');


INSERT INTO usuarios (nombre_completo, nombre_usuario, contrasena, rol, cod_sucursal)
VALUES ('Administrador General', 'admin', 'CAMBIAR_ESTE_HASH', 'ADMINISTRADOR', NULL);