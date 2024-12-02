from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.camera import Camera
from kivy.uix.floatlayout import FloatLayout
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.credentials import Credentials
from kivy.uix.image import Image  # Clase de Kivy para mostrar imágenes
from PIL import Image as PILImage  # Clase de Pillow para manipular imágenes
from kivy.graphics.texture import Texture
import cv2
from kivy.clock import Clock
from subprocess import Popen
import sys
import cv2
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.image import Image as KivyImage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image as PILImage


# Configuración de Google Sheets
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials_csv.json', scope)  # Cambia este archivo por el tuyo
    client = gspread.authorize(creds)
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WLfUVboDmkzJ04BAJKWDr1Q-CJyrnwG8037H55donRs/edit?usp=sharing').sheet1
    return sheet


# Configuración de Google Drive
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
PARENT_FOLDER_ID = "1WaXj_U5QL0nCEeFPuA_8uRmrwNeYnY5G"

active_cameras = []


from kivy.uix.image import Image


def release_all_cameras():
    global active_cameras
    for camera in active_cameras:
        camera.release()
        print("Cámara liberada.")
    active_cameras = []  # Vaciar la lista

def Prender_Cameras(indices=[0]):
    global active_cameras
    cameras = {}
    
    for index in indices:
        camera = cv2.VideoCapture(index)  # Inicializa la cámara
        if camera.isOpened():
            active_cameras.append(camera)  # Agregar a la lista global
            cameras[index] = camera
            print(f"Cámara {index} inicializada y añadida a la lista.")
        else:
            print(f"Error: No se pudo abrir la cámara {index}.")
    
    return cameras


class LoginScreen(Screen):
    def __init__(self, sheet, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.sheet = sheet

        # Imagen de fondo
        background = Image(
            source='login.png',
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(background)

        # Contenedor principal
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40, size_hint=(0.4, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.45})

        # Etiqueta de error centrada
        self.error_label = Label(
            text='',
            color=(1, 0, 0, 1),
            size_hint=(1, 0.2),
            font_size=16,
            halign='center',
            valign='middle'
        )
        self.error_label.bind(size=self.error_label.setter('text_size'))
        layout.add_widget(self.error_label)

        # Sección de "Nombre de Usuario"
        username_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        username_label = Label(text='Nombre de Usuario', font_size=20, halign='center', valign='middle')
        username_label.bind(size=username_label.setter('text_size'))
        self.username_input = TextInput(multiline=False, font_size=18, size_hint=(1, 1))
        username_layout.add_widget(username_label)
        username_layout.add_widget(self.username_input)
        layout.add_widget(username_layout)

        # Sección de "Contraseña"
        password_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        password_label = Label(text='Contraseña', font_size=20, halign='left', valign='middle')
        password_label.bind(size=password_label.setter('text_size'))
        self.password_input = TextInput(password=True, multiline=False, font_size=18, size_hint=(1, 1))
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        layout.add_widget(password_layout)

        # Contenedor para los botones
        button_layout = BoxLayout(size_hint=(1.2, 0.3), spacing=60, padding=(0, 10),pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # Botón de iniciar sesión
        login_button = Button(
            text='Iniciar Sesión',
            font_size=20,
            size_hint=(0.4, 1),
            background_color=(0.2, 0.6, 0.9, 0)  # Color azul
        )
        login_button.bind(on_press=self.login)
        button_layout.add_widget(login_button)

        # Botón de registrarse
        register_button = Button(
            text='Registrarse',
            font_size=20,
            size_hint=(0.4, 1),
            background_color=(0.4, 0.8, 0.4, 0)  # Color verde
        )
        register_button.bind(on_press=self.go_to_register)
        button_layout.add_widget(register_button)

        # Agregar los botones al layout principal
        layout.add_widget(button_layout)

        # Añadir el layout encima del fondo
        self.add_widget(layout)

    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        if not username or not password:
            self.error_label.text = "Por favor, ingresa ambos campos."
            return

        data = self.sheet.get_all_records()
        for row in data:
            user = str(row.get('Usuario', '')).strip()
            passwd = str(row.get('Password', '')).strip()
            if user == username.strip() and passwd == password.strip():
                self.manager.current = 'inicio'
                return

        self.error_label.text = "Usuario o contraseña incorrectos."

    def go_to_register(self, instance):
        self.manager.current = 'register'


class RegisterScreen(Screen):
    def __init__(self, sheet, **kwargs):
        super(RegisterScreen, self).__init__(**kwargs)
        self.sheet = sheet

        # Imagen de fondo
        background = Image(
            source='registro.png',
            allow_stretch=True,
            keep_ratio=False
        )
        self.add_widget(background)

        # Contenedor principal
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40, size_hint=(0.4, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.4})

        # Etiqueta de error centrada
        self.error_label = Label(
            text='',
            color=(1, 0, 0, 1),
            size_hint=(1, 0.2),
            font_size=18,
            halign='center',
            valign='middle'
        )
        self.error_label.bind(size=self.error_label.setter('text_size'))
        layout.add_widget(self.error_label)

        # Sección de "Usuario"
        username_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        username_label = Label(text='Usuario', font_size=20, halign='center', valign='middle')
        username_label.bind(size=username_label.setter('text_size'))
        self.new_username_input = TextInput(multiline=False, font_size=18, size_hint=(1, 1))
        username_layout.add_widget(username_label)
        username_layout.add_widget(self.new_username_input)
        layout.add_widget(username_layout)

        # Sección de "Contraseña"
        password_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        password_label = Label(text='Contraseña', font_size=20, halign='left', valign='middle')
        password_label.bind(size=password_label.setter('text_size'))
        self.new_password_input = TextInput(password=True, multiline=False, font_size=18, size_hint=(1, 1))
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.new_password_input)
        layout.add_widget(password_layout)

        # Sección de "Número de Celular"
        phone_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.2))
        phone_label = Label(text='Número de Celular', font_size=20, halign='left', valign='middle')
        phone_label.bind(size=phone_label.setter('text_size'))
        self.new_phone_input = TextInput(input_filter='int', multiline=False, font_size=18, size_hint=(1, 1))
        phone_layout.add_widget(phone_label)
        phone_layout.add_widget(self.new_phone_input)
        layout.add_widget(phone_layout)

        # Contenedor para los botones
        button_layout = BoxLayout(size_hint=(1.2, 0.3), spacing=60, padding=(0, 10), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # Botón de crear usuario
        create_button = Button(
            text='Crear Usuario',
            font_size=20,
            size_hint=(0.4, 1),
            background_color=(0.2, 0.6, 0.9, 0)  # Color azul
        )
        create_button.bind(on_press=self.create_user)
        button_layout.add_widget(create_button)

        # Botón de regresar
        back_button = Button(
            text='Regresar',
            font_size=20,
            size_hint=(0.4, 1),
            background_color=(0.4, 0.8, 0.4, 0)  # Color verde
        )
        back_button.bind(on_press=self.go_back)
        button_layout.add_widget(back_button)

        # Agregar los botones al layout principal
        layout.add_widget(button_layout)

        # Añadir el layout encima del fondo
        self.add_widget(layout)

    def create_user(self, instance):
        new_username = self.new_username_input.text
        new_password = self.new_password_input.text
        new_phone = self.new_phone_input.text

        if not new_username or not new_password or not new_phone:
            self.error_label.text = "Por favor, llena todos los campos."
            return

        if len(new_phone) < 10:
            self.error_label.text = "El número de celular debe tener al menos 10 dígitos."
            return

        # Guardar la información en el Excel
        self.sheet.append_row([new_username, new_password, new_phone])
        self.error_label.text = "Usuario creado exitosamente."
        self.manager.current = 'login'

    def go_back(self, instance):
        self.manager.current = 'login'

class InicioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        # Imagen de fondo
        fondo = Image(source='fondo.png', allow_stretch=True, keep_ratio=False)
        layout.add_widget(fondo)

        # Botón para ir a la pantalla de "Nuevo Usuario"
        btn_nuevo_usuario = Button(
            text="Nuevo Usuario",
            font_size=20,
            size_hint=(0.6, 0.1),
            background_color=(1, 1, 1, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.415}
        )
        btn_nuevo_usuario.bind(on_press=self.ir_a_nuevo_usuario)
        layout.add_widget(btn_nuevo_usuario)

        # Botón para ir a la pantalla de "Control de Detección"
        btn_control_deteccion = Button(
            text="Control de Detección",
            font_size=20,
            size_hint=(0.6, 0.1),
            background_color=(0.2, 0.8, 0.2, 0),  # Fondo verde semitransparente
            pos_hint={'center_x': 0.5, 'center_y': 0.525}
        )
        btn_control_deteccion.bind(on_press=self.ir_a_control_deteccion)
        layout.add_widget(btn_control_deteccion)

        # Botón para cerrar sesión
        btn_cerrar_sesion = Button(
            text="Cerrar Sesión",
            font_size=20,
            size_hint=(0.6, 0.1),
            background_color=(1, 0.2, 0.2, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.293}
        )
        btn_cerrar_sesion.bind(on_press=self.cerrar_sesion)
        layout.add_widget(btn_cerrar_sesion)

        self.add_widget(layout)

    def ir_a_nuevo_usuario(self, instance):
        """Función para cambiar a la pantalla 'nuevo_usuario'."""
        self.manager.current = "nuevo_usuario"

    def ir_a_control_deteccion(self, instance):
        """Función para cambiar a la pantalla 'control_deteccion'."""
        self.manager.current = "control_deteccion"

    def cerrar_sesion(self, instance):
        """Función para cambiar a la pantalla 'login'."""
        self.manager.current = "login"

class ControlDeteccionScreen(Screen):
    def __init__(self, **kwargs):
        self.segundo_codigo = None  # Variable para guardar el proceso
        super().__init__(**kwargs)
        self.layout = FloatLayout()

        # Imagen de fondo
        fondo = Image(source='deteccion.png', allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(fondo)

        # Etiqueta de información
        self.label = Label(
            text="Pantalla de Control de Detección",
            font_size=24,
            size_hint=(1, 0.2),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        self.layout.add_widget(self.label)

        # Botón para activar reconocimiento
        btn_activar = Button(
            text="Activar Reconocimiento",
            font_size=20,
            size_hint=(0.4, 0.1),
            background_color=(0.2, 0.8, 0.2, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.525}
        )
        btn_activar.bind(on_press=self.activar_reconocimiento)
        self.layout.add_widget(btn_activar)

        # Botón para detener reconocimiento
        btn_detener = Button(
            text="Detener Reconocimiento",
            font_size=20,
            size_hint=(0.4, 0.1),
            background_color=(0.8, 0.2, 0.2, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.415}
        )
        btn_detener.bind(on_press=self.detener_reconocimiento)
        self.layout.add_widget(btn_detener)

        # Botón para monitoreo
        btn_monitoreo = Button(
            text="Monitoreo",
            font_size=20,
            size_hint=(0.4, 0.1),
            background_color=(0.4, 0.6, 1, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.295}
        )
        btn_monitoreo.bind(on_press=self.abrir_monitoreo)
        self.layout.add_widget(btn_monitoreo)

        # Botón para regresar
        btn_back = Button(
            text="Regresar",
            font_size=20,
            size_hint=(0.3, 0.1),
            background_color=(1, 1, 1, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.145}
        )
        btn_back.bind(on_press=self.go_back)
        self.layout.add_widget(btn_back)

        self.add_widget(self.layout)
    
    def activar_reconocimiento(self, instance):
        """Activa el reconocimiento ejecutando el script."""
        # Asegúrate de liberar cualquier recurso anterior
        release_all_cameras()  # Asumiendo que tienes esta función implementada
        
        # Cambia el texto de la etiqueta
        self.label.text = "Reconocimiento Activado"
        
        # Verifica si ya hay un proceso en ejecución
        if self.segundo_codigo and self.segundo_codigo.poll() is None:
            print("El script ya está en ejecución.")
            return
        
        # Inicia el nuevo script
        try:
            self.segundo_codigo = Popen([sys.executable, "deteccion.py"])  # Cambia "osc2.py" según sea necesario
            print("Nuevo script de detección iniciado.")
        except Exception as e:
            print(f"Error al iniciar el script: {e}")

    def detener_reconocimiento(self, instance):
        """Detiene el reconocimiento terminando el script."""
        # Cambia el texto de la etiqueta
        self.label.text = "Reconocimiento Detenido"
        
        # Verifica si el proceso está activo
        if self.segundo_codigo:
            try:
                self.segundo_codigo.terminate()  # Termina el proceso
                self.segundo_codigo.wait()  # Espera a que el proceso termine
                self.segundo_codigo = None  # Limpia la referencia al proceso
                print("Script de detección cerrado.")
            except Exception as e:
                print(f"Error al cerrar el script: {e}")
        else:
            print("No hay ningún script en ejecución.")
        #Prender_Cameras([0,1])
        

    def abrir_monitoreo(self, instance):
        """Cambia a la pantalla de monitoreo."""
        self.manager.current = "monitoreo"

    def go_back(self, instance):
        """Regresa a la pantalla de inicio."""
        self.manager.current = "inicio"

class MonitoreoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")

        # Imagen de fondo
        self.background_image = Image(
            source="monitoreo.png",  # Cambia "fondo.png" por el nombre de tu archivo de imagen
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.background_image)  # Agregar la imagen de fondo como primer widget
        
        # Etiqueta
        label = Label(
            text=" ",
            font_size=24,
            size_hint=(1, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.9}
        )
        self.layout.add_widget(label)

        # Layout para mostrar las dos cámaras
        self.camera_layout = BoxLayout(orientation="horizontal", size_hint=(1, 0.7))
        self.image_cam1 = Image()
        self.image_cam2 = Image()
        self.camera_layout.add_widget(self.image_cam1)
        self.camera_layout.add_widget(self.image_cam2)
        self.layout.add_widget(self.camera_layout)

        # Botón para regresar
        btn_back = Button(
            text="Regresar",
            font_size=20,
            size_hint=(0.2, 0.1),
            background_color=(0.4, 0.6, 1, 0),
            pos_hint={'center_x': 0.5, 'center_y': 0.1}
        )
        btn_back.bind(on_press=self.go_back)
        self.layout.add_widget(btn_back)

        self.add_widget(self.layout)
        
        cam1 = cv2.VideoCapture(0)
        cam2 = cv2.VideoCapture(1)
        # Inicialización de cámaras
        self.capture_cam1 = cam1
        self.capture_cam2 = cam2
        active_cameras.append(cam1)
        active_cameras.append(cam2)

        self.update_event = None

    def on_enter(self):
        """Se ejecuta al entrar a la pantalla. Inicia el monitoreo."""
        cam1 = cv2.VideoCapture(0)
        cam2 = cv2.VideoCapture(1)
        # Inicialización de cámaras
        self.capture_cam1 = cam1
        self.capture_cam2 = cam2
        active_cameras.append(cam1)
        active_cameras.append(cam2)
        self.update_event = Clock.schedule_interval(self.update_frames, 1/30)  # Actualiza a 30 FPS

    #def on_leave(self):
     #   """Se ejecuta al salir de la pantalla. Libera recursos."""
      #  if self.update_event:
       #     self.update_event.cancel()
        #self.capture_cam1.release()
        #self.capture_cam2.release()

    def update_frames(self, dt):
        """Actualiza los frames de las cámaras."""
        ret1, frame1 = self.capture_cam1.read()
        ret2, frame2 = self.capture_cam2.read()

        if ret1:
            self.image_cam1.texture = self.convert_frame_to_texture(frame1)
        if ret2:
            self.image_cam2.texture = self.convert_frame_to_texture(frame2)

    @staticmethod
    def convert_frame_to_texture(frame):
        """Convierte un frame de OpenCV en una textura de Kivy."""
        frame = cv2.flip(frame, 0)  # Voltea el frame verticalmente
        buf = frame.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        return texture

    def go_back(self, instance):
        """Regresa a la pantalla anterior."""
        self.manager.current = "control_deteccion"

class NuevoUsuarioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_name = ""
        self.capture = None  # Para el video capturado de OpenCV
        self.camera_event = None  # Evento programado para la cámara
        self.create_initial_screen()

    def create_initial_screen(self):
        container = FloatLayout()
        background = Image(
            source="captura.png",
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        container.add_widget(background)

        layout = BoxLayout(orientation='vertical', padding=10, spacing=20, size_hint=(0.6, 0.3), pos_hint={'center_x': 0.5, 'center_y': 0.4})
        self.name_input = TextInput(
            hint_text="Ingresa tu Nombre",
            size_hint=(1, 0.2),
            multiline=False,
            font_size=20
        )
        self.name_input.bind(text=self.on_text_change)
        layout.add_widget(self.name_input)

        self.name_button = Button(
            text="Agregar Persona",
            size_hint=(1, 0.2),
            background_color=(1, 1, 1, 0),
            disabled=True,
            font_size=20
        )
        self.name_button.bind(on_press=self.start_camera)
        layout.add_widget(self.name_button)

        self.label = Label(
            text=" ",
            size_hint=(1, 0.2),
            font_size=20,
            halign="center"
        )
        layout.add_widget(self.label)

        back_to_home_button = Button(
            text="Regresar al Inicio",
            size_hint=(1, 0.2),
            font_size=20,
            background_color=(0.7, 0, 0, 0)
        )
        back_to_home_button.bind(on_press=self.go_to_home)
        layout.add_widget(back_to_home_button)

        container.add_widget(layout)
        self.add_widget(container)

    def on_text_change(self, instance, value):
        self.name_button.disabled = not bool(value.strip())

    def start_camera(self, instance):
        self.user_name = self.name_input.text.strip()
        self.label.text = f"Hola, {self.user_name}! Listo para la Foto?"
        self.create_camera_screen()

    def create_camera_screen(self):
        self.clear_widgets()

        container = FloatLayout()
        background = Image(
            source="camara.png",
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        container.add_widget(background)

        self.camera_layout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.8, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.camera_view = KivyImage()  # Widget para mostrar la transmisión
        self.camera_layout.add_widget(self.camera_view)

        capture_button = Button(text="Capturar Foto", size_hint=(1, 0.2), font_size=20, background_color=(1, 1, 1, 0))
        capture_button.bind(on_press=self.capture_photo)
        self.camera_layout.add_widget(capture_button)

        back_button = Button(text="Regresar", size_hint=(1, 0.2), font_size=20, background_color=(1, 1, 1, 0))
        back_button.bind(on_press=self.go_back)
        self.camera_layout.add_widget(back_button)

        container.add_widget(self.camera_layout)
        self.add_widget(container)

        cam1 = cv2.VideoCapture(0)
        # Inicialización de cámaras
        self.capture = cam1
        active_cameras.append(cam1)  # Inicia la cámara de OpenCV
        Clock.schedule_interval(self.update_camera, 1.0 / 30.0)  # Actualiza la cámara a 30 FPS

    def update_camera(self, dt):
        if self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
                texture.blit_buffer(buf, colorfmt="bgr", bufferfmt="ubyte")
                self.camera_view.texture = texture  # Actualizar la textura del widget camera_view


    def capture_photo(self, instance):
        if self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                jpg_file = f"{self.user_name}.jpg"
                cv2.imwrite(jpg_file, frame)

                self.label.text = f"Foto guardada como {jpg_file}. Subiendo a Google Drive..."
                self.upload_to_drive(jpg_file)

    def upload_to_drive(self, file_path):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        drive_service = build('drive', 'v3', credentials=creds)

        folder_id = self.find_folder(drive_service, self.user_name)
        if not folder_id:
            folder_metadata = {
                'name': self.user_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [PARENT_FOLDER_ID]
            }
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')

        file_metadata = {'name': f"{self.user_name}.jpg", 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        self.label.text = f"Foto subida a Google Drive en la carpeta {self.user_name}."

    def find_folder(self, drive_service, folder_name):
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{PARENT_FOLDER_ID}' in parents"
        response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = response.get('files', [])
        return files[0]['id'] if files else None

    

    def go_to_home(self, instance):
        #self.stop_camera()
        self.manager.current = "inicio"
    def on_enter(self):
        """Se ejecuta al entrar a la pantalla. Inicia el monitoreo."""
        cam1 = cv2.VideoCapture(0)
        # Inicialización de cámaras
        self.capture = cam1
        active_cameras.append(cam1)
        self.camera_view = KivyImage()  # Widget para mostrar la transmisión
        
        self.update_event = Clock.schedule_interval(self.update_camera, 1/30)  # Actualiza a 30 FPS


    def go_back(self, instance):
        #self.stop_camera()
        self.clear_widgets()
        self.create_initial_screen()

# Aplicación principal
class CarDefenderApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(InicioScreen(name="inicio"))
        sm.add_widget(NuevoUsuarioScreen(name="nuevo_usuario"))
        return sm


class CarDefenderApp(App):
    def build(self):
        sm = ScreenManager()
        sheet = connect_to_google_sheets()
        sm.add_widget(LoginScreen(sheet, name='login'))
        sm.add_widget(RegisterScreen(sheet, name='register'))
        sm.add_widget(InicioScreen(name='inicio'))
        sm.add_widget(NuevoUsuarioScreen(name='nuevo_usuario'))
        sm.add_widget(ControlDeteccionScreen(name='control_deteccion'))
        sm.add_widget(MonitoreoScreen(name="monitoreo"))
        return sm

if __name__ == '__main__':
    CarDefenderApp().run()
