# aba_renomeador.py
import sys
import os
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QCheckBox, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QGridLayout, QStackedWidget, QSizePolicy
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

    STEP_TITLES = ["1 · Arquivos", "2 · Padrão", "3 · Revisar"]

    def setup_ui(self):
        from ui_helpers import step, field, hint, muted, separator

        self._wizard_step = 0
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(12)

        stepper = QHBoxLayout()
        stepper.setSpacing(8)
        self.step_buttons = []
        for i, title in enumerate(self.STEP_TITLES):
            b = QPushButton(title)
            b.setObjectName("StepButton")
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, idx=i: self.goto_step(idx))
            stepper.addWidget(b)
            self.step_buttons.append(b)
        stepper.addStretch()
        layout_principal.addLayout(stepper)

        self.step_stack = QStackedWidget()
        layout_principal.addWidget(self.step_stack, 1)

        # ---------- PASSO 1: arquivos ----------
        page1 = QFrame()
        page1.setObjectName("Panel")
        page1.setMaximumWidth(1080)
        page1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        l1 = QVBoxLayout(page1)
        l1.setContentsMargins(24, 24, 24, 24)
        l1.setSpacing(10)
        l1.addWidget(step("ARQUIVOS A RENOMEAR"))
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        self.files_count = muted("Nenhum arquivo selecionado")
        self.files_count.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(self.files_count)
        top_row.addStretch()
        btn_selecionar = QPushButton("Selecionar arquivos")
        btn_selecionar.setMinimumHeight(38)
        btn_selecionar.setMinimumWidth(170)
        btn_selecionar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_selecionar.clicked.connect(self.on_select_files)
        top_row.addWidget(btn_selecionar)
        l1.addLayout(top_row)
        self.tabela_arquivos = QTableWidget()
        self.tabela_arquivos.setColumnCount(2)
        self.tabela_arquivos.setHorizontalHeaderLabels(["Nome Original", "Novo Nome (Preview)"])
        self.tabela_arquivos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_arquivos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_arquivos.setShowGrid(False)
        self.tabela_arquivos.verticalHeader().setVisible(False)
        self.tabela_arquivos.verticalHeader().setDefaultSectionSize(32)
        for col in range(2):
            item = self.tabela_arquivos.horizontalHeaderItem(col)
            if item is not None:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        l1.addWidget(self.tabela_arquivos, 1)
        l1.addWidget(hint("A prévia atualiza sozinha a cada bloco adicionado."))
        self.step_stack.addWidget(page1)

        # ---------- PASSO 2: padrão ----------
        page2 = QWidget()
        l2 = QVBoxLayout(page2)
        l2.setContentsMargins(0, 8, 0, 0)
        l2.setSpacing(10)
        seq_card = QFrame()
        seq_card.setObjectName("Panel")
        seq_lay = QVBoxLayout(seq_card)
        seq_lay.setContentsMargins(24, 20, 24, 20)
        seq_lay.setSpacing(10)
        seq_lay.addWidget(step("SEQUÊNCIAS"))
        seq_grid = QGridLayout()
        seq_grid.setContentsMargins(0, 0, 0, 0)
        seq_grid.setHorizontalSpacing(12)
        seq_grid.setVerticalSpacing(10)
        seq_grid.setColumnStretch(0, 1)
        self.num_check = QCheckBox("Sequência numérica")
        self.num_format = QComboBox()
        self.num_format.addItems(["0", "00", "000"])
        self.num_format.setFixedWidth(120)
        self.num_add_btn = QPushButton("Adicionar")
        self.num_add_btn.setFixedWidth(140)
        self.num_add_btn.clicked.connect(self.on_add_num_block)
        seq_grid.addWidget(self.num_check, 0, 0)
        seq_grid.addWidget(self.num_format, 0, 1)
        seq_grid.addWidget(self.num_add_btn, 0, 2)
        self.alpha_check = QCheckBox("Sequência alfabética")
        alpha_range = QHBoxLayout()
        alpha_range.setSpacing(8)
        self.alpha_start = QComboBox()
        self.alpha_start.addItems(self.alpha_letters)
        self.alpha_start.setFixedWidth(70)
        self.alpha_end = QComboBox()
        self.alpha_end.addItems(self.alpha_letters)
        self.alpha_end.setFixedWidth(70)
        self.alpha_format = QComboBox()
        self.alpha_format.addItems(["a", "aa", "aaa"])
        self.alpha_format.setFixedWidth(90)
        alpha_range.addWidget(QLabel("de"))
        alpha_range.addWidget(self.alpha_start)
        alpha_range.addWidget(QLabel("até"))
        alpha_range.addWidget(self.alpha_end)
        alpha_range.addWidget(QLabel("formato"))
        alpha_range.addWidget(self.alpha_format)
        alpha_range.addStretch()
        alpha_range_widget = QWidget()
        alpha_range_widget.setLayout(alpha_range)
        self.alpha_add_btn = QPushButton("Adicionar")
        self.alpha_add_btn.setFixedWidth(140)
        self.alpha_add_btn.clicked.connect(self.on_add_alpha_block)
        seq_grid.addWidget(self.alpha_check, 1, 0)
        seq_grid.addWidget(alpha_range_widget, 1, 1)
        seq_grid.addWidget(self.alpha_add_btn, 1, 2)
        seq_lay.addLayout(seq_grid)
        self.num_format.setEnabled(False); self.num_add_btn.setEnabled(False); self.alpha_start.setEnabled(False); self.alpha_end.setEnabled(False); self.alpha_format.setEnabled(False); self.alpha_add_btn.setEnabled(False)
        self.num_check.toggled.connect(lambda c: (self.num_format.setEnabled(c), self.num_add_btn.setEnabled(c)))
        self.alpha_check.toggled.connect(lambda c: (self.alpha_start.setEnabled(c), self.alpha_end.setEnabled(c), self.alpha_format.setEnabled(c), self.alpha_add_btn.setEnabled(c)))
        prefix_row = QHBoxLayout()
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Prefixo ex.: skin_")
        self.prefix_input.returnPressed.connect(self.on_prefix_add)
        self.prefix_add_btn = QPushButton("Adicionar prefixo")
        self.prefix_add_btn.setFixedWidth(160)
        self.prefix_add_btn.clicked.connect(self.on_prefix_add)
        prefix_row.addWidget(self.prefix_input, 1)
        prefix_row.addWidget(self.prefix_add_btn)
        seq_lay.addLayout(prefix_row)
        l2.addWidget(seq_card)

        lists_card = QFrame()
        lists_card.setObjectName("Panel")
        lists_lay = QVBoxLayout(lists_card)
        lists_lay.setContentsMargins(24, 20, 24, 20)
        lists_lay.setSpacing(10)
        lists_h = QHBoxLayout()
        lists_h.setSpacing(12)
        left_v = QVBoxLayout()
        left_v.addWidget(field("Blocos disponíveis"))
        self.prefix_list = QListWidget()
        self.prefix_list.setMinimumHeight(140)
        self.prefix_list.itemDoubleClicked.connect(self.on_prefix_double)
        left_v.addWidget(self.prefix_list)
        lists_h.addLayout(left_v)
        right_v = QVBoxLayout()
        right_v.addWidget(field("Montagem do nome"))
        self.assembly = QListWidget()
        self.assembly.setMinimumHeight(140)
        self.assembly.itemDoubleClicked.connect(self.on_assembly_double_clicked)
        right_v.addWidget(self.assembly)
        lists_h.addLayout(right_v)
        lists_lay.addLayout(lists_h)
        lists_lay.addWidget(hint("Duplo-clique move entre as listas."))
        l2.addWidget(lists_card, 1)
        self.step_stack.addWidget(page2)

        # ---------- PASSO 3: revisar ----------
        page3 = QWidget()
        p3_wrap = QHBoxLayout(page3)
        p3_wrap.setContentsMargins(0, 8, 0, 0)
        p3_wrap.addStretch()
        sum_card = QFrame()
        sum_card.setObjectName("Panel")
        sum_card.setFixedWidth(620)
        sum_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)
        sum_lay = QVBoxLayout(sum_card)
        sum_lay.setContentsMargins(24, 24, 24, 24)
        sum_lay.setSpacing(10)
        sum_lay.addWidget(step("RESUMO"))
        sum_lay.addWidget(field("Arquivos"))
        self.sum_files = muted("—")
        sum_lay.addWidget(self.sum_files)
        sum_lay.addWidget(field("Padrão do nome"))
        self.sum_pattern = QLineEdit()
        self.sum_pattern.setReadOnly(True)
        self.sum_pattern.setObjectName("PreviewReadout")
        sum_lay.addWidget(self.sum_pattern)
        sum_lay.addWidget(field("Exemplo (primeiro arquivo)"))
        self.sum_example = muted("—")
        sum_lay.addWidget(self.sum_example)
        sum_lay.addWidget(hint("Arquivos que já existirem com o nome novo serão pulados e listados no final."))
        sum_lay.addWidget(separator())
        self.btn_rename = QPushButton("Renomear arquivos")
        self.btn_rename.setObjectName("PrimaryButton")
        self.btn_rename.setMinimumHeight(46)
        self.btn_rename.clicked.connect(self.on_rename_files)
        sum_lay.addWidget(self.btn_rename)
        p3_wrap.addWidget(sum_card)
        p3_wrap.addStretch()
        self.step_stack.addWidget(page3)

        # ---------- rodapé ----------
        footer = QHBoxLayout()
        self.btn_back = QPushButton("Voltar")
        self.btn_back.setFixedWidth(140)
        self.btn_back.clicked.connect(self._on_back)
        footer.addWidget(self.btn_back)
        footer.addStretch()
        self.btn_next = QPushButton("Continuar")
        self.btn_next.setObjectName("PrimaryButton")
        self.btn_next.setFixedWidth(200)
        self.btn_next.setMinimumHeight(40)
        self.btn_next.clicked.connect(self._on_next)
        footer.addWidget(self.btn_next)
        layout_principal.addLayout(footer)

        self.goto_step(0)

    def _on_next(self):
        self.goto_step(self._wizard_step + 1)

    def _on_back(self):
        self.goto_step(self._wizard_step - 1)

    def goto_step(self, index):
        index = max(0, min(2, index))
        if index >= 1 and not self.arquivos_selecionados:
            QMessageBox.warning(self, "Sem arquivos", "Volte ao passo 1 e selecione os arquivos.")
            return False
        if index == 2 and not any(b.type_ in ('num', 'alpha') for b in self.name_blocks):
            QMessageBox.warning(self, "Sem sequência", "Volte ao passo 2 e monte o nome com ao menos um bloco de sequência.")
            return False
        self._wizard_step = index
        self.step_stack.setCurrentIndex(index)
        for i, b in enumerate(self.step_buttons):
            b.setChecked(i == index)
        self.btn_back.setVisible(index > 0)
        self.btn_next.setVisible(index < 2)
        if index == 2:
            self._refresh_summary()
        return True

    def _refresh_summary(self):
        n = len(self.arquivos_selecionados)
        self.sum_files.setText(f"{n} arquivo(s) selecionado(s)")
        pattern = self._generate_string_from_blocks(self.name_blocks, 0)
        ext = os.path.splitext(self.arquivos_selecionados[0])[1] if self.arquivos_selecionados else ""
        self.sum_pattern.setText(f"{pattern}{ext}")
        first = os.path.basename(self.arquivos_selecionados[0]) if self.arquivos_selecionados else "—"
        self.sum_example.setText(f"{first}  ->  {pattern}{ext}")

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
        self.goto_step(0)
    
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