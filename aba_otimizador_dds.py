# aba_otimizador_dds.py
import sys
import os
import re
import struct
import math
import subprocess
import traceback
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QEvent
from PySide6.QtGui import QColor, QBrush, QPalette

# --- THREAD PARA TAREFAS PESADAS ---
class WorkerThread(QThread):
    progress_update = Signal(str)
    scan_complete = Signal(list)
    optimize_complete = Signal(str)

    def __init__(self, mode, files_to_process, texconv_path=None, protect_alpha=False):
        super().__init__()
        self.mode = mode
        self.files_to_process = files_to_process
        self.texconv_path = texconv_path
        self.protect_alpha = protect_alpha

    def run(self):
        try:
            if self.mode == "scan":
                self.scan_files()
            elif self.mode == "optimize":
                self.optimize_files()
        except Exception as e:
            self.optimize_complete.emit(f"Erro na thread: {e}\n{traceback.format_exc()}")

    def get_dds_info(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                f.seek(4); header = f.read(124)
                height = struct.unpack_from('<I', header, 8)[0]
                width = struct.unpack_from('<I', header, 12)[0]
                pf_flags = struct.unpack_from('<I', header, 76)[0]
                four_cc_bytes = struct.unpack_from('4s', header, 80)[0]
                four_cc = "N/A"
                if pf_flags & 0x4: # DDPF_FOURCC
                    four_cc = four_cc_bytes.decode('ascii', errors='ignore').strip()
                    if '\x00' in four_cc or len(four_cc) == 0: four_cc = "Outro/Raw"
                elif pf_flags & 0x40: # DDPF_RGB
                    four_cc = "RGB N/Comprimido"
                return width, height, four_cc
        except Exception as e:
            print(f"Erro ao ler cabeçalho de {file_path}: {e}")
            return None, None, "Erro Leitura"

    def is_alpha_opaque(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                f.seek(128)
                opaque_alpha_block_pattern = b'\xFF\xFF\x00\x00\x00\x00\x00\x00'
                while True:
                    chunk = f.read(16)
                    if not chunk: break
                    if len(chunk) < 8: break
                    alpha_block = chunk[0:8]
                    if alpha_block != opaque_alpha_block_pattern:
                        return False
            return True
        except Exception as e:
            print(f"Erro ao checar alfa de {file_path}: {e}")
            return False

    def scan_files(self):
        mod_path = self.files_to_process
        results = []
        count = 0
        for root, dirs, files in os.walk(mod_path):
            for file in files:
                if file.lower().endswith(".dds"):
                    count += 1
                    if count % 20 == 0:
                        self.progress_update.emit(f"Escaneando... {count} arquivos.")
                    
                    file_path = os.path.join(root, file)
                    width, height, dds_format = self.get_dds_info(file_path)
                    
                    if not (width and height):
                        continue
                    
                    has_modified_alpha = False
                    if self.protect_alpha and (dds_format == "BC3_UNORM" or dds_format == "DXT5"):
                        self.progress_update.emit(f"Analisando Alfa: {file}...")
                        if not self.is_alpha_opaque(file_path):
                            has_modified_alpha = True
                            
                    results.append([file_path, width, height, dds_format, has_modified_alpha])
        
        self.scan_complete.emit(results)

    def optimize_files(self):
        sucessos = 0; erros = []; total = len(self.files_to_process)
        for i, (file_path, new_w, new_h, new_format) in enumerate(self.files_to_process):
            self.progress_update.emit(f"Processando {i+1}/{total}: {os.path.basename(file_path)}")
            output_path = os.path.dirname(file_path)
            command = [
                f'"{self.texconv_path}"', "-y", "-o", f'"{output_path}"',
                "-w", str(new_w), "-h", str(new_h),
                "-f", new_format,
                "-m", "0",
                f'"{file_path}"'
            ]
            command_str = " ".join(command)
            try:
                result = subprocess.run(command_str, check=True, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                sucessos += 1
            except subprocess.CalledProcessError as e:
                error_output = e.stderr.strip() if e.stderr else "Nenhuma saída de erro do texconv.exe."
                if not error_output and e.stdout:
                    error_output = e.stdout.strip()
                erros.append(f"Falha em '{os.path.basename(file_path)}':\n    ERRO: {error_output}\n")
            except Exception as e:
                erros.append(f"Erro de Python em '{os.path.basename(file_path)}': {traceback.format_exc()}")
        
        msg_final = f"{sucessos} de {total} texturas otimizadas com sucesso."
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
class AbaOtimizadorDDS(QWidget):
    def __init__(self):
        super().__init__()
        self.mod_folder_path = ""
        self.texconv_path = ""
        self.worker_thread = None
        
        self.is_dragging_checkbox = False
        self.drag_check_state = Qt.CheckState.Unchecked
        self.last_drag_row = -1
        
        self.setup_ui()
        self.check_for_local_texconv()

    def setup_ui(self):
        layout_principal = QHBoxLayout(self); layout_principal.setContentsMargins(12, 12, 12, 12); layout_principal.setSpacing(10)
        
        coluna_esquerda = QVBoxLayout(); coluna_esquerda.setContentsMargins(0, 0, 10, 0)
        coluna_esquerda.addWidget(QLabel("<b>1. Selecionar Pasta do Mod:</b>")); self.mod_folder_label = QLabel("Nenhuma pasta selecionada"); self.mod_folder_label.setStyleSheet("font-style: italic;")
        btn_select_mod_folder = QPushButton("Selecionar Pasta Raiz do Mod"); btn_select_mod_folder.clicked.connect(self.on_select_mod_folder)
        coluna_esquerda.addWidget(btn_select_mod_folder); coluna_esquerda.addWidget(self.mod_folder_label); coluna_esquerda.addSpacing(10)
        coluna_esquerda.addWidget(QLabel("<b>2. Ferramenta (texconv.exe):</b>")); self.texconv_label = QLabel("Nenhum executável selecionado"); self.texconv_label.setStyleSheet("font-style: italic;")
        btn_select_texconv = QPushButton("Localizar texconv.exe"); btn_select_texconv.clicked.connect(self.on_select_texconv)
        coluna_esquerda.addWidget(btn_select_texconv); coluna_esquerda.addWidget(self.texconv_label)
        separator1 = QFrame(); separator1.setFrameShape(QFrame.Shape.HLine); separator1.setFrameShadow(QFrame.Shadow.Sunken); coluna_esquerda.addWidget(separator1)
        
        coluna_esquerda.addWidget(QLabel("<b>3. Opções de Otimização:</b>"))
        
        coluna_esquerda.addWidget(QLabel("Otimizar texturas com dimensão MAIOR que:"))
        self.combo_res_from = QComboBox(); self.combo_res_from.addItems(["8192", "4096", "2048", "1024", "512", "256", "128"]); self.combo_res_from.setCurrentText("1024")
        coluna_esquerda.addWidget(self.combo_res_from)

        coluna_esquerda.addWidget(QLabel("Opção de Redimensionamento:"))
        self.combo_res_to = QComboBox()
        self.combo_res_to.addItem("(Não Redimensionar)", 0)
        self.combo_res_to.addItem("Descer 1 Nível", -1)
        self.combo_res_to.addItem("4096", 4096); self.combo_res_to.addItem("2048", 2048); self.combo_res_to.addItem("1024", 1024); self.combo_res_to.addItem("512", 512)
        self.combo_res_to.setCurrentIndex(0) # Padrão "Não Redimensionar"
        coluna_esquerda.addWidget(self.combo_res_to)
        
        coluna_esquerda.addWidget(QLabel("Forçar Formato de Saída:"))
        self.combo_format_to = QComboBox()
        self.combo_format_to.addItem("(Manter Original)", "MANTER")
        self.combo_format_to.addItem("BC1_UNORM (DXT1 - Sem Alpha)", "BC1_UNORM")
        self.combo_format_to.addItem("BC3_UNORM (DXT5 - Com Alpha)", "BC3_UNORM")
        self.combo_format_to.addItem("BC5_UNORM (ATI2 - Mapas Normais)", "BC5_UNORM")
        self.combo_format_to.addItem("BC7_UNORM (DX11 - Alta Qualidade)", "BC7_UNORM")
        coluna_esquerda.addWidget(self.combo_format_to)

        self.check_protect_alpha = QCheckBox("Proteger Alfas Modificados")
        self.check_protect_alpha.setToolTip("Se marcado, impede que texturas DXT5 com transparência\n"
                                            "sejam forçadas para DXT1, mesmo que você mande.\n"
                                            "AVISO: Torna o escaneamento MUITO mais lento.")
        self.check_protect_alpha.setChecked(True)
        coluna_esquerda.addWidget(self.check_protect_alpha)
        
        separator2 = QFrame(); separator2.setFrameShape(QFrame.Shape.HLine); separator2.setFrameShadow(QFrame.Shadow.Sunken); coluna_esquerda.addWidget(separator2)
        coluna_esquerda.addWidget(QLabel("<b>4. Ação:</b>")); self.btn_scan = QPushButton("1. Escanear Texturas (Gerar Preview)"); self.btn_scan.clicked.connect(self.on_scan_textures)
        coluna_esquerda.addWidget(self.btn_scan); self.btn_optimize = QPushButton("2. OTIMIZAR Texturas Selecionadas"); self.btn_optimize.clicked.connect(self.on_optimize_textures); self.btn_optimize.setEnabled(False); self.btn_optimize.setStyleSheet("padding: 8px;"); coluna_esquerda.addWidget(self.btn_optimize)
        self.status_label = QLabel("Pronto."); coluna_esquerda.addWidget(self.status_label); coluna_esquerda.addStretch();
        
        coluna_direita = QVBoxLayout(); coluna_direita.setContentsMargins(10, 0, 0, 0)
        coluna_direita.addWidget(QLabel("<b>Resultados do Escaneamento:</b>")); self.checkbox_select_all = QCheckBox("Selecionar Todas / Nenhuma"); self.checkbox_select_all.toggled.connect(self.on_toggle_select_all); coluna_direita.addWidget(self.checkbox_select_all)
        self.tabela_texturas = QTableWidget()
        self.tabela_texturas.setColumnCount(6); self.tabela_texturas.setHorizontalHeaderLabels(["", "Arquivo", "Res. Atual", "Formato Atual", "Nova Res.", "Novo Formato"])
        self.tabela_texturas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch); self.tabela_texturas.setColumnWidth(0, 30); self.tabela_texturas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_texturas.setSortingEnabled(True)
        coluna_direita.addWidget(self.tabela_texturas)
        
        layout_principal.addLayout(coluna_esquerda, 1); layout_principal.addLayout(coluna_direita, 3)

        self.combo_res_from.currentIndexChanged.connect(self.update_preview)
        self.combo_res_to.currentIndexChanged.connect(self.update_preview)
        self.combo_format_to.currentIndexChanged.connect(self.update_preview)
        self.check_protect_alpha.toggled.connect(self.update_preview)
        
        # [MUDANÇA] Instalando o filtro no VIEWPORT da tabela
        self.tabela_texturas.viewport().installEventFilter(self)
        
        self.default_text_brush = self.tabela_texturas.palette().brush(QPalette.ColorRole.Text)


    def check_for_local_texconv(self):
        local_path = os.path.join("tools", "texconv", "texconv.exe")
        if os.path.exists(local_path):
            full_path = os.path.abspath(local_path); self.texconv_path = full_path; self.texconv_label.setText(f"Encontrado: {full_path}"); self.texconv_label.setStyleSheet("font-style: normal; color: green;"); self.texconv_label.setToolTip(full_path)
        else: self.texconv_label.setStyleSheet("font-style: italic; color: red;"); self.texconv_label.setText("texconv.exe não encontrado na pasta 'tools'")

    def on_select_mod_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Raiz do Mod");
        if folder: self.mod_folder_path = folder; self.mod_folder_label.setText(f"Pasta: {folder}"); self.mod_folder_label.setStyleSheet("font-style: normal;")

    def on_select_texconv(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecionar texconv.exe", "", "Executables (*.exe)");
        if filepath: self.texconv_path = filepath; self.texconv_label.setText(f"Caminho: {filepath}"); self.texconv_label.setStyleSheet("font-style: normal;")

    def on_toggle_select_all(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.tabela_texturas.rowCount()):
            item = self.tabela_texturas.item(i, 0)
            if item: item.setCheckState(state)

    def calculate_new_dims(self, width, height, threshold, new_max_dim_code):
        current_max_dim = max(width, height)
        if current_max_dim <= threshold:
            return None
        if new_max_dim_code == 0:
            return None
        if new_max_dim_code == -1:
            new_w = width // 2; new_h = height // 2
        else:
            new_max_dim = new_max_dim_code
            if new_max_dim > current_max_dim: # Não faz upscale
                return None
            
            if width > height: ratio = height / width; new_w = new_max_dim; new_h = int(new_w * ratio)
            elif height > width: ratio = width / height; new_h = new_max_dim; new_w = int(new_h * ratio)
            else: new_w = new_max_dim; new_h = new_max_dim
            
        new_w = max(4, new_w - (new_w % 4)); new_h = max(4, new_h - (new_h % 4))
        return new_w, new_h

    @Slot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    @Slot(list)
    def on_scan_finished(self, results):
        self.tabela_texturas.setRowCount(len(results))
        self.tabela_texturas.blockSignals(True)
        
        for row, (file_path, width, height, dds_format, has_modified_alpha) in enumerate(results):
            
            name_item = QTableWidgetItem(os.path.basename(file_path))
            name_item.setToolTip(file_path)
            raw_data = (file_path, width, height, dds_format, has_modified_alpha)
            name_item.setData(Qt.ItemDataRole.UserRole, raw_data)

            check_item = QTableWidgetItem(); check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            res_item = QNumericTableWidgetItem(f"{width}x{height}", width * height)
            format_item = QTableWidgetItem(dds_format)
            
            new_res_item = QNumericTableWidgetItem("", 0)
            new_format_item = QTableWidgetItem("")

            self.tabela_texturas.setItem(row, 0, check_item)
            self.tabela_texturas.setItem(row, 1, name_item)
            self.tabela_texturas.setItem(row, 2, res_item)
            self.tabela_texturas.setItem(row, 3, format_item)
            self.tabela_texturas.setItem(row, 4, new_res_item)
            self.tabela_texturas.setItem(row, 5, new_format_item)
        
        self.tabela_texturas.blockSignals(False)
        self.btn_scan.setEnabled(True)
        
        self.update_preview()
        self.status_label.setText(f"Escaneamento concluído! {len(results)} texturas encontradas.")

    @Slot()
    def update_preview(self):
        if self.tabela_texturas.rowCount() == 0:
            return 

        self.tabela_texturas.blockSignals(True)

        threshold = int(self.combo_res_from.currentText())
        new_max_dim_code = self.combo_res_to.currentData()
        format_desejado = self.combo_format_to.currentData()
        protect_alpha_enabled = self.check_protect_alpha.isChecked()
        
        files_to_optimize = 0

        for row in range(self.tabela_texturas.rowCount()):
            check_item = self.tabela_texturas.item(row, 0)
            name_item = self.tabela_texturas.item(row, 1)
            new_res_item = self.tabela_texturas.item(row, 4)
            new_format_item = self.tabela_texturas.item(row, 5)

            raw_data = name_item.data(Qt.ItemDataRole.UserRole)
            if not raw_data: continue
            
            file_path, width, height, dds_format, has_modified_alpha = raw_data

            new_dims = self.calculate_new_dims(width, height, threshold, new_max_dim_code)
            
            final_new_format_str = dds_format
            needs_format_change = False

            if format_desejado != "MANTER":
                if (protect_alpha_enabled and
                    (dds_format == "BC3_UNORM" or dds_format == "DXT5") and
                    has_modified_alpha and
                    format_desejado == "BC1_UNORM"):
                    
                    final_new_format_str = f"{dds_format} (Protegido)"
                    needs_format_change = False
                else:
                    final_new_format_str = format_desejado
                    needs_format_change = True
                    
            needs_resize = (new_dims is not None)
            needs_optimization = needs_resize or needs_format_change
            
            name_item.setForeground(self.default_text_brush)
            new_res_item.setForeground(self.default_text_brush)
            new_format_item.setForeground(self.default_text_brush)

            if needs_optimization:
                final_w, final_h = new_dims if new_dims else (width, height)
                
                new_res_item.setText(f"{final_w}x{final_h}")
                if isinstance(new_res_item, QNumericTableWidgetItem): 
                    new_res_item.numeric_value = final_w * final_h
                new_format_item.setText(final_new_format_str)
                
                check_item.setCheckState(Qt.CheckState.Checked)
                
                if new_dims:
                    name_item.setForeground(QColor("yellow"))
                    new_res_item.setForeground(QColor("yellow"))
                if needs_format_change:
                    new_format_item.setForeground(QColor("cyan"))
                
                name_item.setData(Qt.ItemDataRole.UserRole + 1, (final_w, final_h))
                name_item.setData(Qt.ItemDataRole.UserRole + 2, final_new_format_str.split(" ")[0])
                
                files_to_optimize += 1
            else:
                new_res_item.setText("(Manter)")
                if isinstance(new_res_item, QNumericTableWidgetItem):
                    new_res_item.numeric_value = 0
                new_format_item.setText(final_new_format_str if "Protegido" in final_new_format_str else "(Manter)")
                
                check_item.setCheckState(Qt.CheckState.Unchecked)
                
                name_item.setData(Qt.ItemDataRole.UserRole + 1, None)
                name_item.setData(Qt.ItemDataRole.UserRole + 2, None)

        self.tabela_texturas.blockSignals(False)
        self.checkbox_select_all.setChecked(files_to_optimize > 0)
        self.status_label.setText(f"{self.tabela_texturas.rowCount()} texturas. {files_to_optimize} para otimizar com as opções atuais.")
        self.btn_optimize.setEnabled(files_to_optimize > 0)


    def on_scan_textures(self):
        if not self.mod_folder_path:
            QMessageBox.warning(self, "Erro", "Selecione a 'Pasta Raiz do Mod' primeiro.")
            return

        threshold = int(self.combo_res_from.currentText())
        new_max_dim_code = self.combo_res_to.currentData()
        
        if new_max_dim_code != -1 and new_max_dim_code != 0 and new_max_dim_code > threshold:
            QMessageBox.warning(self, "Erro de Lógica", "A nova dimensão MÁXIMA deve ser MENOR ou IGUAL à dimensão MÍNIMA para redimensionar.\n\n(A menos que você use 'Descer 1 Nível' ou 'Não Redimensionar')")
            return
            
        if self.check_protect_alpha.isChecked():
            confirm = QMessageBox.question(self, "Aviso de Lentidão",
                                           "A proteção de alfa está ativada.\n\n"
                                           "Isso é MUITO lento, pois precisa ler cada pixel de cada textura DXT5.\n\n"
                                           "Deseja continuar?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.No:
                return

        self.btn_scan.setEnabled(False); self.btn_optimize.setEnabled(False)
        self.status_label.setText("Escaneando, por favor aguarde...")
        self.tabela_texturas.setRowCount(0)
        
        self.worker_thread = WorkerThread(
            mode="scan",
            files_to_process=self.mod_folder_path,
            texconv_path=None,
            protect_alpha=self.check_protect_alpha.isChecked()
        )
        self.worker_thread.progress_update.connect(self.update_status)
        self.worker_thread.scan_complete.connect(self.on_scan_finished)
        self.worker_thread.start()

    @Slot(str)
    def on_optimize_finished(self, final_message):
        self.btn_scan.setEnabled(True); self.btn_optimize.setEnabled(False)
        self.status_label.setText("Otimização concluída. Faça um novo scan para ver os resultados.")
        QMessageBox.information(self, "Otimização Concluída", final_message)
        self.tabela_texturas.setRowCount(0)

    def on_optimize_textures(self):
        if not self.texconv_path or not os.path.exists(self.texconv_path):
            QMessageBox.warning(self, "Erro", "O executável 'texconv.exe' não foi encontrado. Verifique a configuração.")
            self.check_for_local_texconv(); return
            
        files_to_process = []
        for row in range(self.tabela_texturas.rowCount()):
            check_item = self.tabela_texturas.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                name_item = self.tabela_texturas.item(row, 1)
                format_item_atual = self.tabela_texturas.item(row, 3) 
                
                file_path_data = name_item.data(Qt.ItemDataRole.UserRole)
                new_dims_data = name_item.data(Qt.ItemDataRole.UserRole + 1)
                new_format_data = name_item.data(Qt.ItemDataRole.UserRole + 2)

                if not file_path_data: continue
                
                file_path = file_path_data[0]
                
                if new_format_data:
                    new_format = new_format_data
                else: 
                    new_format = format_item_atual.text().split(" ")[0]
                
                if new_dims_data:
                    final_w, final_h = new_dims_data
                else: 
                    w_h_item = self.tabela_texturas.item(row, 2)
                    w, h = map(int, w_h_item.text().split('x'))
                    final_w, final_h = w, h

                if file_path:
                    files_to_process.append( (file_path, final_w, final_h, new_format) )
        
        if not files_to_process:
            QMessageBox.warning(self, "Aviso", "Nenhuma textura está marcada para otimização.")
            return

        self.btn_scan.setEnabled(False); self.btn_optimize.setEnabled(False)
        self.status_label.setText("Otimizando, isso pode demorar...")

        self.worker_thread = WorkerThread(
            mode="optimize",
            files_to_process=files_to_process,
            texconv_path=self.texconv_path,
            protect_alpha=False
        )
        self.worker_thread.progress_update.connect(self.update_status)
        self.worker_thread.optimize_complete.connect(self.on_optimize_finished)
        self.worker_thread.start()

    # --- Funções do Filtro de Eventos para "Arrastar" ---
    
    def eventFilter(self, source, event):
        # [MUDANÇA] Checando o VIEWPORT
        if source is self.tabela_texturas.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                if self.handle_mouse_press(event):
                    return True # "Consome" o evento
            elif event.type() == QEvent.Type.MouseMove:
                if self.handle_mouse_move(event):
                    return True # "Consome" o evento
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if self.handle_mouse_release(event):
                    return True # "Consome" o evento
        
        return super().eventFilter(source, event)

    def handle_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.tabela_texturas.indexAt(event.pos())
            row, col = index.row(), index.column()

            if col == 0 and row != -1:
                item = self.tabela_texturas.item(row, col)
                if not item: return False

                current_state = item.checkState()
                new_state = Qt.CheckState.Checked if current_state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
                item.setCheckState(new_state)
                
                self.is_dragging_checkbox = True
                self.drag_check_state = new_state
                self.last_drag_row = row
                return True
        return False

    def handle_mouse_move(self, event):
        # [MUDANÇA] Checagem extra se o botão ainda está pressionado
        if self.is_dragging_checkbox and (event.buttons() & Qt.MouseButton.LeftButton):
            index = self.tabela_texturas.indexAt(event.pos())
            row, col = index.row(), index.column()

            if col == 0 and row != -1 and row != self.last_drag_row:
                item = self.tabela_texturas.item(row, col)
                if not item: return True

                item.setCheckState(self.drag_check_state)
                self.last_drag_row = row
            
            return True 
        return False

    def handle_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging_checkbox:
            self.is_dragging_checkbox = False
            self.last_drag_row = -1
            return True 
        return False