# EFCT Predict v2

Plataforma web que anticipa riesgos operativos de un restaurante (afluencia de clientes, retrasos de delivery, llegada del personal y costo de insumos) cruzando datos externos actualizados: clima (OpenWeather), tráfico (TomTom) e indicadores económicos (BCRP).

Pensada para un decision maker (dueño, gerente o encargado): una pantalla de resumen con el estado del día, qué hacer y por qué.

## Arquitectura

```
efct-predict-v2/
  backend/            API en Python (FastAPI) + base de datos + refresco automático
    app/
      iam/            Autenticación (bcrypt + JWT) y panel de administración
      business/       Restaurante, sedes (ubicación, aforo, horario) y menú
      ingestion/      Pipeline de datos: clientes de APIs, limpieza, refresco programado
      prediction/     Variables por hora, modelo de riesgo, predicción 24 h, backtesting
      reporting/      Endpoints del dashboard (resumen y detalle)
      shared/         Conexión a base de datos
    tests/            Pruebas automáticas (pytest)
    scripts/          Generación de histórico y calibración del modelo
    data/backtest/    Histórico para backtesting
  frontend/           Interfaz web en React (Vite)
```

Flujo de datos: APIs externas → `ingestion` (obtener, validar, limpiar, guardar snapshots) → `prediction` (features por hora → modelo → riesgos y acciones) → `reporting` (JSON) → `frontend` (dashboard).

Mapa de responsables por módulo: ver [OWNERSHIP.md](OWNERSHIP.md).

## Requisitos

- Python 3.10 o superior
- Node.js 18 o superior
- (Opcional) API keys de OpenWeather y TomTom. Sin ellas la app funciona con datos simulados, marcados como tales en la interfaz.

## Cómo correrlo en local (Windows, PowerShell)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Abre `backend\.env` y completa:

- `SECRET_KEY`: genera una con `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `ADMIN_EMAIL` y `ADMIN_PASSWORD`: la cuenta de administrador (8+ caracteres, letras y números)
- `OPENWEATHER_API_KEY` y `TOMTOM_API_KEY`: si las tienes

Luego:

```powershell
uvicorn app.main:app --reload
```

El backend queda en http://127.0.0.1:8000 (documentación interactiva de la API en http://127.0.0.1:8000/docs).

Si PowerShell bloquea `Activate.ps1`, corre una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 2. Frontend (otra terminal)

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173, crea una cuenta de restaurante, agrega una sede y ya tienes el pronóstico.

Atajo: `start.ps1` en la raíz abre ambas terminales.

### 3. Pruebas

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

Cubren autenticación, negocio, administración, consumo de APIs (con respuestas simuladas, sin internet), limpieza de datos, cálculos de riesgo, predicciones y el umbral mínimo de precisión del modelo.

## API keys

| Servicio | Para qué | Dónde se obtiene | Variable |
|---|---|---|---|
| OpenWeather | Clima actual y pronóstico 5 días | https://home.openweathermap.org/api_keys (plan gratuito) | `OPENWEATHER_API_KEY` |
| TomTom | Flujo de tráfico | https://developer.tomtom.com (plan gratuito) | `TOMTOM_API_KEY` |
| BCRP | Tipo de cambio e inflación de alimentos | API pública, sin key | - |

Las keys solo viven en `backend/.env`, que está en `.gitignore`. El repositorio solo incluye `backend/.env.example`. Para verificar que se cargaron: http://127.0.0.1:8000/api/health

## Actualización automática de datos

El backend refresca solo, sin intervención:

- Clima y pronóstico: cada 30 min
- Tráfico: cada 15 min
- BCRP: cada 12 h

Se configura en `.env` (`*_REFRESH_MINUTES`). Si una API falla, se sigue usando el último dato válido y la interfaz muestra la antigüedad de cada fuente. El dashboard se recarga cada 5 min y tiene un botón "Actualizar datos".

## Modelo y backtesting

- Delivery: regresión logística (tráfico, lluvia, hora punta, variabilidad del tráfico) entrenada por descenso de gradiente.
- Afluencia: curva típica por hora y día ajustada por clima y tráfico; pesos por búsqueda en grilla.
- Llegadas y costos: modelos logísticos con tráfico/lluvia e indicadores BCRP.

Calibración y evaluación (desde `backend/`):

```powershell
python -m scripts.generate_backtest_data   # genera el histórico
python -m scripts.calibrate                # optimiza pesos con el 70% antiguo y evalúa en el 30% reciente
```

Resultado actual en el conjunto de prueba: accuracy 0.90 y F1 0.61 en retrasos de delivery; error medio de demanda 6 puntos del aforo. Umbrales mínimos exigidos por las pruebas: accuracy ≥ 0.75, F1 ≥ 0.60, error ≤ 10 puntos.

Importante: el histórico actual es simulado (un año sintético con un proceso distinto al del modelo, para medir generalización). Cuando el restaurante registre incidentes reales, se reemplaza `data/backtest/history.csv` con las mismas columnas y se vuelve a calibrar.

## Despliegue en la nube (siguiente fase)

Ya está preparado:

- `Dockerfile` en la raíz: compila el frontend y lo sirve desde el mismo backend (un solo servicio).
- `render.yaml`: configuración para Render (servicio web + Postgres gratuito).
- Cambiar de SQLite a Postgres es solo cambiar `DATABASE_URL`.

Pasos generales: crear la cuenta en el proveedor, conectar el repositorio, cargar las variables de `.env.example` en el panel del proveedor y desplegar.

## Seguridad

- Contraseñas con hash bcrypt y sal aleatoria; nunca se guardan en texto plano.
- Sesiones con token JWT firmado (`SECRET_KEY`) que expira (`TOKEN_MINUTES`).
- Política de contraseñas (8+ caracteres, letras y números) y bloqueo de 15 min tras 5 intentos fallidos.
- Cada dueño solo ve sus propias sedes; el administrador ve datos públicos del negocio y correos enmascarados.
