# aba_multi_copiador.py
import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt
from app_state import append_history

class AbaMultiCopiador(QWidget):
    def __init__(self):
        super().__init__()
        self.arquivo_fonte = ""
        self.pasta_raiz = ""
        self.subpastas_encontradas = []
        self.setup_ui()

    def setup_ui(self):
        from ui_helpers import step, field, muted, separator, elide_label

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        content = QVBoxLayout()
        content.setSpacing(12)
        fixed = QWidget()
        fixed.setFixedWidth(700)
        fixed.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        fixed_layout = QVBoxLayout(fixed)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.setSpacing(12)

        # --- 1. Arquivo fonte ---
        card_file = QFrame()
        card_file.setObjectName("Panel")
        lay_file = QVBoxLayout(card_file)
        lay_file.setContentsMargins(18, 16, 18, 16)
        lay_file.setSpacing(8)
        lay_file.addWidget(step("1 · ARQUIVO FONTE"))
        self.arquivo_fonte_label = muted("Nenhum arquivo selecionado")
        lay_file.addWidget(self.arquivo_fonte_label)
        btn_select_file = QPushButton("Selecionar arquivo para copiar")
        btn_select_file.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_file.clicked.connect(self.on_select_source_file)
        lay_file.addWidget(btn_select_file)
        fixed_layout.addWidget(card_file)

        # --- 2. Pasta raiz ---
        card_root = QFrame()
        card_root.setObjectName("Panel")
        lay_root = QVBoxLayout(card_root)
        lay_root.setContentsMargins(18, 16, 18, 16)
        lay_root.setSpacing(8)
        lay_root.addWidget(step("2 · PASTA RAIZ DOS DESTINOS"))
        self.pasta_raiz_label = muted("Nenhuma pasta selecionada")
        lay_root.addWidget(self.pasta_raiz_label)
        btn_select_root_folder = QPushButton("Selecionar pasta raiz")
        btn_select_root_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_root_folder.clicked.connect(self.on_select_root_folder)
        lay_root.addWidget(btn_select_root_folder)
        fixed_layout.addWidget(card_root)

        # --- 3. Destinos ---
        card_dest = QFrame()
        card_dest.setObjectName("Panel")
        lay_dest = QVBoxLayout(card_dest)
        lay_dest.setContentsMargins(16, 16, 16, 16)
        lay_dest.setSpacing(8)
        lay_dest.addWidget(step("3 · PASTAS DE DESTINO"))
        dest_head = QHBoxLayout()
        self.checkbox_select_all = QCheckBox("Selecionar todas")
        self.checkbox_select_all.toggled.connect(self.on_toggle_select_all)
        dest_head.addWidget(self.checkbox_select_all)
        dest_head.addStretch()
        self.dest_count = muted("")
        dest_head.addWidget(self.dest_count)
        lay_dest.addLayout(dest_head)

        self.pastas_list_widget = QListWidget()
        self.pastas_list_widget.setMinimumHeight(200)
        self.pastas_list_widget.itemChanged.connect(self._update_dest_count)
        self._empty_state = QLabel("Selecione a pasta raiz para listar as subpastas de destino.")
        self._empty_state.setObjectName("Muted")
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setVisible(False)
        lay_dest.addWidget(self.pastas_list_widget, 1)
        lay_dest.addWidget(self._empty_state, 1)

        lay_dest.addWidget(separator())
        btn_copiar = QPushButton("Copiar arquivo para pastas selecionadas")
        btn_copiar.setObjectName("PrimaryButton")
        btn_copiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copiar.setMinimumHeight(44)
        btn_copiar.clicked.connect(self.on_copy_files)
        lay_dest.addWidget(btn_copiar)
        fixed_layout.addWidget(card_dest, 1)

        content.addWidget(fixed)
        layout_principal.addLayout(content)

    def on_select_source_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo Fonte")
        if filepath:
            from ui_helpers import elide_label
            self.arquivo_fonte = filepath
            elide_label(self.arquivo_fonte_label, f"Arquivo: {os.path.basename(filepath)}", 640)

    def on_select_root_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Raiz contendo as subpastas")
        if folder:
            from ui_helpers import elide_label
            self.pasta_raiz = folder
            elide_label(self.pasta_raiz_label, f"Pasta raiz: {folder}", 640)
            self.popular_lista_pastas()

    def popular_lista_pastas(self):
        self.pastas_list_widget.clear()
        self.subpastas_encontradas = []
        self._empty_state.setVisible(False)
        self.pastas_list_widget.setVisible(True)
        self.dest_count.setText("")

        if not self.pasta_raiz:
            self._show_empty("Selecione a pasta raiz para listar as subpastas de destino.")
            return

        try:
            for nome in os.listdir(self.pasta_raiz):
                caminho_completo = os.path.join(self.pasta_raiz, nome)
                if os.path.isdir(caminho_completo):
                    self.subpastas_encontradas.append(caminho_completo)
            
            if not self.subpastas_encontradas:
                self._show_empty("Nenhuma subpasta encontrada nesta pasta raiz.")
                return

            for caminho_pasta in sorted(self.subpastas_encontradas):
                nome_pasta = os.path.basename(caminho_pasta)
                item = QListWidgetItem(nome_pasta)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setData(Qt.ItemDataRole.UserRole, caminho_pasta)
                item.setToolTip(caminho_pasta)
                self.pastas_list_widget.addItem(item)

            self.dest_count.setText(f"{len(self.subpastas_encontradas)} subpasta(s) encontrada(s)")
            
            self.checkbox_select_all.setChecked(False)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível ler as subpastas: {e}")

    def _show_empty(self, text):
        self._empty_state.setText(text)
        self._empty_state.setVisible(True)
        self.pastas_list_widget.setVisible(False)

    def on_toggle_select_all(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.pastas_list_widget.count()):
            item = self.pastas_list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(state)

    def _update_dest_count(self, *args):
        total = marked = 0
        for i in range(self.pastas_list_widget.count()):
            item = self.pastas_list_widget.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                total += 1
                if item.checkState() == Qt.CheckState.Checked:
                    marked += 1
        if total:
            self.dest_count.setText(f"{marked} de {total} marcada(s)")

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
        append_history(
            "Copiador Múltiplo",
            "Cópia em lote",
            f"Arquivo: {nome_arquivo_fonte} | Sucesso: {sucessos}/{len(pastas_selecionadas)} | Erros: {len(erros)}"
        )
        QMessageBox.information(self, "Concluído", msg_final)