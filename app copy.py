import os
import fitz  # PyMuPDF
import logging
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import base64
from datetime import datetime
import re
import string
from unidecode import unidecode

# Obtener la fecha y hora actual para los logs y nombres de archivos
current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
print("Current date & time : ", current_datetime)
str_current_datetime = str(current_datetime).replace('-', '_').replace(' ', '__')

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Necesario para usar flash messages

# Configuración de la carpeta para guardar imágenes y textos
UPLOAD_FOLDER = 'static/uploads'
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
TEXT_FOLDER = 'extracted_texts'
LOG_FOLDER = 'logs'

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(TEXT_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de tipos de archivos permitidos
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configuración del logger
logger = logging.getLogger('PDFProcessor')
logger.setLevel(logging.INFO)
# Crear un manejador de archivos con timestamp en el nombre
file_handler = logging.FileHandler(os.path.join(LOG_FOLDER, f'app_{str_current_datetime}.log'))
file_handler.setLevel(logging.INFO)
# Crear un formato para los logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
# Añadir el manejador al logger
logger.addHandler(file_handler)

def clean_text(text):
    """
    Limpia el texto extraído del PDF eliminando caracteres no deseados,
    símbolos y simplificando espacios y saltos de línea.
    """
    # Convertir caracteres Unicode a sus equivalentes ASCII
    text = unidecode(text)
    # Eliminar caracteres no ASCII
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Eliminar caracteres no imprimibles
    text = ''.join(filter(lambda x: x in string.printable, text))
    # Reemplazar múltiples espacios por uno solo
    text = re.sub(r'\s+', ' ', text)
    # Opcional: Eliminar símbolos específicos si persisten
    symbols_to_remove = ['♂', '½', '±', '', '', '', 'Q', 'Ó', 'Ô', '', '', '', '±', '½', '']
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

    return text.strip()



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    logger.info('Inicio de la ruta /process')
    if 'file' not in request.files:
        logger.error('No se encontró ningún archivo en la solicitud.')
        flash('No se encontró ningún archivo en la solicitud.')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        logger.error('No se seleccionó ningún archivo.')
        flash('No se seleccionó ningún archivo.')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(pdf_path)
            logger.info(f'Archivo PDF guardado en {pdf_path}')
        except Exception as e:
            logger.exception('Error al guardar el archivo PDF.')
            flash(f'Error al guardar el archivo PDF: {e}')
            return redirect(url_for('index'))
        
        # Abrir el PDF con PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            logger.info(f'PDF abierto exitosamente: {pdf_path}')
        except Exception as e:
            logger.exception('Error al abrir el PDF con PyMuPDF.')
            flash(f'Error al abrir el PDF: {e}')
            return redirect(url_for('index'))
        
        # Limpiar la carpeta de imágenes antes de guardar nuevas
        try:
            for img_file in os.listdir(IMAGE_FOLDER):
                if img_file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    os.remove(os.path.join(IMAGE_FOLDER, img_file))
            logger.info('Carpeta de imágenes limpiada.')
        except Exception as e:
            logger.exception('Error al limpiar la carpeta de imágenes.')
            flash(f'Error al limpiar la carpeta de imágenes: {e}')
            return redirect(url_for('index'))
        
        # Extraer y guardar cada página como imagen
        image_filenames = []
        for page_num in range(doc.page_count):
            try:
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                image_filename = f'page_{page_num + 1}.png'
                image_path = os.path.join(IMAGE_FOLDER, image_filename)
                pix.save(image_path)
                image_filenames.append(image_filename)
                logger.info(f'Imagen guardada: {image_path}')
            except Exception as e:
                logger.exception(f'Error al procesar la página {page_num + 1}.')
                flash(f'Error al procesar la página {page_num + 1}: {e}')
                continue
        
        # Extraer texto del PDF y guardarlo en un archivo .txt
        try:
            text = ""
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()


            # Limpieza del texto
            final_text = clean_text(text)

            
            txt_filename = f'{os.path.splitext(filename)[0]}.txt'
            txt_path = os.path.join(TEXT_FOLDER, txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(final_text)
            logger.info(f'Texto extraído y guardado en {txt_path}')
        except Exception as e:
            logger.exception('Error al extraer el texto del PDF.')
            flash(f'Error al extraer el texto del PDF: {e}')
            return redirect(url_for('index'))
        
        # Cerrar el documento PDF
        doc.close()
        logger.info('Documento PDF cerrado.')
        
        # # Eliminar el PDF después de procesarlo para ahorrar espacio (opcional)
        # try:
        #     os.remove(pdf_path)
        #     logger.info(f'Archivo PDF eliminado: {pdf_path}')
        # except Exception as e:
        #     logger.warning(f'No se pudo eliminar el archivo PDF: {pdf_path}. Error: {e}')
        
        # Verificar que se hayan extraído imágenes
        if not image_filenames:
            logger.warning('No se extrajeron imágenes del PDF.')
            flash('No se extrajeron imágenes del PDF.')
            return redirect(url_for('index'))
        
        # Preparar las rutas de las imágenes para la plantilla
        images_base64 = []
        for img_filename in image_filenames:
            image_path = os.path.join(IMAGE_FOLDER, img_filename)
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
        
        # Leer el texto extraído
        try:
            with open(txt_path, 'r', encoding='utf-8') as txt_file:
                extracted_text = txt_file.read()
            logger.info('Texto extraído leído correctamente.')
            
            # Limpiar el texto

            logger.info('Texto extraído limpiado correctamente.')
        except Exception as e:
            logger.exception('Error al leer el archivo de texto extraído.')
            flash(f'Error al leer el texto extraído: {e}')
            extracted_text = "No se pudo extraer el texto."
        
        # Redirigir a la página de resultados con las imágenes y el texto
        return render_template('result.html', images=images_base64, extracted_text=extracted_text, txt_filename=txt_filename)

# Ruta para descargar el archivo de texto extraído
@app.route('/download/<filename>')
def download_text(filename):
    logger.info(f'Solicitud de descarga del archivo de texto: {filename}')
    try:
        return send_from_directory(TEXT_FOLDER, filename, as_attachment=True)
    except Exception as e:
        logger.exception(f'Error al descargar el archivo de texto: {filename}')
        flash(f'Error al descargar el archivo de texto: {e}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
