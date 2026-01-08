# aba_otimizador_tga.py
import sys
import os
import math
import traceback
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QPalette
from PIL import Image # Biblioteca Pillow

# --- THREAD PARA TAREFAS PESADAS ---
class WorkerThread(QThread):
    progress_update = Signal(str)
    scan_complete = Signal(list)
    optimize_complete = Signal(str)

    def __init__(self, mode, files_to_process, use_rle=True):
        super().__init__()
        self.mode = mode
        self.files_to_process = files_to_process
        self.use_rle = use_rle

    def run(self):
        try:
            if self.mode == "scan":
                self.scan_files()
            elif self.mode == "optimize":
                self.optimize_files()
        except Exception as e:
            self.optimize_complete.emit(f"Erro na thread: {e}\n{traceback.format_exc()}")

    def get_tga_info(self, file_path):
        try:
            with Image.open(file_path) as img:
                # O Pillow lê o cabeçalho sem carregar a imagem inteira na RAM
                return img.width, img.height, img.mode
        except Exception as e:
            print(f"Erro ao ler {file_path}: {e}")
            return None, None, "Erro"

    def scan_files(self):
        mod_path = self.files_to_process
        results = []
        count = 0
        for root, dirs, files in os.walk(mod_path):
            for file in files:
                if file.lower().endswith(".tga"):
                    count += 1
                    if count % 50 == 0:
                        self.progress_update.emit(f"Escaneando... {count} arquivos.")
                    
                    file_path = os.path.join(root, file)
                    width, height, mode = self.get_tga_info(file_path)
                    
                    if width and height:
                        results.append([file_path, width, height, mode])
        
        self.scan_complete.emit(results)

    def optimize_files(self):
        sucessos = 0; erros = []; total = len(self.files_to_process)
        
        # files_to_process = [(file_path, new_w, new_h), ...]
        for i, (file_path, new_w, new_h) in enumerate(self.files_to_process):
            self.progress_update.emit(f"Processando {i+1}/{total}: {os.path.basename(file_path)}")
            
            try:
                with Image.open(file_path) as img:
                    # Redimensiona se necessário
                    if new_w != img.width or new_h != img.height:
                        # LANCZOS é o melhor filtro para downscaling (alta qualidade)
                        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    
                    # Salva sobrescrevendo o original
                    # compression='tga_rle' diminui o tamanho sem perder qualidade
                    if self.use_rle:
                        img.save(file_path, compression='tga_rle')
                    else:
                        img.save(file_path)
                        
                sucessos += 1
            except Exception as e:
                erros.append(f"Falha em '{os.path.basename(file_path)}': {e}")
        
        msg_final = f"{sucessos} de {total} texturas TGA otimizadas com sucesso."
        if erros: 
            msg_final += f"\n\n--- FALHA AO OTIMIZAR {len(erros)} TEXTURAS ---\n" + "\n".join(erros)
        self.optimize_complete.emit(msg_final)

# Item customizado para ordenação numérica
class QNumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, numeric_value):
        super().__init__(text); self.numeric_value = numeric_value
    def __lt__(self, other):
        return self.numeric_value < other.numeric_value

# --- CLASSE PRINCIPAL DA ABA ---
class AbaOtimizadorTGA(QWidget):
    def __init__(self):
        super().__init__()
        self.mod_folder_path = ""
        self.worker_thread = None
        self.default_text_brush = None
        self.setup_ui()

    def setup_ui(self):
        layout_principal = QHBoxLayout(self); layout_principal.setContentsMargins(12, 12, 12, 12); layout_principal.setSpacing(10)
        
        # --- COLUNA ESQUERDA ---
        coluna_esquerda = QVBoxLayout(); coluna_esquerda.setContentsMargins(0, 0, 10, 0)
        coluna_esquerda.addWidget(QLabel("<b>1. Selecionar Pasta:</b>"))
        self.mod_folder_label = QLabel("Nenhuma pasta selecionada"); self.mod_folder_label.setStyleSheet("font-style: italic;")
        btn_select = QPushButton("Selecionar Pasta Raiz"); btn_select.clicked.connect(self.on_select_mod_folder)
        coluna_esquerda.addWidget(btn_select); coluna_esquerda.addWidget(self.mod_folder_label)
        
        separator1 = QFrame(); separator1.setFrameShape(QFrame.Shape.HLine); separator1.setFrameShadow(QFrame.Shadow.Sunken); coluna_esquerda.addWidget(separator1)
        
        coluna_esquerda.addWidget(QLabel("<b>2. Opções de Otimização:</b>"))
        coluna_esquerda.addWidget(QLabel("Redimensionar TGA maior que:"))
        self.combo_res_from = QComboBox(); self.combo_res_from.addItems(["8192", "4096", "2048", "1024", "512"]); self.combo_res_from.setCurrentText("2048")
        coluna_esquerda.addWidget(self.combo_res_from)
        
        coluna_esquerda.addWidget(QLabel("Opção de Redimensionamento:"))
        self.combo_res_to = QComboBox()
        self.combo_res_to.addItem("(Não Redimensionar)", 0)
        self.combo_res_to.addItem("Descer 1 Nível", -1)
        self.combo_res_to.addItem("4096", 4096); self.combo_res_to.addItem("2048", 2048); self.combo_res_to.addItem("1024", 1024); self.combo_res_to.addItem("512", 512)
        self.combo_res_to.setCurrentIndex(0)
        coluna_esquerda.addWidget(self.combo_res_to)

        # ####################################################
        # ##               NOVA OPÇÃO AQUI                  ##
        # ####################################################
        self.check_force_pot = QCheckBox("Forçar Potência de 2 (POT)")
        self.check_force_pot.setToolTip("Corrige dimensões estranhas (ex: 1896x1179) para a potência de 2 mais próxima (ex: 2048x1024).\nIsso melhora muito a performance no jogo.")
        coluna_esquerda.addWidget(self.check_force_pot)

        self.check_rle = QCheckBox("Usar Compressão RLE")
        self.check_rle.setToolTip("RLE diminui o tamanho do arquivo sem perder qualidade.\nRecomendado deixar marcado.")
        self.check_rle.setChecked(True)
        coluna_esquerda.addWidget(self.check_rle)
        
        separator2 = QFrame(); separator2.setFrameShape(QFrame.Shape.HLine); separator2.setFrameShadow(QFrame.Shadow.Sunken); coluna_esquerda.addWidget(separator2)
        
        coluna_esquerda.addWidget(QLabel("<b>3. Ação:</b>"))
        self.btn_scan = QPushButton("1. Escanear TGA"); self.btn_scan.clicked.connect(self.on_scan_textures)
        coluna_esquerda.addWidget(self.btn_scan)
        self.btn_optimize = QPushButton("2. OTIMIZAR Selecionadas"); self.btn_optimize.clicked.connect(self.on_optimize_textures); self.btn_optimize.setEnabled(False); self.btn_optimize.setStyleSheet("padding: 8px;")
        coluna_esquerda.addWidget(self.btn_optimize)
        self.status_label = QLabel("Pronto."); coluna_esquerda.addWidget(self.status_label)
        coluna_esquerda.addStretch()

        # --- COLUNA DIREITA ---
        coluna_direita = QVBoxLayout(); coluna_direita.setContentsMargins(10, 0, 0, 0)
        coluna_direita.addWidget(QLabel("<b>Resultados:</b>"))
        self.checkbox_select_all = QCheckBox("Selecionar Todas / Nenhuma"); self.checkbox_select_all.toggled.connect(self.on_toggle_select_all); coluna_direita.addWidget(self.checkbox_select_all)
        
        self.tabela_texturas = QTableWidget()
        self.tabela_texturas.setColumnCount(5); self.tabela_texturas.setHorizontalHeaderLabels(["", "Arquivo", "Res. Atual", "Modo", "Nova Res."])
        self.tabela_texturas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch); self.tabela_texturas.setColumnWidth(0, 30); self.tabela_texturas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_texturas.setSortingEnabled(True)
        coluna_direita.addWidget(self.tabela_texturas)
        
        layout_principal.addLayout(coluna_esquerda, 1); layout_principal.addLayout(coluna_direita, 3)

        # Conexões de Preview
        self.combo_res_from.currentIndexChanged.connect(self.update_preview)
        self.combo_res_to.currentIndexChanged.connect(self.update_preview)
        self.check_force_pot.toggled.connect(self.update_preview) # Atualiza ao marcar
        
        self.default_text_brush = self.tabela_texturas.palette().brush(QPalette.ColorRole.Text)

    def on_select_mod_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta");
        if folder: self.mod_folder_path = folder; self.mod_folder_label.setText(f"Pasta: {folder}"); self.mod_folder_label.setStyleSheet("font-style: normal;")

    def on_toggle_select_all(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.tabela_texturas.rowCount()):
            item = self.tabela_texturas.item(i, 0)
            if item: item.setCheckState(state)

    # ####################################################
    # ##               LÓGICA DE POT (POWER OF TWO)     ##
    # ####################################################
    def get_closest_pot(self, value):
        """Retorna a potência de 2 mais próxima do valor dado."""
        if value <= 0: return 4
        # Calcula log base 2
        power = round(math.log(value, 2))
        return int(math.pow(2, power))

    def calculate_new_dims(self, width, height, threshold, new_max_dim_code, force_pot):
        # 1. Calcula as dimensões baseadas na redução normal (mantendo ratio)
        current_max_dim = max(width, height)
        new_w, new_h = width, height # Assume original por padrão
        
        needs_resize = False

        # Lógica de redução (se aplicável)
        if new_max_dim_code == -1: 
            if current_max_dim > threshold:
                new_w = width // 2; new_h = height // 2
                needs_resize = True
        elif new_max_dim_code > 0:
            new_max_dim = new_max_dim_code
            if current_max_dim > threshold and new_max_dim < current_max_dim:
                if width > height: ratio = height / width; new_w = new_max_dim; new_h = int(new_w * ratio)
                elif height > width: ratio = width / height; new_h = new_max_dim; new_w = int(new_h * ratio)
                else: new_w = new_max_dim; new_h = new_max_dim
                needs_resize = True
        
        # 2. Aplica a lógica de POT se estiver marcada
        if force_pot:
            pot_w = self.get_closest_pot(new_w)
            pot_h = self.get_closest_pot(new_h)
            
            # Se as dimensões POT forem diferentes das calculadas, precisamos redimensionar
            if pot_w != new_w or pot_h != new_h:
                new_w, new_h = pot_w, pot_h
                needs_resize = True

        # Se nada mudou em relação ao original, retorna None
        if not needs_resize:
            return None
            
        return max(4, new_w), max(4, new_h)

    @Slot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    @Slot(list)
    def on_scan_finished(self, results):
        self.scan_results = results 
        self.update_preview()
        self.btn_scan.setEnabled(True)

    @Slot()
    def update_preview(self):
        if not hasattr(self, 'scan_results') or not self.scan_results: return

        self.tabela_texturas.setRowCount(len(self.scan_results))
        threshold = int(self.combo_res_from.currentText())
        new_max_dim_code = self.combo_res_to.currentData()
        force_pot = self.check_force_pot.isChecked() # Pega o estado do checkbox
        files_to_optimize = 0
        
        self.tabela_texturas.blockSignals(True)
        for row, (file_path, width, height, mode) in enumerate(self.scan_results):
            
            new_dims = self.calculate_new_dims(width, height, threshold, new_max_dim_code, force_pot)
            
            check_item = QTableWidgetItem(); check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            name_item = QTableWidgetItem(os.path.basename(file_path)); name_item.setData(Qt.ItemDataRole.UserRole, file_path); name_item.setToolTip(file_path)
            res_item = QNumericTableWidgetItem(f"{width}x{height}", width * height)
            mode_item = QTableWidgetItem(mode)
            
            if new_dims:
                final_w, final_h = new_dims
                new_res_item = QNumericTableWidgetItem(f"{final_w}x{final_h}", final_w * final_h)
                check_item.setCheckState(Qt.CheckState.Checked)
                name_item.setForeground(QColor("yellow")); new_res_item.setForeground(QColor("yellow"))
                name_item.setData(Qt.ItemDataRole.UserRole + 1, (final_w, final_h))
                files_to_optimize += 1
            else:
                new_res_item = QNumericTableWidgetItem("(Manter)", 0)
                check_item.setCheckState(Qt.CheckState.Unchecked)
                name_item.setForeground(self.default_text_brush)
                new_res_item.setForeground(self.default_text_brush)
                name_item.setData(Qt.ItemDataRole.UserRole + 1, None) 

            self.tabela_texturas.setItem(row, 0, check_item)
            self.tabela_texturas.setItem(row, 1, name_item)
            self.tabela_texturas.setItem(row, 2, res_item)
            self.tabela_texturas.setItem(row, 3, mode_item)
            self.tabela_texturas.setItem(row, 4, new_res_item)
            
        self.tabela_texturas.blockSignals(False)
        self.checkbox_select_all.setChecked(files_to_optimize > 0)
        self.status_label.setText(f"Concluído! {len(self.scan_results)} arquivos. {files_to_optimize} para redimensionar.")
        self.btn_optimize.setEnabled(files_to_optimize > 0)

    def on_scan_textures(self):
        if not self.mod_folder_path:
            QMessageBox.warning(self, "Erro", "Selecione a pasta primeiro.")
            return

        self.btn_scan.setEnabled(False); self.btn_optimize.setEnabled(False)
        self.status_label.setText("Escaneando...")
        self.tabela_texturas.setRowCount(0)
        
        self.worker_thread = WorkerThread("scan", self.mod_folder_path)
        self.worker_thread.progress_update.connect(self.update_status)
        self.worker_thread.scan_complete.connect(self.on_scan_finished)
        self.worker_thread.start()

    @Slot(str)
    def on_optimize_finished(self, final_message):
        self.btn_scan.setEnabled(True); self.btn_optimize.setEnabled(False)
        self.status_label.setText("Otimização concluída.")
        QMessageBox.information(self, "Sucesso", final_message)
        self.tabela_texturas.setRowCount(0)
        self.scan_results = [] 

    def on_optimize_textures(self):
        files_to_process = []
        for row in range(self.tabela_texturas.rowCount()):
            check_item = self.tabela_texturas.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                name_item = self.tabela_texturas.item(row, 1)
                file_path = name_item.data(Qt.ItemDataRole.UserRole)
                new_dims = name_item.data(Qt.ItemDataRole.UserRole + 1)
                
                if file_path and new_dims:
                    files_to_process.append( (file_path, new_dims[0], new_dims[1]) )
        
        if not files_to_process: return

        self.btn_scan.setEnabled(False); self.btn_optimize.setEnabled(False)
        self.status_label.setText("Processando...")

        self.worker_thread = WorkerThread(
            mode="optimize",
            files_to_process=files_to_process,
            use_rle=self.check_rle.isChecked()
        )
        self.worker_thread.progress_update.connect(self.update_status)
        self.worker_thread.optimize_complete.connect(self.on_optimize_finished)
        self.worker_thread.start()