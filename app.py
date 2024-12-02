from flask import Flask, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'c:/Users/danii/Python_codes/bloque/Fotos/'

@app.route('/upload', methods=['POST'])
def upload_file():
    name = request.form['name']
    file = request.files['file']

    # Crear la carpeta si no existe
    directorio_persona = os.path.join(UPLOAD_FOLDER, name)
    if not os.path.exists(directorio_persona):
        os.makedirs(directorio_persona)

    # Guardar la imagen en la carpeta específica
    file_path = os.path.join(directorio_persona, file.filename)
    file.save(file_path)
    return 'Archivo guardado exitosamente', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
