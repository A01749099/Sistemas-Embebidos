import gspread
from oauth2client.service_account import ServiceAccountCredentials
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


# Conexión con Google Sheets
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials_csv.json', scope)  # Cambia este archivo por el tuyo
    client = gspread.authorize(creds)
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1WLfUVboDmkzJ04BAJKWDr1Q-CJyrnwG8037H55donRs/edit?usp=sharing').sheet1  # Cambia por tu URL de Google Sheets
    return sheet


class LoginScreen(Screen):
    def __init__(self, sheet, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.sheet = sheet
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # Error Message
        self.error_label = Label(text='', color=(1, 0, 0, 1), size_hint=(1, 0.2))
        layout.add_widget(self.error_label)

        # Username Input
        layout.add_widget(Label(text='Nombre de Usuario'))
        self.username_input = TextInput(multiline=False)
        layout.add_widget(self.username_input)

        # Password Input
        layout.add_widget(Label(text='Contraseña'))
        self.password_input = TextInput(password=True, multiline=False)
        layout.add_widget(self.password_input)

        # Buttons
        button_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        
        login_button = Button(text='Iniciar Sesión')
        login_button.bind(on_press=self.login)
        button_layout.add_widget(login_button)

        register_button = Button(text='Registrarse')
        register_button.bind(on_press=self.go_to_register)
        button_layout.add_widget(register_button)

        layout.add_widget(button_layout)

        self.add_widget(layout)

    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        if not username or not password:
            self.error_label.text = "Por favor, ingresa ambos campos."
            return

        # Obtener registros y depurar datos
        data = self.sheet.get_all_records()
        print("Datos obtenidos desde Google Sheets:", data)  # Depuración
        for row in data:
            print("Fila procesada:", row)  # Imprime cada fila para identificar problemas
            user = str(row.get('Usuario', '')).strip()
            passwd = str(row.get('Password', '')).strip()

            if user == username.strip() and passwd == password.strip():
                self.manager.current = 'welcome'
                return


        self.error_label.text = "Usuario o contraseña incorrectos."


    def go_to_register(self, instance):
        self.manager.current = 'register'


class RegisterScreen(Screen):
    def __init__(self, sheet, **kwargs):
        super(RegisterScreen, self).__init__(**kwargs)
        self.sheet = sheet
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # Error Message
        self.error_label = Label(text='', color=(1, 0, 0, 1), size_hint=(1, 0.2))
        layout.add_widget(self.error_label)

        # Username Input
        layout.add_widget(Label(text='Ingresa tu usuario a crear'))
        self.new_username_input = TextInput(multiline=False)
        layout.add_widget(self.new_username_input)

        # Password Input
        layout.add_widget(Label(text='Ingresa tu contraseña'))
        self.new_password_input = TextInput(password=True, multiline=False)
        layout.add_widget(self.new_password_input)

        # Buttons
        button_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)

        create_button = Button(text='Crear Usuario')
        create_button.bind(on_press=self.create_user)
        button_layout.add_widget(create_button)

        back_button = Button(text='Regresar')
        back_button.bind(on_press=self.go_back)
        button_layout.add_widget(back_button)

        layout.add_widget(button_layout)

        self.add_widget(layout)

    def create_user(self, instance):
        new_username = self.new_username_input.text
        new_password = self.new_password_input.text
        if not new_username or not new_password:
            self.error_label.text = "Por favor, llena ambos campos."
            return

        # Agregar usuario al Google Sheet
        self.sheet.append_row([new_username, new_password])
        self.error_label.text = "Usuario creado exitosamente."
        self.manager.current = 'login'

    def go_back(self, instance):
        self.manager.current = 'login'


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super(WelcomeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        welcome_label = Label(text='¡Bienvenido!', font_size='24sp')
        layout.add_widget(welcome_label)

        logout_button = Button(text='Cerrar Sesión', size_hint=(1, 0.2))
        logout_button.bind(on_press=self.logout)
        layout.add_widget(logout_button)

        self.add_widget(layout)

    def logout(self, instance):
        self.manager.current = 'login'


class LoginApp(App):
    def build(self):
        sheet = connect_to_google_sheets()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(sheet, name='login'))
        sm.add_widget(RegisterScreen(sheet, name='register'))
        sm.add_widget(WelcomeScreen(name='welcome'))
        return sm


if __name__ == '__main__':
    LoginApp().run()
