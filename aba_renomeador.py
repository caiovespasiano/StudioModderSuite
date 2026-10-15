# aba_renomeador.py
import sys
import os
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QCheckBox, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from app_state import append_history

class BlockItem:
    def __init__(self, text, type_="prefix", config=None):
        self.text = text
        self.type_ = type_
        self.config = config if config else {}
    def clone(self):
        if self.type_ in ('num', 'alpha'):
            return self
        return BlockItem(self.text, self.type_, self.config.copy())

class AbaRenomeador(QWidget):
    def __init__(self):
        super().__init__()
        self.arquivos_selecionados = []
        self.prefix_store = []
        self.name_blocks = []
        self.alpha_letters = list("abcdefghijklmnopqrstuvwxyz")
        self.setup_ui()

    def setup_ui(self):
        from ui_helpers import step, field, hint, muted, separator

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(12)

        # --- PAINEL ESQUERDO (arquivos + prévia) ---
        left_panel = QFrame()
        left_panel.setObjectName("Panel")
        coluna_esquerda = QVBoxLayout(left_panel)
        coluna_esquerda.setContentsMargins(16, 16, 16, 16)
        coluna_esquerda.setSpacing(8)

        coluna_esquerda.addWidget(step("1 · ARQUIVOS"))
        btn_selecionar = QPushButton("Selecionar arquivos")
        btn_selecionar.clicked.connect(self.on_select_files)
        coluna_esquerda.addWidget(btn_selecionar)

        self.files_count = muted("Nenhum arquivo selecionado")
        coluna_esquerda.addWidget(self.files_count)

        self.tabela_arquivos = QTableWidget()
        self.tabela_arquivos.setColumnCount(2)
        self.tabela_arquivos.setHorizontalHeaderLabels(["Nome Original", "Novo Nome (Preview)"])
        self.tabela_arquivos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_arquivos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        coluna_esquerda.addWidget(self.tabela_arquivos)

        layout_principal.addWidget(left_panel, 2)

        # --- PAINEL DIREITO (montagem do nome) ---
        right_panel = QFrame()
        right_panel.setObjectName("Panel")
        right_panel.setFixedWidth(400)
        coluna_direita = QVBoxLayout(right_panel)
        coluna_direita.setContentsMargins(16, 16, 16, 16)
        coluna_direita.setSpacing(8)

        coluna_direita.addWidget(step("2 · BLOCOS DO NOME"))

        seq_grid = QGridLayout()
        seq_grid.setContentsMargins(0, 0, 0, 0)
        seq_grid.setHorizontalSpacing(8)
        seq_grid.setVerticalSpacing(8)
        seq_grid.setColumnStretch(1, 1)
        self.num_check = QCheckBox("Sequência numérica")
        self.num_format = QComboBox()
        self.num_format.addItems(["0", "00", "000"])
        self.num_format.setFixedWidth(90)
        self.num_add_btn = QPushButton("Adicionar")
        self.num_add_btn.clicked.connect(self.on_add_num_block)
        seq_grid.addWidget(self.num_check, 0, 0)
        seq_grid.addWidget(self.num_format, 0, 1)
        seq_grid.addWidget(self.num_add_btn, 0, 2)
        self.alpha_check = QCheckBox("Sequência alfabética")
        alpha_range = QHBoxLayout()
        alpha_range.setSpacing(6)
        self.alpha_start = QComboBox()
        self.alpha_start.addItems(self.alpha_letters)
        self.alpha_start.setFixedWidth(56)
        self.alpha_end = QComboBox()
        self.alpha_end.addItems(self.alpha_letters)
        self.alpha_end.setFixedWidth(56)
        self.alpha_format = QComboBox()
        self.alpha_format.addItems(["a", "aa", "aaa"])
        self.alpha_format.setFixedWidth(70)
        alpha_range.addWidget(QLabel("de"))
        alpha_range.addWidget(self.alpha_start)
        alpha_range.addWidget(QLabel("até"))
        alpha_range.addWidget(self.alpha_end)
        alpha_range.addWidget(QLabel("formato"))
        alpha_range.addWidget(self.alpha_format)
        alpha_range.addStretch()
        self.alpha_add_btn = QPushButton("Adicionar")
        self.alpha_add_btn.clicked.connect(self.on_add_alpha_block)
        seq_grid.addWidget(self.alpha_check, 1, 0)
        seq_grid.addLayout(alpha_range, 1, 1, 1, 2)
        seq_grid.addWidget(self.alpha_add_btn, 2, 2)
        coluna_direita.addLayout(seq_grid)
        self.num_format.setEnabled(False); self.num_add_btn.setEnabled(False); self.alpha_start.setEnabled(False); self.alpha_end.setEnabled(False); self.alpha_format.setEnabled(False); self.alpha_add_btn.setEnabled(False)
        self.num_check.toggled.connect(lambda c: (self.num_format.setEnabled(c), self.num_add_btn.setEnabled(c)))
        self.alpha_check.toggled.connect(lambda c: (self.alpha_start.setEnabled(c), self.alpha_end.setEnabled(c), self.alpha_format.setEnabled(c), self.alpha_add_btn.setEnabled(c)))

        prefix_row = QHBoxLayout()
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Prefixo ex.: skin_")
        self.prefix_input.returnPressed.connect(self.on_prefix_add)
        self.prefix_add_btn = QPushButton("Adicionar")
        self.prefix_add_btn.clicked.connect(self.on_prefix_add)
        prefix_row.addWidget(self.prefix_input, 1)
        prefix_row.addWidget(self.prefix_add_btn)
        coluna_direita.addLayout(prefix_row)

        coluna_direita.addWidget(field("Blocos disponíveis"))
        self.prefix_list = QListWidget()
        self.prefix_list.itemDoubleClicked.connect(self.on_prefix_double)
        coluna_direita.addWidget(self.prefix_list)

        coluna_direita.addWidget(field("Montagem do nome"))
        self.assembly = QListWidget()
        self.assembly.itemDoubleClicked.connect(self.on_assembly_double_clicked)
        coluna_direita.addWidget(self.assembly)
        coluna_direita.addWidget(hint("Duplo-clique move entre as listas · confira a prévia na tabela"))

        coluna_direita.addWidget(separator())
        btn_renomear = QPushButton("Renomear arquivos")
        btn_renomear.setObjectName("PrimaryButton")
        btn_renomear.setMinimumHeight(40)
        btn_renomear.clicked.connect(self.on_rename_files)
        coluna_direita.addWidget(btn_renomear)

        layout_principal.addWidget(right_panel)

    # ... (o resto do código do aba_renomeador.py permanece o mesmo) ...
    def on_select_files(self):
        arquivos, _ = QFileDialog.getOpenFileNames(self, "Selecione os arquivos para renomear")
        if arquivos:
            self.arquivos_selecionados = sorted(arquivos) # Ordena os arquivos para consistência
            self.popular_tabela()
            self.update_all_previews()

    def popular_tabela(self):
        self.tabela_arquivos.setRowCount(len(self.arquivos_selecionados))
        for i, caminho_arquivo in enumerate(self.arquivos_selecionados):
            nome_original = os.path.basename(caminho_arquivo)
            self.tabela_arquivos.setItem(i, 0, QTableWidgetItem(nome_original))
        n = len(self.arquivos_selecionados)
        self.files_count.setText(f"{n} arquivo(s) selecionado(s)" if n else "Nenhum arquivo selecionado")

    def update_all_previews(self):
        if not self.arquivos_selecionados: return
        for i in range(len(self.arquivos_selecionados)):
            novo_nome = self._generate_string_from_blocks(self.name_blocks, i)
            ext = os.path.splitext(self.arquivos_selecionados[i])[1]
            self.tabela_arquivos.setItem(i, 1, QTableWidgetItem(novo_nome + ext))
    
    def on_prefix_add(self):
        txt = self.prefix_input.text().strip()
        if txt and not any(item.text() == txt for item in (self.prefix_list.item(i) for i in range(self.prefix_list.count()))):
            b = BlockItem(txt, "prefix"); item = QListWidgetItem(txt); item.setData(Qt.UserRole, b); self.prefix_store.append(b); self.prefix_list.addItem(item); self.prefix_input.clear()
    
    def on_add_num_block(self):
        format_text = self.num_format.currentText(); label = f"[{format_text}]"
        existing_block = next((b for b in self.prefix_store if b.type_ == "num"), None)
        if existing_block: existing_block.config["format"] = format_text
        else: b = BlockItem("NUMÉRICA", "num", {"format": format_text}); self.prefix_store.append(b)
        self.refresh_all_views()
        
    def on_add_alpha_block(self):
        format_text = self.alpha_format.currentText()
        config = {"format": format_text, "start_index": self.alpha_letters.index(self.alpha_start.currentText()), "end_index": self.alpha_letters.index(self.alpha_end.currentText())}
        existing_block = next((b for b in self.prefix_store if b.type_ == "alpha"), None)
        if existing_block: existing_block.config.update(config)
        else: b = BlockItem("ALFABÉTICA", "alpha", config); self.prefix_store.append(b)
        self.refresh_all_views()
        
    def on_prefix_double(self, item):
        block_to_add = item.data(Qt.UserRole)
        final_block = block_to_add.clone() if block_to_add.type_ == 'prefix' else block_to_add
        self.name_blocks.append(final_block)
        self.refresh_assembly()
        
    def on_assembly_double_clicked(self, item):
        row = self.assembly.row(item)
        if row >= 0: del self.name_blocks[row]; self.refresh_assembly()

    def refresh_assembly(self):
        self.assembly.clear()
        for b in self.name_blocks:
            label = b.text if b.type_ == "prefix" else f"[{b.config.get('format', b.text)}]"
            item = QListWidgetItem(label); item.setData(Qt.UserRole, b); self.assembly.addItem(item)
        self.update_all_previews()

    def refresh_all_views(self):
        self.prefix_list.clear()
        for b in self.prefix_store:
            label = b.text if b.type_ == "prefix" else f"[{b.config.get('format', b.text)}]"
            item = QListWidgetItem(label); item.setData(Qt.UserRole, b); self.prefix_list.addItem(item)
        self.refresh_assembly()
        
    def on_rename_files(self):
        if not self.arquivos_selecionados:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo selecionado."); return
        if not any(b.type_ in ('num', 'alpha') for b in self.name_blocks):
            QMessageBox.warning(self, "Erro", "A montagem do nome deve conter ao menos um bloco de sequência!"); return

        renomeados = 0
        erros = []
        for i in range(len(self.arquivos_selecionados)):
            caminho_original = self.arquivos_selecionados[i]
            pasta = os.path.dirname(caminho_original)
            novo_nome_item = self.tabela_arquivos.item(i, 1)
            
            if not novo_nome_item or not novo_nome_item.text(): continue

            novo_nome = novo_nome_item.text()
            caminho_novo = os.path.join(pasta, novo_nome)

            try:
                if caminho_original != caminho_novo:
                    if os.path.exists(caminho_novo):
                        erros.append(f"{os.path.basename(caminho_original)} -> Erro: Arquivo '{novo_nome}' já existe.")
                        continue 
                    os.rename(caminho_original, caminho_novo)
                    renomeados += 1
            except Exception as e:
                erros.append(f"{os.path.basename(caminho_original)} -> {e}")

        msg_final = f"{renomeados} arquivos renomeados com sucesso."
        if erros:
            msg_final += f"\n\nFalha ao renomear {len(erros)} arquivos:\n" + "\n".join(erros)
        append_history(
            "Renomeador em Lote",
            "Renomeação",
            f"Arquivos selecionados: {len(self.arquivos_selecionados)} | Renomeados: {renomeados} | Erros: {len(erros)}"
        )
        QMessageBox.information(self, "Concluído", msg_final)
        
        self.arquivos_selecionados = []
        self.tabela_arquivos.setRowCount(0)
        self.files_count.setText("Nenhum arquivo selecionado")
        self.name_blocks = []
        self.prefix_store = []
        self.refresh_all_views()
    
    def _alpha_repr(self, b, index):
        fmt_len, start_idx, end_idx = len(b.config.get("format", "a")), b.config.get("start_index", 0), b.config.get("end_index", len(self.alpha_letters) - 1); base = (end_idx - start_idx) + 1
        if base <= 0: return ""
        if index == 0: return self.alpha_letters[start_idx] * fmt_len
        result, temp_index = "", index
        while temp_index > 0: temp_index -= 1; remainder = temp_index % base; result = self.alpha_letters[start_idx + remainder] + result; temp_index //= base
        return result.rjust(fmt_len, self.alpha_letters[start_idx])

    def _generate_string_from_blocks(self, blocks, index):
        final_str = ""
        for b in blocks:
            if b.type_ == "prefix": final_str += b.text
            elif b.type_ == "num": final_str += str(index).zfill(len(b.config.get("format","0")))
            elif b.type_ == "alpha": final_str += self._alpha_repr(b, index)
        return final_str