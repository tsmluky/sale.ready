# Plan de Diferenciación: Quant Lite vs. Quant Pro

## 1. Visión Estratégica
El objetivo no es solo vender el "Pro", sino utilizar el "Lite" como una herramienta de confianza que demuestre que el sistema funciona, creando un camino natural hacia la actualización ("Upsell").

*   **Quant Lite**: Es el *gancho*. Genera confianza y hábito de uso. Es "seguro" y lento.
*   **Quant Pro**: Es la *velocidad*. Ofrece granularidad, experimentación y ventaja competitiva.

---

## 2. Definición de Productos

### 🟢 Quant Lite (La Base)
Diseñado para el usuario casual o conservador que quiere operar pero no tiene tiempo de estar pegado a la pantalla todo el día.

*   **Estrategias**: Solo *Core Strategies* (probadas y de bajo riesgo, ej. MA Cross).
*   **Timeframes**: Solo *Macro* (> 4 horas). Menos ruido, menos señales.
*   **Alertas**: Estándar (Notificación en Dashboard/Telegram).
*   **Coste**: Incluido en la suscripción base o Freemium (según modelo).

### 🔴 Quant Pro (La Máquina)
Diseñado para el trader activo que busca alpha y oportunidades constantes en el mercado.

*   **Estrategias**: *Core* + *Experimental* (Mean Reversion, Breakouts agresivos).
*   **Timeframes**: Todos, incluyendo *Intradía* (15m, 1h). Mucha más acción.
*   **Alertas**: Prioridad (Push inmediato, Telegram Bot dedicado).
*   **Data**: Acceso a reportes de Backtesting detallados (Win Rate, Drawdown por estrategia).
*   **Coste**: Suscripción Premium Mensual.

---

## 3. Matriz Comparativa (Features)

| Feature | Quant Lite | Quant Pro |
| :--- | :---: | :---: |
| **Estrategias Disponibles** | Solo Core (Trend King) | Core + Experimental (Mean Rev, Vol Flow) |
| **Frecuencia de Señales** | Baja (1-3 por semana) | Alta (3-10 por día) |
| **Timeframes** | 4h, 1d | 15m, 1h, 4h, 1d |
| **Latencia de Datos** | Tiempo Real | Tiempo Real |
| **Reportes de Rendimiento** | Básico (PnL General) | Avanzado (Métricas por Estrategia) |
| **Canales de Alerta** | Dashboard, Email | Telegram, Push, Webhook (API) |
| **Soporte** | Comunitario | Prioritario |

---

## 4. Estrategia de Implementación (Roadmap)

### Fase 1: Hardening de "Lite" (Confianza)
*   Asegurar que las *Core Strategies* en 4h sean impecables.
*   El usuario Lite debe sentir que "se pierde cosas" por no tener el Pro, viendo las estrategias bloqueadas en gris en el dashboard.

### Fase 2: El "Upsell" Visual
*   En el Dashboard, mostrar señales "Pro" borrosas o con un candado.
*   Mostrar un banner: *"Hubieras ganado X% hoy con Quant Pro"*.

### Fase 3: Lanzamiento Pro
*   Habilitar los timeframes de 15m y las estrategias experimentales para usuarios con flag `plan: pro`.

---
*Documento preparado para reunión de socios - Enero 2026*
