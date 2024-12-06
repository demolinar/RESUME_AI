from flask import Blueprint, request, render_template, redirect, url_for, flash, send_from_directory, current_app
from werkzeug.utils import secure_filename
from src.pdf_utils import extract_images_and_text
from src.text_cleaning import clean_text
import os
import base64
import logging
import openai
from openai import OpenAI
import json
import requests

main_blueprint = Blueprint('main', __name__)

@main_blueprint.before_app_request
def load_openai_api_key():
    """
     Carga la clave de API de OpenAI desde la configuración de la aplicación antes de manejar cualquier solicitud.
    """
    config = current_app.config
    openai.api_key = config['OPENAI_API_KEY']

@main_blueprint.route('/')
def index():
    """
    Renderiza la página de inicio de la aplicación.
    """
    return render_template('index.html')

@main_blueprint.route('/process', methods=['POST'])
def process():
    """
    Procesa una hv pdf cargado por el usuario:
    1. Verifica que el archivo es válido y permitido.
    2. Guarda el archivo en el servidor.
    3. Extrae texto e imágenes del PDF.
    4. Convierte las imágenes a formato Base64 para visualización.
    5. Renderiza la plantilla con el contenido extraído.    
    """
    logger = logging.getLogger('PDFProcessor')
    logger.info('Inicio de la ruta /process')

    if 'file' not in request.files:
        logger.error('No se encontro ningun archivo en la solicitud.')
        flash('No se encontro ningun archivo en la solicitud.')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        logger.error('No se selecciono ningun archivo.')
        flash('No se selecciono ningun archivo.')
        return redirect(request.url)

    config = current_app.config
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in config['ALLOWED_EXTENSIONS']:
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(config['UPLOAD_FOLDER'], filename)
        try:
            file.save(pdf_path)
            logger.info(f'Archivo PDF guardado en {pdf_path}')
        except Exception as e:
            logger.exception('Error al guardar el archivo PDF.')
            flash(f'Error al guardar el archivo PDF: {e}')
            return redirect(url_for('main.index'))

        try:
            image_filenames, txt_filename = extract_images_and_text(
                pdf_path=pdf_path, 
                upload_folder=config['UPLOAD_FOLDER'], 
                text_folder=config['TEXT_FOLDER'], 
                clean_text_func=clean_text
            )
            logger.info('Extraccion de imagenes y texto completada.')
        except Exception as e:
            logger.exception('Error al extraer el texto del PDF.')
            flash(f'Error al extraer el texto del PDF: {e}')
            return redirect(url_for('main.index'))

        # Convertir imagenes a base64
        images_base64 = []
        images_folder = os.path.join(config['UPLOAD_FOLDER'], 'images')
        for img_filename in image_filenames:
            image_path = os.path.join(images_folder, img_filename)
            try:
                with open(image_path, 'rb') as img_file:
                    img_bytes = img_file.read()
                    base64_img = base64.b64encode(img_bytes).decode('utf-8')
                    images_base64.append({
                        'filename': img_filename,
                        'mimetype': 'image/png',
                        'data': base64_img
                    })
                logger.info(f'Imagen convertida a base64: {img_filename}')
            except Exception as e:
                logger.exception(f'Error al convertir la imagen {img_filename} a base64.')
                flash(f'Error al procesar la imagen {img_filename}: {e}')
                continue

        # Leer el texto extraido
        txt_path = os.path.join(config['TEXT_FOLDER'], txt_filename)
        try:
            with open(txt_path, 'r', encoding='utf-8') as txt_file:
                extracted_text = txt_file.read()
            logger.info('Texto extraido leido correctamente.')
        except Exception as e:
            logger.exception('Error al leer el archivo de texto extraido.')
            flash(f'Error al leer el texto extraido: {e}')
            extracted_text = "No se pudo extraer el texto."

        return render_template('result.html', images=images_base64, extracted_text=extracted_text, txt_filename=txt_filename)

    else:
        flash('Tipo de archivo no permitido. Por favor, sube un archivo PDF.')
        return redirect(url_for('main.index'))

@main_blueprint.route('/download/<filename>')
def download_text(filename):
    """
    Permite descargar el archivo de texto extraído del PDF.
    Recupera el archivo desde la carpeta configurada y lo envía al cliente.
    """
    logger = logging.getLogger('PDFProcessor')
    logger.info(f'Solicitud de descarga del archivo de texto: {filename}')
    config = current_app.config
    try:
        return send_from_directory(config['TEXT_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        logger.exception(f'Error al descargar el archivo de texto: {filename}')
        flash(f'Error al descargar el archivo de texto: {e}')
        return redirect(url_for('main.index'))


@main_blueprint.route('/analyze_openai_text', methods=['POST'])
def analyze_openai_text():
    """
    Analiza el texto extraído usando la API de OpenAI:
    1. Carga el texto extraído y el prompt del usuario.
    2. Construye un mensaje inicial con instrucciones para OpenAI.
    3. Llama a la API de OpenAI para obtener una evaluación en formato JSON.
    4. Valida el formato de la respuesta.
    5. Renderiza la plantilla con los resultados obtenidos.
    """
    logger = logging.getLogger('PDFProcessor')
    logger.info('Inicio de la ruta /analyze_openai_text')

    prompt = request.form.get('prompt', '')

    prompt = 'NOMBRE_COMPLETO, EMAILS, CELULAR_TELEFONO' + prompt + ' , EXPLICACION'

    txt_filename = request.form.get('txt_filename', '')

    config = current_app.config
    txt_path = os.path.join(config['TEXT_FOLDER'], txt_filename)
    if not os.path.exists(txt_path):
        flash('El archivo de texto no existe.')
        return redirect(url_for('main.index'))

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        logger.exception('Error al leer el archivo de texto para analisis.')
        flash(f'Error al leer el archivo de texto: {e}')
        return redirect(url_for('main.index'))

    if not prompt.strip():
        flash('Debe proporcionar un prompt para el analisis.')
        return redirect(url_for('main.index'))
    
    initial_prompt = "Actua como un experto en seleccion de personal. Debes responder SOLAMENTE con un JSON. " \
                     "La estructura del JSON debe iniciar llenando los campos NOMBRE_COMPLETO, EMAILS, CELULAR_TELEFONO" \
                     "Luego La estructura del JSON debe indicar si el candidato cumple con cada habilidad listada y una explicacion. " \
                     "Si cumple, pon true; si no, pon false, y por ultimo la explicacion. " \
                     "No agregues texto adicional fuera de  NOMBRE_COMPLETO, EMAILS, CELULAR_TELEFONO y para habilidades true, false y una unica explicacion."

    
    areas = prompt.strip()

    user_message = f"{initial_prompt}\n\nHabilidades a evaluar: {areas}\n\nHoja de vida:\n{text_content}\n\n" \
               "Crea un JSON con las claves siendo cada una de las habilidades listadas " \
               "y valores true/false indicando si se cumplen y si no corresponde la llave a una habilidad explica ejemplo:   "\
               " { "\
                "'NOMBRE_COMPLETO': JUAN ROBERTO PRIETO CARDONA" \
                "'EMAILS': jrprieto@gmail.com, luan_co@adl.com" \
                "'CELULAR_TELEFONO': 3011234567, 2309512" \
                "'ARQUITECTURA': true," \
                "'CRIPTOGRAFIA': true," \
                "'EXPLICACION': Se ha desempeñado en empresas como ADL como criptografo en 2023 y en arquitectura en Construcciones Bolivar" \
                "}"

    ai_response = None

    client = openai.OpenAI()
    
    try:
        response = client.chat.completions.create( # Change the method
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": "Actua como un experto en seleccion de personal. Debes responder SOLAMENTE con un JSON."},
            {"role": "user", "content": user_message},
        ],
        max_tokens=300,
        temperature=0.3
        )

        ai_response = response.choices[0].message.content.strip()
        logger.info('Respuesta API Open AI exitosa.')
        try:
            parsed_response = json.loads(ai_response)
            logger.info('Validacion Exitosa formato JSON API Open AI.')
            # parsed_response contendra el JSON convertido a diccionario Python
        except json.JSONDecodeError:
            # Maneja el caso de que la respuesta no sea un JSON valido
            logger.exception(f'La respuesta del modelo no es un JSON valido.')

    except Exception as e:
        logger.exception('Error al llamar a OpenAI API.')
        flash(f'Error al analizar con OpenAI: {e}')
        return redirect(url_for('main.index'))
    
    return render_template('analysis_result.html', ai_response=ai_response, prompt=prompt, txt_filename=txt_filename)




@main_blueprint.route('/analyze_openai_text_images', methods=['POST'])
def analyze_openai_text_images():
    """
    # Analiza texto e imágenes extraídas usando la API de OpenAI:
    # 1. Carga texto extraído y codifica imágenes en Base64.
    # 2. Construye un mensaje combinado de texto e imágenes para OpenAI.
    # 3. Llama a la API de OpenAI para obtener una evaluación.
    # 4. Valida la respuesta como JSON.
    # 5. Renderiza los resultados en la plantilla correspondiente.
    """
    logger = logging.getLogger('PDFProcessor')
    logger.info('Inicio de la ruta /analyze_openai_text_images')

    prompt = request.form.get('prompt', '')
    txt_filename = request.form.get('txt_filename', '')

    config = current_app.config
    txt_path = os.path.join(config['TEXT_FOLDER'], txt_filename)
    if not os.path.exists(txt_path):
        flash('El archivo de texto no existe.')
        return redirect(url_for('main.index'))
    

    prompt = 'NOMBRE_COMPLETO, EMAILS, CELULAR_TELEFONO' + prompt + ' , EXPLICACION'

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        logger.exception('Error al leer el archivo de texto para analisis (opcion 2).')
        flash(f'Error al leer el archivo de texto: {e}')
        return redirect(url_for('main.index'))

    if not prompt.strip():
        flash('Debe proporcionar un prompt para el analisis (opcion 2).')
        return redirect(url_for('main.index'))

    # Construir el mensaje del usuario y el prompt inicial
    initial_prompt = "Actua como un experto en seleccion de personal. Debes responder SOLAMENTE con un JSON. " \
                     "La estructura del JSON debe iniciar llenando los campos NOMBRE_COMPLETO, EMAILS, CELULAR_TELEFONO" \
                     "Luego La estructura del JSON debe indicar si el candidato cumple con cada habilidad listada y una explicacion. " \
                     "Si cumple, pon true; si no, pon false, y por ultimo la explicacion. " \
                     "No agregues texto adicional fuera de  NOMBRE_COMPLETO, EMAILS, CELULAR_TELEFONO y para habilidades true, false y una unica explicacion."

    areas = prompt.strip()

    user_message = f"{initial_prompt}\n\nHabilidades a evaluar: {areas}\n\nHoja de vida:\n{text_content}\n\n" \
                   "Crea un JSON con las claves siendo cada una de las habilidades listadas " \
                   "y valores true/false indicando si se cumplen. " \
                   "Si no corresponde la llave a una habilidad explica. Ejemplo:\n" \
                    " { "\
                        "'NOMBRE_COMPLETO': JUAN ROBERTO PRIETO CARDONA" \
                        "'EMAILS': jrprieto@gmail.com, luan_co@adl.com" \
                        "'CELULAR_TELEFONO': 3011234567, 2309512" \
                        "'ARQUITECTURA': true," \
                        "'CRIPTOGRAFIA': true," \
                        "'EXPLICACION': Se ha desempeñado en empresas como ADL como criptografo en 2023 y en arquitectura en Construcciones Bolivar" \
                        "}"

    # Obtener la clave API y el header
    api_key = current_app.config['OPENAI_API_KEY']

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Codificar imágenes de ejemplo (aquí asumimos que existe page_1.png)
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    IMAGE_FOLDER = os.path.join(config['UPLOAD_FOLDER'], 'images')

    # Obtenemos la lista de imágenes disponibles
    images = os.listdir(IMAGE_FOLDER)
    # Filtramos por extensiones soportadas si es necesario
    supported_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    images = [img for img in images if img.lower().endswith(supported_exts)]

    if len(images) == 0:
        logger.warning("No se encontraron imágenes, no se enviarán imágenes.")
        base64_image = None
        base64_image2 = None
        base64_image3 = None
    else:
        # Si hay menos de 3 imágenes, replicamos.
        while len(images) < 3:
            images.append(images[0])
        images = images[:3]

        encoded_images = []
        for img_filename in images:
            img_path = os.path.join(IMAGE_FOLDER, img_filename)
            encoded_images.append(encode_image(img_path))
        base64_image = encoded_images[0]
        base64_image2 = encoded_images[1]
        base64_image3 = encoded_images[2]


    if base64_image:
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        }
        if base64_image2:
            image_content["image_url"]["url2"] = f"data:image/jpeg;base64,{base64_image2}"
        if base64_image3:
            image_content["image_url"]["url3"] = f"data:image/jpeg;base64,{base64_image3}"

        messages_content = [
            {
                "type": "text",
                "text": user_message
            },
            image_content
        ]
    else:
        messages_content = [
            {
                "type": "text",
                "text": user_message
            }
        ]
    payload = {
        "model": "gpt-4o", 
        "messages": [
          {
            "role": "user",
            "content": messages_content
          }
        ],
        "max_tokens": 300
    }

    # Llamar a la API usando requests.post
    import requests
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()

        content = response_json['choices'][0]['message']['content']
        cleaned_content = content.strip('```json\n').strip('```')

        ai_response = cleaned_content
        logger.info('Respuesta API Open AI opcion 2 exitosa.')

        # Intentar parsear a JSON
        try:
            parsed_response = json.loads(cleaned_content)
            logger.info('Validacion Exitosa formato JSON API Open AI (opcion 2).')
        except json.JSONDecodeError:
            logger.exception('La respuesta del modelo no es un JSON valido (opcion 2).')

    except requests.exceptions.RequestException as e:
        logger.exception('Error al llamar a OpenAI API opcion 2.')
        flash(f'Error al analizar con OpenAI (opcion 2): {e}')
        return redirect(url_for('main.index'))

    return render_template('analysis_result.html', ai_response=ai_response, prompt=prompt, txt_filename=txt_filename)