# ATLAS Terminal — guía de publicación (sin saber programar)

Web de inteligencia financiera con mapa mundial que se actualiza sola con GitHub Actions.
Sigue estos pasos EN ORDEN. Solo necesitas un navegador. Todo es gratis.

## Paso 1 — Cuenta y repositorio

1. Crea cuenta en github.com (botón Sign up).
2. Arriba a la derecha: **+** → **New repository**.
3. Nombre: `atlas-terminal` · marca **Public** · botón verde **Create repository**.

## Paso 2 — Sube estos archivos

En la página del repositorio, pulsa el enlace **uploading an existing file** y arrastra
TODO el contenido de esta carpeta:

- `index.html`
- `README.md`
- `requirements.txt`
- `robot-update.yml`
- la carpeta `scripts` (con `update_data.py` dentro)
- la carpeta `data` (con los 2 archivos json de muestra)

Abajo pulsa **Commit changes**.

⚠️ Si al arrastrar carpetas no se suben, entra en la carpeta y arrastra los archivos
de uno en uno; luego usa "Add file → Upload files" indicando `scripts/` o `data/` en el nombre.

## Paso 3 — Crea el robot (el archivo especial)

El robot vive en una carpeta que empieza por punto y GitHub la trata aparte.
Se crea escribiendo su nombre a mano:

1. En el repositorio: **Add file** → **Create new file**.
2. En la casilla del nombre escribe EXACTAMENTE: `.github/workflows/update.yml`
   (al escribir cada `/` GitHub crea la carpeta sola).
3. Abre el archivo `robot-update.yml` que subiste en el Paso 2, copia TODO su contenido
   y pégalo en el editor.
4. Botón verde **Commit changes**.

## Paso 4 — Dale permisos al robot

**Settings** → menú izquierdo **Actions → General** → baja hasta "Workflow permissions"
→ marca **Read and write permissions** → **Save**.

## Paso 5 — Lanza el robot

1. Pestaña **Actions** (si sale un aviso, acéptalo con "enable them").
2. Columna izquierda: clica **Actualizar datos de mercado**.
3. Botón **Run workflow** → otra vez **Run workflow**.
4. Espera 2-3 minutos hasta el ✅ verde. Ya tienes precios y noticias reales en `data/`.

## Paso 6 — Publica la web

**Settings** → **Pages** → en "Build and deployment", Source: **Deploy from a branch**
→ Branch: `main` y `/ (root)` → **Save**.

Espera 1-2 minutos, recarga la página y arriba verás tu dirección:
`https://TU_USUARIO.github.io/atlas-terminal/`

## ¿Cómo sé que funciona?

Al abrir tu web verás arriba a la derecha del mapa el sello verde **● Datos reales**
con la fecha y hora de la última actualización. El robot corre solo de lunes a viernes
a las 06:00 y 16:30 UTC (08:00 y 18:30 en España), aunque tu ordenador esté apagado.

## Opcional — Resúmenes de noticias con IA

1. Crea una API key en console.anthropic.com (cuesta céntimos al día).
2. Repo → Settings → Secrets and variables → Actions → **New repository secret**
   → Name: `ANTHROPIC_API_KEY` → Secret: tu clave → Add secret.
3. Desde la siguiente ejecución, cada titular llevará un resumen en español.

## Si algo falla

- Pestaña Actions vacía → el Paso 3 no se completó; repítelo con el nombre exacto.
- Ejecución con ❌ → clica la fila roja → "update" → copia el error y pídeme ayuda.
- La web sale en blanco → comprueba que `index.html` está en la raíz del repositorio
  (no dentro de una subcarpeta).

---
*Proyecto educativo. Datos con retardo (~15 min, Yahoo Finance). No es asesoramiento financiero.*
