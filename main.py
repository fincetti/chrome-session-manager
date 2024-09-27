import os
import re
import json
import socket
import subprocess
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QHBoxLayout, QLabel, QDialog, QFileDialog, QComboBox
)





class ChromeSessionManager(QWidget):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.setWindowTitle("Session Manager - Google Chrome")
        self.setGeometry(100, 100, 1080, 720)
        icon_r = os.path.join('Storage', 'Settings', 'icons', 'favicon.png')
        self.setWindowIcon(QIcon(icon_r))

        # Cargar configuraciones y sesiones existentes
        self.config = self.cargar_configuracion()

        # Variable para el estado del orden actual (ascendente o descendente) para cada columna
        self.sort_orders = {
            'name': Qt.AscendingOrder,  # Para el nombre, inicialmente ascendente
            'date': Qt.AscendingOrder,  # Para la fecha, inicialmente ascendente
            'size': Qt.DescendingOrder  # Para el uso de almacenamiento, inicialmente descendente
        }

        # Layout principal
        main_layout = QVBoxLayout()

        # Encabezado
        header_label = QLabel("Administración de sesiones paralelas", self)
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # Campo de entrada para el nombre de la sesión
        self.session_name_input = QLineEdit(self)
        self.session_name_input.setPlaceholderText("Nombre de la sesión")
        self.session_name_input.setFont(QFont("Arial", 12))
        self.session_name_input.setStyleSheet("padding: 10px; border-radius: 5px; border: 1px solid #ccc;")
        main_layout.addWidget(self.session_name_input)

        # Botón para crear una nueva sesión
        create_session_btn = QPushButton("Crear sesión paralela", self)
        create_session_btn.setFont(QFont("Arial", 12, QFont.Bold))
        create_session_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #28a745;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        create_session_btn.clicked.connect(self.crear_sesion)
        main_layout.addWidget(create_session_btn)

        # Árbol para mostrar las sesiones creadas
        self.sessions_tree = QTreeWidget(self)
        self.sessions_tree.setFont(QFont("Arial", 11))
        self.sessions_tree.setHeaderLabels(["Nombre", "Fecha/Hora de Creación", "Uso de Almacenamiento"])
        
        # Habilitar clics en el encabezado para ordenar
        header = self.sessions_tree.header()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_click)
        header.setSortIndicatorShown(True)  # Mostrar el indicador de orden en el encabezado

        # Conectar la señal de cambio de selección al método actualizar_botones
        self.sessions_tree.itemSelectionChanged.connect(self.actualizar_botones)

        main_layout.addWidget(self.sessions_tree)

        # Espacio ocupado y libre
        self.space_info_label = QLabel(self)
        self.space_info_label.setFont(QFont("Arial", 11))
        main_layout.addWidget(self.space_info_label)

        # Contenedor para el botón de actualización
        update_button_container = QWidget()
        update_button_layout = QHBoxLayout()
        update_button_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes
        update_button_layout.setSpacing(0)  # Eliminar espacios
        update_button_container.setLayout(update_button_layout)

        # Botón de actualización
        self.update_btn = QPushButton("Actualizar", self)
        self.update_btn.setFont(QFont("Arial", 12))
        self.update_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #999966;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7a7a52;
            }
        """)
        self.update_btn.clicked.connect(self.actualizar_todo)
        update_button_layout.addStretch()  # Empujar el botón hacia la derecha
        update_button_layout.addWidget(self.update_btn)

        main_layout.addWidget(update_button_container)  # Añadir contenedor al layout principal

        # Botones de acción para sesiones seleccionadas
        self.action_buttons_layout = QHBoxLayout()

        self.run_session_btn = QPushButton("Ejecutar sesión paralela", self)
        self.run_session_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.run_session_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #007bff;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.run_session_btn.clicked.connect(self.ejecutar_sesion)
        self.run_session_btn.setVisible(False)  # Inicialmente oculto
        self.action_buttons_layout.addWidget(self.run_session_btn)

        self.delete_session_btn = QPushButton("Borrar sesión paralela", self)
        self.delete_session_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.delete_session_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #dc3545;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_session_btn.clicked.connect(self.borrar_sesion)
        self.delete_session_btn.setVisible(False)  # Inicialmente oculto
        self.action_buttons_layout.addWidget(self.delete_session_btn)

        main_layout.addLayout(self.action_buttons_layout)

        # Botón "Ver carpeta de sesiones"
        self.view_sessions_folder_btn = QPushButton("Ver carpeta de almacenamiento", self)
        self.view_sessions_folder_btn.setFont(QFont("Arial", 12))
        self.view_sessions_folder_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #17a2b8;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.view_sessions_folder_btn.clicked.connect(self.abrir_carpeta_sesiones)
        self.view_sessions_folder_btn.setVisible(False)  # Inicialmente oculto
        main_layout.addWidget(self.view_sessions_folder_btn)

        # Botones para salir y configuración
        bottom_buttons_layout = QHBoxLayout()

        # Botón para configuración
        config_btn = QPushButton("Configuración", self)
        config_btn.setFont(QFont("Arial", 12, QFont.Bold))
        config_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #ffc107;
                color: black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        config_btn.clicked.connect(self.abrir_configuracion)
        bottom_buttons_layout.addWidget(config_btn)

        # Botón para salir
        exit_btn = QPushButton("Cerrar programa", self)
        exit_btn.setFont(QFont("Arial", 12, QFont.Bold))
        exit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #6c757d;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        exit_btn.clicked.connect(self.close)
        bottom_buttons_layout.addWidget(exit_btn)

        main_layout.addLayout(bottom_buttons_layout)

        self.setLayout(main_layout)

        # Cargar sesiones existentes y mostrarlas
        self.sesiones = self.cargar_sesiones_existentes()
        self.mostrar_sesiones()
        self.actualizar_espacio()

        # Ordenar por defecto por "Nombre"
        self.sessions_tree.sortItems(0, Qt.AscendingOrder)
        header.setSortIndicator(0, Qt.AscendingOrder)

        # Aplicar el tema al final
        self.tema = self.config.get("tema", "Oscuro")  # Oscuro por defecto
        self.aplicar_tema()
    
    def aplicar_tema(self):
        """
        Aplica el tema según la configuración del usuario.
        """
        if self.tema == "Oscuro":
            self.setStyleSheet("""
                background-color: black;
                color: white;
            """)
            self.sessions_tree.setStyleSheet("""
                QHeaderView::section { background-color: black; color: white; }
                QTreeWidget { background-color: black; color: white; }
                QLineEdit { background-color: white; color: black; }
            """)
            self.session_name_input.setStyleSheet("background-color: white; color: black;")
        else:  # Tema "Encendido"
            self.setStyleSheet("""
                background-color: white;
                color: black;
            """)
            self.sessions_tree.setStyleSheet("""
                QHeaderView::section { background-color: white; color: black; }
                QTreeWidget { background-color: white; color: black; }
                QLineEdit { background-color: white; color: black; }
            """)
            self.session_name_input.setStyleSheet("background-color: white; color: black;")

    def on_header_click(self, logical_index):
        """
        Controla el clic en el encabezado de una columna para ordenar los elementos.
        """
        if logical_index == 0:  # Columna "Nombre"
            current_order = self.sort_orders['name']
            self.sessions_tree.sortItems(0, current_order)
            self.sort_orders['name'] = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder
        elif logical_index == 1:  # Columna "Fecha/Hora de Creación"
            current_order = self.sort_orders['date']
            self.sort_sessions_by_date(current_order)
            self.sort_orders['date'] = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder
        elif logical_index == 2:  # Columna "Uso de Almacenamiento"
            current_order = self.sort_orders['size']
            self.sort_sessions_by_size(current_order)
            self.sort_orders['size'] = Qt.AscendingOrder if current_order == Qt.DescendingOrder else Qt.DescendingOrder

        # Después de ordenar, actualizamos los botones
        self.actualizar_botones()

    def sort_sessions_by_date(self, order):
        """
        Ordena las sesiones por fecha de creación.
        """
        items = []
        for index in range(self.sessions_tree.topLevelItemCount()):
            item = self.sessions_tree.topLevelItem(index)
            items.append({
                'name': item.text(0),
                'date': item.text(1),
                'size': item.text(2)
            })

        # Ordenar por fecha
        items.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"), reverse=order == Qt.DescendingOrder)

        # Limpiar el QTreeWidget
        self.sessions_tree.clear()

        # Volver a agregar los elementos, creando nuevos QTreeWidgetItem
        for item_data in items:
            new_item = QTreeWidgetItem([item_data['name'], item_data['date'], item_data['size']])
            self.sessions_tree.addTopLevelItem(new_item)

    def sort_sessions_by_size(self, order):
        """
        Ordena las sesiones por el uso de almacenamiento.
        """
        items = []
        for index in range(self.sessions_tree.topLevelItemCount()):
            item = self.sessions_tree.topLevelItem(index)
            size_text = item.text(2)  # Esto contiene la cantidad, la unidad y el porcentaje

            # Extraer la cantidad y la unidad usando expresiones regulares
            match = re.search(r'(\d+(\.\d+)?)\s*(B|KB|MB|GB|TB)', size_text)
            if match:
                size_value = float(match.group(1))  # La cantidad, p. ej., 2.5
                size_unit = match.group(3)  # La unidad, p. ej., GB
                size_in_bytes = self.convert_to_bytes(size_value, size_unit)
            else:
                size_in_bytes = 0  # Si no se puede extraer, asignar 0

            items.append({
                'name': item.text(0),
                'date': item.text(1),
                'size': item.text(2),
                'size_in_bytes': size_in_bytes  # Agregamos el tamaño en bytes para el ordenamiento
            })

        # Ordenar por tamaño en bytes
        items.sort(key=lambda x: x['size_in_bytes'], reverse=order == Qt.DescendingOrder)

        # Limpiar el QTreeWidget
        self.sessions_tree.clear()

        # Volver a agregar los elementos, creando nuevos QTreeWidgetItem
        for item_data in items:
            new_item = QTreeWidgetItem([item_data['name'], item_data['date'], item_data['size']])
            self.sessions_tree.addTopLevelItem(new_item)
    
    def convert_to_bytes(self, size_value, size_unit):
        """
        Convierte una cantidad con unidad a bytes.
        """
        unit_multipliers = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}
        return size_value * unit_multipliers[size_unit.upper()]

    def cargar_configuracion(self):
        config_path = os.path.join('Storage', 'Settings', 'constants.json')
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            default_config = {"chrome_ruta": "/usr/bin/google-chrome"}
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
        else:
            with open(config_path, 'r') as f:
                try:
                    default_config = json.load(f)
                except json.JSONDecodeError:
                    default_config = {"chrome_ruta": "/usr/bin/google-chrome"}
                    with open(config_path, 'w') as f:
                        json.dump(default_config, f, indent=4)
        return default_config

    def guardar_configuracion(self):
        """
        Guarda la configuración actual en el archivo JSON.
        """
        config_path = os.path.join('Storage', 'Settings', 'constants.json')
        self.config['tema'] = self.tema  # Guardar el tema seleccionado
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def cargar_sesiones_existentes(self):
        storage_path = os.path.join('Storage', 'Settings', 'sessions.json')
        if not os.path.exists(storage_path):
            # Crear el archivo con un JSON vacío
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            with open(storage_path, 'w') as f:
                json.dump({}, f, indent=4)
        with open(storage_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def guardar_sesiones(self):
        storage_path = os.path.join('Storage', 'Settings', 'sessions.json')
        with open(storage_path, 'w') as f:
            json.dump(self.sesiones, f, indent=4)

    def mostrar_sesiones(self):
        """
        Muestra las sesiones cargadas en el QTreeWidget.
        """
        self.sessions_tree.clear()
        for nombre_sesion, fecha_hora in self.sesiones.items():
            uso_almacenamiento = self.calcular_tamano_sesion(nombre_sesion)
            porcentaje_uso = (uso_almacenamiento / self.calcular_espacio_ocupado()) * 100 if self.calcular_espacio_ocupado() > 0 else 0
            item = QTreeWidgetItem([nombre_sesion, fecha_hora, f"{self.format_size(uso_almacenamiento)} ({porcentaje_uso:.1f}% del espacio total ocupado)"])
            self.sessions_tree.addTopLevelItem(item)

        # Actualizar los botones según la selección actual
        self.actualizar_botones()

        # Ajustar automáticamente el tamaño de las columnas
        for column in range(self.sessions_tree.columnCount()):
            self.sessions_tree.resizeColumnToContents(column)
            current_width = self.sessions_tree.columnWidth(column)
            self.sessions_tree.setColumnWidth(column, current_width + 20)

        self.actualizar_espacio()

        # Mostrar u ocultar el botón "Ver carpeta de sesiones"
        self.view_sessions_folder_btn.setVisible(len(self.sesiones) > 0)

    def calcular_tamano_sesion(self, nombre_sesion):
        storage_r = os.path.join('Storage', 'Sessions', nombre_sesion)
        if os.path.exists(storage_r):
            return self.calcular_espacio_ocupado_directorio(storage_r)
        return 0

    def calcular_espacio_ocupado_directorio(self, directory):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except FileNotFoundError:
                    # Si el archivo no se encuentra, simplemente lo ignoramos
                    continue
        return total_size

    def calcular_espacio_ocupado(self):
        storage_dir = os.path.join('Storage', 'Sessions')
        if not os.path.exists(storage_dir):
            return 0
        return self.calcular_espacio_ocupado_directorio(storage_dir)

    def obtener_espacio_libre(self):
        disk_info = os.statvfs('/')
        free_space = disk_info.f_frsize * disk_info.f_bavail
        return free_space

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def actualizar_espacio(self):
        espacio_ocupado = self.calcular_espacio_ocupado()
        espacio_libre = self.obtener_espacio_libre()
        self.space_info_label.setText(f"Espacio total ocupado: {self.format_size(espacio_ocupado)}  -  Espacio libre: {self.format_size(espacio_libre)}")

    def actualizar_botones(self):
        """
        Controla la visibilidad de los botones en función de si se ha seleccionado una sesión.
        """
        selected_item = self.sessions_tree.currentItem()
        if selected_item:
            self.run_session_btn.setVisible(True)
            self.delete_session_btn.setVisible(True)
        else:
            self.run_session_btn.setVisible(False)
            self.delete_session_btn.setVisible(False)

    def crear_sesion(self):
        nombre_instancia = self.session_name_input.text().strip()
        chrome_ruta = self.config['chrome_ruta']

        if not nombre_instancia:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre para la sesión.", QMessageBox.Ok)
            return

        if nombre_instancia in self.sesiones:
            QMessageBox.warning(self, "Error", "La sesión ya existe.", QMessageBox.Ok)
            return

        # Registrar la nueva sesión
        fecha_hora_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sesiones[nombre_instancia] = fecha_hora_creacion
        self.guardar_sesiones()

        self.crear_instancia_chrome(nombre_instancia, chrome_ruta)
        self.mostrar_sesiones()
        self.session_name_input.clear()
        self.view_sessions_folder_btn.setVisible(True)

    def ejecutar_sesion(self):
        selected_item = self.sessions_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccionar Sesión", "Debe seleccionar una sesión antes de ejecutar.", QMessageBox.Ok)
            return

        nombre_sesion = selected_item.text(0)
        chrome_ruta = self.config['chrome_ruta']
        self.crear_instancia_chrome(nombre_sesion, chrome_ruta)

    def borrar_sesion(self):
        selected_item = self.sessions_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccionar Sesión", "Debe seleccionar una sesión antes de borrar.", QMessageBox.Ok)
            return

        nombre_sesion = selected_item.text(0)
        confirm = QMessageBox.question(self, "Confirmar Borrado", 
                                        f"¿Está seguro de que desea borrar la sesión '{nombre_sesion}' permanentemente?",
                                        QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            storage_r = os.path.join('Storage', 'Sessions', nombre_sesion)
            if os.path.exists(storage_r):
                # Eliminar el directorio de la sesión
                subprocess.call(['rm', '-rf', storage_r])

            # Eliminar el registro de la sesión
            if nombre_sesion in self.sesiones:
                del self.sesiones[nombre_sesion]
                self.guardar_sesiones()

            self.mostrar_sesiones()
            self.view_sessions_folder_btn.setVisible(len(self.sesiones) > 0)

    def crear_instancia_chrome(self, nombre_instancia: str, chrome_ruta: str):
        def find_available_port():
            for port in range(49152, 65536):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    result = s.connect_ex(('127.0.0.1', port))
                    if result != 0:  # Si la conexión falló, el puerto está libre
                        return port
            return None

        port = find_available_port()

        if port is None:
            QMessageBox.critical(self, "Error", "No se pudo encontrar un puerto disponible.", QMessageBox.Ok)
            return

        url = "https://www.google.com/"
        storage_r = os.path.join('Storage', 'Sessions', nombre_instancia)
        if not os.path.exists(storage_r):
            os.makedirs(storage_r)

        subprocess.Popen(
            [chrome_ruta, f"--remote-debugging-port={port}", f"--user-data-dir={storage_r}", url],
            start_new_session=True
        )

    def abrir_configuracion(self):
        config_dialog = ConfiguracionDialog(self.config, self)
        config_dialog.exec_()
        self.config = config_dialog.get_config()
        self.guardar_configuracion()

    def abrir_carpeta_sesiones(self):
        folder_path = os.path.abspath(os.path.join('Storage', 'Sessions'))
        if os.path.exists(folder_path):
            if os.name == 'nt':  # Para Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # Para macOS y Linux
                subprocess.call(('xdg-open', folder_path))
        else:
            QMessageBox.warning(self, "Error", "La carpeta de sesiones no existe.", QMessageBox.Ok)

    def actualizar_todo(self):
        # Recargar las sesiones existentes
        self.sesiones = self.cargar_sesiones_existentes()
        
        # Actualizar la visualización de las sesiones
        self.mostrar_sesiones()
        
        # Actualizar la información del espacio
        self.actualizar_espacio()

class ConfiguracionDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setGeometry(150, 150, 400, 150)
        self.config = config
        self.parent = parent  # Referencia al ChromeSessionManager

        layout = QVBoxLayout()
        
        # Sección de selección de tema
        tema_label = QLabel("Tema:", self)
        layout.addWidget(tema_label)

        self.tema_selector = QComboBox(self)
        self.tema_selector.addItems(["Oscuro", "Encendido"])
        self.tema_selector.setCurrentText(self.config.get("tema", "Oscuro"))
        layout.addWidget(self.tema_selector)

        # Campo de entrada para la ruta de Chrome
        chrome_ruta_label = QLabel("Ruta a Google Chrome:", self)
        layout.addWidget(chrome_ruta_label)

        self.chrome_ruta_input = QLineEdit(self)
        self.chrome_ruta_input.setText(self.config.get('chrome_ruta', '/usr/bin/google-chrome'))
        self.chrome_ruta_input.setFont(QFont("Arial", 12))
        self.chrome_ruta_input.setStyleSheet("padding: 10px; border-radius: 5px; border: 1px solid #ccc;")
        layout.addWidget(self.chrome_ruta_input)

        # Botón para seleccionar la ruta del ejecutable de Chrome
        select_chrome_ruta_btn = QPushButton("Seleccionar desde explorador...", self)
        select_chrome_ruta_btn.setFont(QFont("Arial", 12))
        select_chrome_ruta_btn.clicked.connect(self.seleccionar_ruta_chrome)
        layout.addWidget(select_chrome_ruta_btn)

        # Botón para guardar la configuración
        save_btn = QPushButton("Guardar", self)
        save_btn.setFont(QFont("Arial", 12, QFont.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #28a745;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self.guardar)
        layout.addWidget(save_btn)
        self.setLayout(layout)

    def seleccionar_ruta_chrome(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Google Chrome (chrome*);;Todos los archivos (*)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.chrome_ruta_input.setText(selected_file)

    def guardar(self):
        # Guardar el tema seleccionado
        self.config['tema'] = self.tema_selector.currentText()
        self.config['chrome_ruta'] = self.chrome_ruta_input.text()

        # Aplicar el tema en tiempo real
        self.parent.tema = self.config['tema']  # Actualizar el tema en el objeto principal
        self.parent.aplicar_tema()  # Aplicar el tema inmediatamente

        # Guardar la configuración en el archivo JSON
        self.parent.guardar_configuracion()

        self.accept()

    def get_config(self):
        return self.config

if __name__ == '__main__':
    app = QApplication([])
    app.setStyle("Fusion")
    window = ChromeSessionManager()
    window.show()
    app.exec_()