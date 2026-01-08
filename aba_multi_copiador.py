# aba_multi_copiador.py
import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QCheckBox
)
from PySide6.QtCore import Qt

class AbaMultiCopiador(QWidget):
    def __init__(self):
        super().__init__()
        self.arquivo_fonte = ""
        self.pasta_raiz = ""
        self.subpastas_encontradas = []
        self.setup_ui()

    def setup_ui(self):
        # ####################################################
        # ##               LAYOUT CORRIGIDO AQUI            ##
        # ##   Usando QVBoxLayout para colocar tudo "em cima" ##
        # ####################################################
        layout_principal = QVBoxLayout(self) # <-- Layout principal é VERTICAL
        layout_principal.setContentsMargins(12, 12, 12, 12)
        layout_principal.setSpacing(10)

        # --- 1. Selecionar Arquivo Fonte ---
        layout_principal.addWidget(QLabel("<b>1. Selecionar Arquivo Fonte:</b>"))
        
        layout_arquivo = QHBoxLayout()
        self.arquivo_fonte_label = QLabel("Nenhum arquivo selecionado")
        self.arquivo_fonte_label.setStyleSheet("font-style: italic;")
        btn_select_file = QPushButton("Selecionar Arquivo para Copiar")
        btn_select_file.clicked.connect(self.on_select_source_file)
        layout_arquivo.addWidget(self.arquivo_fonte_label)
        layout_arquivo.addStretch()
        layout_arquivo.addWidget(btn_select_file)
        layout_principal.addLayout(layout_arquivo)

        layout_principal.addSpacing(10)

        # --- 2. Selecionar Pasta Raiz ---
        layout_principal.addWidget(QLabel("<b>2. Selecionar Pasta Raiz (dos destinos):</b>"))
        
        layout_pasta = QHBoxLayout()
        self.pasta_raiz_label = QLabel("Nenhuma pasta selecionada")
        self.pasta_raiz_label.setStyleSheet("font-style: italic;")
        btn_select_root_folder = QPushButton("Selecionar Pasta Raiz")
        btn_select_root_folder.clicked.connect(self.on_select_root_folder)
        layout_pasta.addWidget(self.pasta_raiz_label)
        layout_pasta.addStretch()
        layout_pasta.addWidget(btn_select_root_folder)
        layout_principal.addLayout(layout_pasta)

        separator1 = QFrame(); separator1.setFrameShape(QFrame.Shape.HLine); separator1.setFrameShadow(QFrame.Shadow.Sunken); layout_principal.addWidget(separator1)

        # --- 3. Lista de Destinos ---
        layout_principal.addWidget(QLabel("<b>3. Selecionar Pastas de Destino:</b>"))
        
        self.checkbox_select_all = QCheckBox("Selecionar Todas / Nenhuma")
        self.checkbox_select_all.toggled.connect(self.on_toggle_select_all)
        layout_principal.addWidget(self.checkbox_select_all)
        
        self.pastas_list_widget = QListWidget()
        layout_principal.addWidget(self.pastas_list_widget, 1) # '1' faz a lista expandir

        separator2 = QFrame(); separator2.setFrameShape(QFrame.Shape.HLine); separator2.setFrameShadow(QFrame.Shadow.Sunken); layout_principal.addWidget(separator2)

        # --- 4. Ação Final ---
        layout_principal.addWidget(QLabel("<b>4. Ação Final:</b>"))
        
        layout_acao = QHBoxLayout()
        layout_acao.addStretch() # Empurra o botão para a direita
        btn_copiar = QPushButton("Copiar Arquivo para Pastas Selecionadas")
        btn_copiar.clicked.connect(self.on_copy_files)
        btn_copiar.setStyleSheet("padding: 8px;") 
        layout_acao.addWidget(btn_copiar)
        layout_principal.addLayout(layout_acao)

    def on_select_source_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo Fonte")
        if filepath:
            self.arquivo_fonte = filepath
            self.arquivo_fonte_label.setText(f"Arquivo: {os.path.basename(filepath)}")
            self.arquivo_fonte_label.setStyleSheet("font-style: normal;") 

    def on_select_root_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Raiz contendo as subpastas")
        if folder:
            self.pasta_raiz = folder
            self.pasta_raiz_label.setText(f"Pasta Raiz: {folder}")
            self.pasta_raiz_label.setStyleSheet("font-style: normal;")
            self.popular_lista_pastas()

    def popular_lista_pastas(self):
        self.pastas_list_widget.clear()
        self.subpastas_encontradas = []

        if not self.pasta_raiz: return

        try:
            for nome in os.listdir(self.pasta_raiz):
                caminho_completo = os.path.join(self.pasta_raiz, nome)
                if os.path.isdir(caminho_completo):
                    self.subpastas_encontradas.append(caminho_completo)
            
            if not self.subpastas_encontradas:
                self.pastas_list_widget.addItem("Nenhuma subpasta encontrada.")
                return

            for caminho_pasta in sorted(self.subpastas_encontradas):
                nome_pasta = os.path.basename(caminho_pasta)
                item = QListWidgetItem(nome_pasta)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, caminho_pasta)
                self.pastas_list_widget.addItem(item)
            
            self.checkbox_select_all.setChecked(False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível ler as subpastas: {e}")

    def on_toggle_select_all(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.pastas_list_widget.count()):
            item = self.pastas_list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(state)

    def on_copy_files(self):
        if not self.arquivo_fonte:
            QMessageBox.warning(self, "Erro", "Selecione um arquivo para copiar primeiro.")
            return

        pastas_selecionadas = []
        for i in range(self.pastas_list_widget.count()):
            item = self.pastas_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                caminho_completo = item.data(Qt.ItemDataRole.UserRole)
                pastas_selecionadas.append(caminho_completo)

        if not pastas_selecionadas:
            QMessageBox.warning(self, "Aviso", "Nenhuma pasta de destino foi selecionada.")
            return

        confirm = QMessageBox.question(self, "Confirmar Cópia", 
            f"Você está prestes a copiar o arquivo:\n\n{os.path.basename(self.arquivo_fonte)}\n\n"
            f"Para {len(pastas_selecionadas)} pastas de destino. Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.No:
            return

        nome_arquivo_fonte = os.path.basename(self.arquivo_fonte)
        erros = []
        sucessos = 0

        for pasta_destino in pastas_selecionadas:
            try:
                caminho_final_arquivo = os.path.join(pasta_destino, nome_arquivo_fonte)
                shutil.copy2(self.arquivo_fonte, caminho_final_arquivo)
                sucessos += 1
            except Exception as e:
                erros.append(f"Falha ao copiar para '{os.path.basename(pasta_destino)}': {e}")
        
        msg_final = f"{sucessos} cópias realizadas com sucesso."
        if erros:
            msg_final += f"\n\nFalha ao copiar para {len(erros)} pastas:\n" + "\n".join(erros)
        QMessageBox.information(self, "Concluído", msg_final)