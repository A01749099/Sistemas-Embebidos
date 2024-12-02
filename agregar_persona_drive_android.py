from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from PIL import Image  # Librería Pillow para manejar imágenes
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from jnius import autoclass

# Credenciales y token
CREDENTIALS_FILE = "credentials.json"  # Ruta al archivo de credenciales
TOKEN_FILE = "token.json"              # Ruta al archivo de token
PARENT_FOLDER_ID = "1WaXj_U5QL0nCEeFPuA_8uRmrwNeYnY5G"    # Cambiar por el ID de la carpeta donde se creará la subcarpeta


class NameCameraApp(App):
    def build(self):
        # Guardar el diseño inicial en un método separado para reutilizarlo
        return self.create_initial_screen()

    def create_initial_screen(self):
        # Crear el diseño principal
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Crear una barra de texto para el nombre
        self.name_input = TextInput(hint_text="Ingresa tu Nombre", size_hint=(1, 0.1), multiline=False)
        self.name_input.bind(text=self.on_text_change)  # Vincular un evento para monitorear cambios
        self.main_layout.add_widget(self.name_input)

        # Crear un botón para confirmar el nombre, inicialmente deshabilitado
        self.name_button = Button(text="Agregar Persona", size_hint=(1, 0.1), disabled=True)
        self.name_button.bind(on_press=self.start_camera)
        self.main_layout.add_widget(self.name_button)

        # Crear una etiqueta para mostrar mensajes
        self.label = Label(text="Bienvenido!", size_hint=(1, 0.1))
        self.main_layout.add_widget(self.label)

        return self.main_layout

    def on_text_change(self, instance, value):
        # Habilitar el botón solo si hay texto en el TextInput
        self.name_button.disabled = not bool(value.strip())

    def start_camera(self, instance):
        # Mostrar un mensaje con el nombre
        self.user_name = self.name_input.text.strip()
        self.label.text = f"Hola, {self.user_name}! Listo para la Foto?."

        # Limpiar el diseño y agregar la cámara
        self.main_layout.clear_widgets()

        # Crear el diseño de cámara
        camera_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Agregar cámara
        self.camera = Camera(resolution=(640, 480), play=True)
        camera_layout.add_widget(self.camera)

        # Botón para capturar la foto
        capture_button = Button(text="Empecemos", size_hint=(1, 0.1))
        capture_button.bind(on_press=self.capture_photo)
        camera_layout.add_widget(capture_button)

        # Botón para regresar a la pantalla inicial
        back_button = Button(text="Regresar", size_hint=(1, 0.1))
        back_button.bind(on_press=self.go_back)
        camera_layout.add_widget(back_button)

        # Botón para activar/desactivar el flash
        self.flash_on = False
        flash_button = Button(text="Flash Off", size_hint=(1, 0.1))
        flash_button.bind(on_press=self.toggle_flash)
        camera_layout.add_widget(flash_button)

        # Agregar cámara y botones al diseño principal
        self.main_layout.add_widget(self.label)
        self.main_layout.add_widget(camera_layout)

    def toggle_flash(self, instance):
        # Alternar el estado del flash para Android
        Camera = autoclass('android.hardware.Camera')
        CameraParameters = autoclass('android.hardware.Camera$Parameters')

        if not hasattr(self, 'camera_android'):
            self.camera_android = Camera.open()
            self.params = self.camera_android.getParameters()

        self.flash_on = not self.flash_on

        if self.flash_on:
            self.params.setFlashMode(CameraParameters.FLASH_MODE_TORCH)
            self.camera_android.setParameters(self.params)
            self.camera_android.startPreview()
            instance.text = "Flash On"
        else:
            self.params.setFlashMode(CameraParameters.FLASH_MODE_OFF)
            self.camera_android.setParameters(self.params)
            self.camera_android.stopPreview()
            instance.text = "Flash Off"

    def capture_photo(self, instance):
        # Capturar y guardar la foto como PNG temporal
        temp_png_file = "temp_image.png"
        self.camera.export_to_png(temp_png_file)

        # Convertir a JPG usando Pillow con el nombre del usuario
        jpg_file = f"{self.user_name}.jpg"
        with Image.open(temp_png_file) as img:
            rgb_img = img.convert("RGB")  # Convertir a RGB si es necesario
            rgb_img.save(jpg_file, "JPEG")

        self.label.text = f"Photo saved as '{jpg_file}'. Uploading to Google Drive..."
        print(f"Photo saved as '{jpg_file}'")

        # Subir a Google Drive
        self.upload_to_drive(jpg_file)

    def find_folder(self, drive_service, folder_name):
        """Busca una carpeta con el nombre dado en Google Drive."""
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{PARENT_FOLDER_ID}' in parents"
        response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = response.get('files', [])
        return files[0]['id'] if files else None

    def upload_to_drive(self, file_path):
        # Autenticar en la API de Google Drive
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        drive_service = build('drive', 'v3', credentials=creds)

        # Buscar si la carpeta ya existe
        folder_id = self.find_folder(drive_service, self.user_name)
        if not folder_id:
            # Crear carpeta si no existe
            folder_metadata = {
                'name': self.user_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [PARENT_FOLDER_ID]
            }
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"Folder '{self.user_name}' created with ID: {folder_id}")
        else:
            print(f"Folder '{self.user_name}' already exists with ID: {folder_id}")

        # Subir el archivo a la carpeta encontrada o creada
        file_metadata = {
            'name': f"{self.user_name}.jpg",
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"File '{file_path}' uploaded to Google Drive with ID: {file.get('id')}")

        self.label.text = f"Photo uploaded to Google Drive as '{self.user_name}.jpg' in folder '{self.user_name}'."

    def go_back(self, instance):
        # Limpiar el diseño y volver a la pantalla inicial
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.create_initial_screen())


if __name__ == "__main__":
    NameCameraApp().run()
