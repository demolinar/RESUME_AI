import fitz
import os

def extract_images_and_text(pdf_path, upload_folder, text_folder, clean_text_func):
    doc = fitz.open(pdf_path)
    images_folder = os.path.join(upload_folder, 'images')

    # Limpiar carpeta de imágenes
    for img_file in os.listdir(images_folder):
        if img_file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            os.remove(os.path.join(images_folder, img_file))

    # Extraer imágenes
    image_filenames = []
    text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image_filename = f'page_{page_num + 1}.png'
        image_path = os.path.join(images_folder, image_filename)
        pix.save(image_path)
        image_filenames.append(image_filename)
        text += page.get_text()

    doc.close()

    # Limpiar texto
    final_text = clean_text_func(text)

    # Guardar texto en .txt
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_filename = f'{pdf_name}.txt'
    txt_path = os.path.join(text_folder, txt_filename)
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(final_text)

    return image_filenames, txt_filename
