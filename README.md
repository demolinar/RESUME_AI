# Analizador de Habilidades en Hojas de Vida con IA

Este proyecto es una aplicación web construida con [Flask](https://flask.palletsprojects.com/) que analiza hojas de vida (CVs) en formato PDF para extraer información clave sobre las habilidades de los candidatos.  Utiliza la API de OpenAI para un análisis semántico profundo del texto extraído, permitiendo una comprensión más precisa de las competencias de cada candidato.

## Funcionalidades

1. **Subir un archivo PDF (CV).**
2. **Extraer texto e imágenes del PDF.**
3. **Visualizar el texto extraído.**
4. **Analizar el texto extraído con la API de OpenAI para identificar y categorizar habilidades.**
5. **Presentar un resumen de las habilidades encontradas.**


## Requerimientos

- Python 3.9+ (recomendado)
- `pip` para gestionar dependencias.
- Una cuenta de OpenAI con una [API Key](https://platform.openai.com/account/api-keys) válida.

## Instalación y Configuración

1. **Clonar el Repositorio:**

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>
```

2. **Crear un entorno virtual (recomendado):**

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows
```

3. **Instalar las dependencias:**

```bash
pip install -r requirements.txt
```

Asegúrate de que `requirements.txt` contenga las siguientes dependencias (y cualquier otra que hayas añadido):

```
Flask
openai
PyMuPDF
requests
unidecode
python-dotenv
```

4. **Configurar el archivo `.env`:**

Crea un archivo `.env` en la raíz del proyecto con la siguiente información:

```
OPENAI_API_KEY="tu_clave_api_de_openai"
SECRET_KEY="una_clave_secreta_para_flask"  # Opcional, pero recomendado
```


## Ejecución

**Iniciar la aplicación Flask:**

Si tu archivo principal se llama `app.py`, puedes iniciarlo directamente:

```bash
python app.py
```

Esto iniciará la aplicación Flask en `http://127.0.0.1:5000/` por defecto.


**Subir un PDF:**

1. Abre tu navegador web y ve a `http://127.0.0.1:5000/`.
2. Encontrarás un formulario para subir tu archivo PDF.

**Procesamiento del PDF:**

Al subir el PDF, la aplicación lo procesará (ruta `/process`), extrayendo el texto y las imágenes.  Los resultados se mostrarán en la página `result.html`:

- **Imágenes:** Las imágenes extraídas se mostrarán codificadas en base64.
- **Texto:** El texto extraído y limpiado se mostrará en la página.

**Descargar el Texto:**

En `result.html`, encontrarás un botón "Download Extracted Text".  Al hacer clic, se descargará un archivo `.txt` (ruta `/download/<txt_filename>`)  conteniendo el texto extraído del PDF.

**Análisis con IA (Opción 1 - Sin Imágenes):**

En `result.html`,  hay un formulario para ingresar palabras clave separadas por comas.  Estas palabras clave se usarán como llaves en la respuesta JSON de la API de OpenAI, junto con una explicación general.  Por ejemplo, si ingresas:

```
IA, SCRUM, FRONTEND
```

La respuesta de OpenAI tendrá la siguiente estructura:

```json
{
  "IA": true,  // o false, según el análisis del CV
  "SCRUM": true, // o false, según el análisis del CV
  "FRONTEND": false, // o false, según el análisis del CV
  "EXPLICACION": "El candidato cuenta con experiencia y certificación en IA y SCRUM, pero no menciona experiencia específica en Frontend en su hoja de vida."
}
```

**Análisis con IA (Opción 2 - Con Imágenes):**

Funciona de manera similar a la opción 1. Ingresa las palabras clave separadas por comas en el formulario correspondiente. La respuesta JSON seguirá la misma estructura, incluyendo las llaves especificadas y una explicación general (`EXPLICACION`).  La diferencia es que en esta opción, las imágenes del PDF se envían también a la API de OpenAI para el análisis, lo que puede influir en la respuesta.


En ambos casos, el valor asociado a cada llave (excepto `EXPLICACION`) será `true` si la habilidad se detecta en el CV y `false` en caso contrario. La clave `EXPLICACION` siempre contendrá un resumen generado por la IA que describe las habilidades del candidato con más detalle.


## Estructura del Proyecto

```
project/
├── app.py
├── config.py
├── requirements.txt
├── .env
├── logs/
├── static/
│   └── uploads/
│       └── images/
├── templates/
│   ├── index.html
│   ├── result.html
│   └── analysis_result.html
└── src/
    ├── __init__.py
    ├── routes.py
    ├── pdf_utils.py
    ├── text_cleaning.py
    ├── logger_config.py
```


## Próximas Mejoras

- **Interfaz de usuario más intuitiva:** Mejorar la visualización de los resultados y la interacción con la aplicación.
- **Soporte para otros formatos:**  Añadir soporte para otros formatos de CV, como DOCX.
- **Análisis más específico:** Refinar el análisis para identificar habilidades técnicas, blandas, idiomas, etc.
- **Integración con bases de datos:** Guardar los resultados del análisis para búsquedas posteriores.
- **Panel de administración:**  Añadir un panel para gestionar CVs y análisis.



## Imagenes Paso a Paso


![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/0.png)
![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/1.png)
![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/2.png)
![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/3.png)
![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/4.png)
![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/5.png)
![alt text](https://github.com/demolinar/RESUME_AI/blob/main/static/uploads/readme_images/6.png)





## Licencia

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).
