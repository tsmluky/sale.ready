# 📘 TraderCopilot Quant Engine V2: Arquitectura Agéntica
> **Documento de Diseño para Socios**
> **Objetivo**: Explicar cómo el sistema Pro pasa de ser una herramienta de "configuración" a una de "creación" mediante IA.

## 1. El Concepto: De Usuario a Creador
Los sistemas actuales son limitados: el usuario solo puede cambiar parámetros (ej. RSI 14 a 20).
**Quant Engine V2** rompe esa barrera. Permite al usuario actuar como un **Hedge Fund Manager**, dictando la estrategia en lenguaje natural, mientras la IA actúa como su equipo de Quants.

---

## 2. La "Tríada" Agéntica (El Núcleo)
No usamos un solo prompt gigante. Usamos una cadena de montaje de 3 Agentes especializados para garantizar código de calidad institucional.

### 🕵️ 1. El Arquitecto (Razonamiento)
*   **Rol**: Product Manager.
*   **IA**: Gemini 1.5 Pro.
*   **Función**: Entrevista al usuario. Rechaza ideas vagas como "hazme rico". Exige condiciones claras de Entrada, Salida y Gestión de Riesgo.
*   **Output**: Un "BluePrint" JSON (sin código).
    *   *Ejemplo*: "Entrar si EMA(50) cruza EMA(200) y RSI < 40".

### 🛠️ 2. El Ingeniero (Implementación)
*   **Rol**: Desarrollador Senior Python.
*   **IA**: DeepSeek Coder V3.
*   **Función**: Traduce el JSON a código Python real.
*   **Restricción**: No puede inventar librerías. Solo puede usar nuestras piezas de "Lego" certificadas (`QuantLib`).
*   **Output**: Código Python ejecutable.

### 🛡️ 3. El Auditor (Control de Calidad)
*   **Rol**: Seguridad y QA.
*   **Herramientas**: Análisis de Sintaxis (AST).
*   **Función**:
    1.  **Seguridad**: Bloquea comandos peligrosos (borrar archivos, conexiones externas no autorizadas).
    2.  **Sintaxis**: Verifica que el código compile y tenga sentido.
    3.  **Auto-Corrección**: Si encuentra un error, lo devuelve al Ingeniero para que lo arregle automáticamente.

---

## 3. Seguridad: El Sistema "Padlock"
¿Cómo permitimos que los usuarios ejecuten código sin romper el servidor?

1.  **El Esqueleto Inmutable**: La IA no escribe todo el archivo. Solo rellena un hueco específico (`user_logic`) dentro de una plantilla maestra protegida. No puede tocar la gestión de dinero ni la conexión con el Exchange.
2.  **Caja de Arena (Sandbox)**: El código se ejecuta en un entorno aislado donde solo existen las matemáticas y los datos de precios. No tiene acceso al sistema operativo.

---

## 4. Hoja de Ruta (Roadmap)
1.  **Fase I (Prototipo)**: Generador básico. Le hablas, te da el código.
2.  **Fase II (The Lab)**: Un editor visual (tipo VS Code) en la web para ver y ajustar lo que creó la IA.
3.  **Fase III (Deep Backtest)**: Probar esa estrategia con datos de 1 año en segundos.
4.  **Fase IV (Paper Trading)**: Activar la estrategia en modo simulación con alertas a Telegram.

---
*Propuesta de Valor Pro*: El usuario no necesita saber programar, solo necesita tener la idea. TraderCopilot se encarga de la ingeniería.
