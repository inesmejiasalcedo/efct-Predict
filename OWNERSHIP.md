# Asignación de entendimiento

Cada integrante debe poder explicar cómo funciona su parte: qué historia de usuario cubre, qué archivos la implementan, cómo fluye el dato y cómo se prueba. Cada archivo indica su responsable en el comentario de la primera línea.

## Mariana: autenticación y cuentas

HU: Como dueño de restaurante quiero registrarme, iniciar sesión y cambiar mi contraseña de forma segura.

| Capa | Archivos |
|---|---|
| Backend | `backend/app/iam/models.py`, `security.py`, `service.py`, `deps.py`, `router.py` |
| Frontend | `frontend/src/api/client.js`, `src/auth/*`, `src/pages/LoginPage.jsx`, `RegisterPage.jsx`, `AccountPage.jsx` |
| Pruebas | `backend/tests/test_auth.py` |

Cómo funciona: al registrarse, la contraseña pasa por la política (8+ caracteres, letra y número) y se guarda como hash bcrypt. El login compara el hash; tras 5 fallos la cuenta se bloquea 15 min. Si es correcto, el backend firma un token JWT con `SECRET_KEY` que el frontend guarda y envía en cada petición (`Authorization: Bearer ...`). `deps.get_current_user` valida el token en cada endpoint protegido. Esto reemplaza el usuario y contraseña fijos del Sprint 1.

Endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/change-password`.

## Aaron: traducción y administración de usuarios

HU 1: Como usuario quiero usar la app en español o inglés.
HU 2: Como administrador quiero ver los restaurantes registrados con sus sedes, ubicación, aforo y precios, y activar o desactivar cuentas, sin acceder a datos confidenciales.

| Capa | Archivos |
|---|---|
| Backend | `backend/app/iam/admin_router.py`, `PUT /api/auth/language` en `iam/router.py` |
| Frontend | `frontend/src/i18n/es.js`, `en.js`, `LanguageContext.jsx`, `formatters.js`, `src/pages/AdminPage.jsx` |
| Pruebas | `test_admin_*` en `backend/tests/test_business_admin.py` |

Cómo funciona: todo texto visible sale de `es.js`/`en.js` mediante `t("clave", {parametros})`. El backend nunca manda frases, manda códigos (por ejemplo `{"code": "delivery_buffer", "params": {"minutes": 10}}`) y `formatters.js` los convierte en texto en el idioma activo. Los errores también llegan como códigos (`err.invalid_credentials`). El panel admin solo es accesible con rol `admin` (`require_admin`); muestra datos públicos del negocio y correos enmascarados (`mask_email`).

## Matías: personalización del negocio

HU: Como dueño quiero registrar mis sedes (ubicación, aforo, horario) y los ítems de mi menú (nombre, precio y descripción opcional) para que el pronóstico se ajuste a mi negocio.

| Capa | Archivos |
|---|---|
| Backend | `backend/app/business/models.py`, `service.py`, `router.py`, `districts.py` |
| Frontend | `frontend/src/pages/BusinessPage.jsx`, `src/components/business/SiteForm.jsx`, `MenuEditor.jsx` |
| Pruebas | `test_create_site_*`, `test_menu_*`, `test_owner_cannot_*` en `backend/tests/test_business_admin.py` |

Cómo funciona: una sede guarda latitud/longitud (con distritos predefinidos para no buscar coordenadas), aforo y horario. La ubicación decide qué clima y tráfico se consultan; el aforo convierte la ocupación esperada en número de clientes; el horario define qué horas cuentan como servicio. Al crear una sede se disparan en segundo plano las consultas a las APIs. El menú se carga con cajas de texto (ítem, precio, descripción y categoría opcionales) y alimenta las estadísticas de precios del panel admin. `get_site_for_user` garantiza que un dueño solo vea sus sedes.

## Gabriel: UI/UX y navegación

HU: Como usuario quiero una interfaz consistente y fácil de leer, donde encuentre todo rápido desde cualquier pantalla.

| Capa | Archivos |
|---|---|
| Frontend | `frontend/src/styles/theme.css`, `app.css`, `src/App.jsx`, `src/layout/AppLayout.jsx`, `src/site/SiteContext.jsx`, `src/components/ui/*`, `src/lib/useAsync.js` |

Cómo funciona: `theme.css` define todos los colores (blanco con gradiente amarillo/naranja `--brand-grad`, verde/ámbar/rojo por nivel de riesgo), tipografía y radios; ningún componente usa colores sueltos. `app.css` define las piezas reutilizables (card, botones, badges, tablas, tabs, formularios) y el comportamiento responsive. `App.jsx` define las rutas y `AppLayout` la barra superior con navegación, selector de sede e idioma. `components/ui` tiene los componentes gráficos propios en SVG (medidor, gráfico por hora, barras de nivel, iconos) sin librerías externas.

Rutas: `/login`, `/registro`, `/` (resumen), `/riesgo/:tipo` (detalle), `/negocio`, `/cuenta`, `/admin`.

## Inés: página de resumen

HU: Como gerente quiero ver en una sola pantalla cómo viene el día, cuáles son los riesgos y qué hacer al respecto.

| Capa | Archivos |
|---|---|
| Backend | `backend/app/reporting/service.py`, endpoint `/api/dashboard/summary` en `reporting/router.py` |
| Frontend | `frontend/src/pages/SummaryPage.jsx`, `src/components/summary/*` |
| Pruebas | `test_summary_endpoint_end_to_end` en `backend/tests/test_risk_and_predictions.py` |

Cómo funciona: `site_prediction` toma los últimos datos limpios de la sede, arma las variables por hora y llama al modelo. La página muestra: titular en lenguaje simple con la ventana horaria crítica (`OverallHero`), las 4 tarjetas de riesgo (`RiskCard`), la curva de clientes esperados frente a un día normal y el aforo, las 4 acciones más prioritarias (`ActionList`), condiciones actuales y la frescura de los datos con aviso si son simulados (`DataStatus`). Se refresca sola cada 5 minutos.

## Diana: páginas de detalle

HU: Como gerente quiero entender por qué un riesgo está alto, en qué horas ocurre, qué lo causa y con qué datos se calculó.

| Capa | Archivos |
|---|---|
| Backend | endpoint `/api/dashboard/risk/{tipo}` en `backend/app/reporting/router.py`, `backend/app/prediction/actions.py` |
| Frontend | `frontend/src/pages/RiskDetailPage.jsx`, `src/components/detail/*` |
| Pruebas | `test_prediction_structure_and_closed_hours`, `test_rainy_night_*` en `test_risk_and_predictions.py` |

Cómo funciona: cada riesgo trae sus factores con el porcentaje que aporta (`FactorBreakdown`), la serie de las próximas 24 h con umbrales 40/70, las acciones recomendadas, los datos externos usados con su fuente y antigüedad (`InputsPanel`) y una explicación en lenguaje simple de cómo se calcula. `actions.py` decide las recomendaciones según nivel y factor dominante (por ejemplo, si el delivery está alto por lluvia sugiere sumar minutos y usar empaques resistentes).

## Harry: pipeline de datos y modelo

HU: Como gerente quiero que los datos externos se actualicen solos y que las predicciones sean confiables.

| Capa | Archivos |
|---|---|
| Backend | `backend/app/ingestion/*` (clientes, `cleaning.py`, `service.py`, `scheduler.py`, `simulated.py`), `backend/app/prediction/features.py`, `profiles.py`, `risk.py`, `forecast.py`, `backtest.py`, `weights.json`, `backend/scripts/*` |
| Pruebas | `backend/tests/test_api_consumption.py`, cálculos y backtesting en `test_risk_and_predictions.py` |

Cómo funciona:
1. Obtener: `clients/` llama a OpenWeather, TomTom y BCRP con la key del `.env` (la sesión HTTP es inyectable para probar sin internet).
2. Filtrar y limpiar: `cleaning.py` valida campos mínimos, recorta valores fuera de rango, rellena faltantes con valores neutros, elimina duplicados y normaliza unidades (bloques de 3 h a serie por hora, periodos del BCRP a fechas).
3. Guardar: `service.py` guarda cada resultado como snapshot. Si una API falla usa el último dato válido; si no hay key, guarda datos simulados marcados.
4. Refrescar: `scheduler.py` repite todo cada 15-30 min.
5. Predecir: `features.py` arma una fila por hora (lluvia, temperatura, tráfico proyectado), `risk.py` calcula los 4 riesgos y `forecast.py` arma la predicción de 24 h con ventanas críticas.
6. Optimizar: `scripts/calibrate.py` entrena los pesos con el 70% antiguo del histórico y `backtest.py` mide precisión en el 30% reciente.
