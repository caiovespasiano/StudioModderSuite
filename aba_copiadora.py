# aba_copiadora.py
import sys
import os
import re
import uuid
import string
import math
import html
import shutil
from copy import deepcopy
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QListWidget, QListWidgetItem, QFileDialog,
    QCheckBox, QComboBox, QTextEdit, QMessageBox, QDialog, QGridLayout,
    QAbstractItemView, QMenu, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextFormat, QTextCharFormat, QFont
from app_state import append_history

# ... (As classes BlockItem, BlockBuilderDialog, AssemblyList, HoverTextEdit não mudam) ...
class BlockItem:
    def __init__(self, text, type_="prefix", config=None): self.text = text; self.type_ = type_; self.config = deepcopy(config) if config else {}
    def clone(self): return BlockItem(self.text, self.type_, deepcopy(self.config))
class BlockBuilderDialog(QDialog):
    def __init__(self, parent, available_blocks):
        super().__init__(parent); self.setWindowTitle("Montar Sequência de Conteúdo Interno"); self.main_window_ref = parent; self.available_blocks = available_blocks; self.result_blocks = []; self.setup_ui()
    def update_preview(self):
        all_blocks = [self.assembled.item(i).data(Qt.UserRole) for i in range(self.assembled.count()) if self.assembled.item(i)]
        self.preview_edit.setText(self.main_window_ref._generate_string_from_blocks(all_blocks, 0))
    def setup_ui(self):
        self.setMinimumWidth(600); layout = QVBoxLayout(self); layout.addWidget(QLabel("Monte o conteúdo usando os blocos já definidos na janela principal."))
        main_h_layout = QHBoxLayout(); left_v_layout = QVBoxLayout(); left_v_layout.addWidget(QLabel("Blocos Disponíveis (duplo-clique):")); self.pref_list = QListWidget()
        for block in self.available_blocks:
            label = block.text if block.type_ == "prefix" else f"[{block.config.get('format', block.text)}]"
            item = QListWidgetItem(label); item.setData(Qt.UserRole, block); self.pref_list.addItem(item)
        self.pref_list.itemDoubleClicked.connect(self.on_block_double_clicked); left_v_layout.addWidget(self.pref_list); main_h_layout.addLayout(left_v_layout)
        right_v_layout = QVBoxLayout(); right_v_layout.addWidget(QLabel("Montagem (arraste para reordenar):")); self.assembled = QListWidget(); self.assembled.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove); self.assembled.model().rowsMoved.connect(self.update_preview); right_v_layout.addWidget(self.assembled); remove_btn = QPushButton("Remover Selecionado"); remove_btn.clicked.connect(self.remove_selected); right_v_layout.addWidget(remove_btn); main_h_layout.addLayout(right_v_layout); layout.addLayout(main_h_layout)
        preview_h = QHBoxLayout(); preview_h.addWidget(QLabel("Preview:")); self.preview_edit = QLineEdit(); self.preview_edit.setReadOnly(True); preview_h.addWidget(self.preview_edit); layout.addLayout(preview_h)
        bottom = QHBoxLayout(); bottom.addStretch(); ok = QPushButton("Concluir"); ok.setObjectName("PrimaryButton"); ok.clicked.connect(self.on_ok); cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject); bottom.addWidget(ok); bottom.addWidget(cancel); layout.addLayout(bottom)
    def on_block_double_clicked(self, item):
        block_ref = item.data(Qt.UserRole)
        new_item = QListWidgetItem(item.text()); new_item.setData(Qt.UserRole, block_ref); self.assembled.addItem(new_item); self.update_preview()
    def remove_selected(self): it = self.assembled.currentItem();_ = self.assembled.takeItem(self.assembled.row(it)) if it else None; self.update_preview()
    def on_ok(self): self.result_blocks = [self.assembled.item(i).data(Qt.UserRole) for i in range(self.assembled.count())]; self.accept()
    def get_result(self): return self.result_blocks
class AssemblyList(QListWidget):
    def __init__(self, parent_widget: 'AbaCopiadora' = None):
        super().__init__(parent_widget); self.parent_widget = parent_widget; self.setAcceptDrops(True); self.setDragEnabled(True); self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        if self.parent_widget: self.model().rowsMoved.connect(self.parent_widget.reorder_name_blocks_from_assembly)
    def dropEvent(self, e):
        if e.source() and e.source() != self and e.mimeData().hasText():
            e.setDropAction(Qt.CopyAction)
            if self.parent_widget: self.parent_widget.add_block_from_prefix_text(e.mimeData().text())
        else: super().dropEvent(e)
class HoverTextEdit(QTextEdit):
    def __init__(self, parent_window=None):
        super().__init__(parent_window); self.parent_window = parent_window; self.setMouseTracking(True)
    def mouseMoveEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        if self.parent_window and self.parent_window._is_cursor_on_cfg_span(cursor):
            self.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.IBeamCursor)
        super().mouseMoveEvent(event)
    def leaveEvent(self, event):
        self.viewport().setCursor(Qt.IBeamCursor); super().leaveEvent(event)

# -----------------------
# AbaCopiadora
# -----------------------
class AbaCopiadora(QWidget):
    CFG_RE = re.compile(r'id="cfg-([0-9a-fA-F\-]+)"')
    TEXT_EXTENSIONS = ['.txt', '.xml', '.ini', '.json', '.html', '.css', '.js', '.py', '.lua', '.sii', '.sui', '.siv', '.tobj', '.pim', '.pit', '.pis']

    def __init__(self):
        super().__init__(); self.alpha_letters = list(string.ascii_lowercase); self.selected_file = ""; self.selected_folder = ""; self.prefix_store = []; self.name_blocks = []; self.internal_configs = {}; self.setup_ui()
    
    STEP_TITLES = ["1 · Fonte", "2 · Nome", "3 · Revisar"]

    def setup_ui(self):
        from ui_helpers import step, field, hint, muted, separator

        self._wizard_step = 0
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

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
        main_layout.addLayout(stepper)

        self.step_stack = QStackedWidget()
        main_layout.addWidget(self.step_stack, 1)

        # ---------- PASSO 1: fonte ----------
        page1 = QWidget()
        p1_wrap = QHBoxLayout(page1)
        p1_wrap.setContentsMargins(0, 8, 0, 0)
        p1_wrap.addStretch()
        card1 = QFrame()
        card1.setObjectName("Panel")
        card1.setFixedWidth(620)
        l1 = QVBoxLayout(card1)
        l1.setContentsMargins(24, 24, 24, 24)
        l1.setSpacing(10)
        l1.addWidget(step("DE ONDE VÊM AS CÓPIAS"))
        l1.addWidget(field("Arquivo molde"))
        self.file_label = muted("Nenhum arquivo selecionado")
        l1.addWidget(self.file_label)
        self.file_btn = QPushButton("Selecionar arquivo base")
        self.file_btn.setMinimumHeight(40)
        self.file_btn.clicked.connect(self.on_select_file)
        l1.addWidget(self.file_btn)
        l1.addWidget(field("Pasta de exportação"))
        self.folder_label = muted("Nenhuma pasta selecionada")
        l1.addWidget(self.folder_label)
        self.folder_btn = QPushButton("Selecionar pasta de exportação")
        self.folder_btn.setMinimumHeight(40)
        self.folder_btn.clicked.connect(self.on_select_folder)
        l1.addWidget(self.folder_btn)
        qty_row = QHBoxLayout()
        qty_row.addWidget(field("Quantidade de arquivos"))
        qty_row.addStretch()
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setFixedWidth(120)
        qty_row.addWidget(self.qty_spin)
        l1.addLayout(qty_row)
        l1.addWidget(hint("O arquivo base conta como 1 — para gerar 35 arquivos novos, peça 36."))
        p1_wrap.addWidget(card1)
        p1_wrap.addStretch()
        self.step_stack.addWidget(page1)

        # ---------- PASSO 2: nome ----------
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
        self.alpha_add_btn = QPushButton("Adicionar")
        self.alpha_add_btn.setFixedWidth(140)
        self.alpha_add_btn.clicked.connect(self.on_add_alpha_block)
        seq_grid.addWidget(self.alpha_check, 1, 0)
        seq_grid.addLayout(alpha_range, 1, 1, 1, 2)
        seq_grid.addWidget(self.alpha_add_btn, 2, 2)
        seq_lay.addLayout(seq_grid)
        self.num_format.setEnabled(False); self.num_add_btn.setEnabled(False); self.alpha_start.setEnabled(False); self.alpha_end.setEnabled(False); self.alpha_format.setEnabled(False); self.alpha_add_btn.setEnabled(False); self.num_check.toggled.connect(lambda c: (self.num_format.setEnabled(c), self.num_add_btn.setEnabled(c))); self.alpha_check.toggled.connect(lambda c: (self.alpha_start.setEnabled(c), self.alpha_end.setEnabled(c), self.alpha_format.setEnabled(c), self.alpha_add_btn.setEnabled(c)))
        limit_row = QHBoxLayout()
        self.char_check = QCheckBox("Limitar caracteres em")
        self.char_spin = QSpinBox()
        self.char_spin.setRange(12, 255)
        self.char_spin.setFixedWidth(90)
        self.char_spin.setEnabled(False)
        limit_row.addWidget(self.char_check)
        limit_row.addWidget(self.char_spin)
        limit_row.addStretch()
        seq_lay.addLayout(limit_row)
        self.char_check.toggled.connect(self.char_spin.setEnabled); self.char_check.toggled.connect(self.update_preview); self.char_spin.valueChanged.connect(self.update_preview)
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
        self.prefix_list.setMinimumHeight(150)
        self.prefix_list.setDragEnabled(True)
        self.prefix_list.itemDoubleClicked.connect(self.on_prefix_double)
        self.prefix_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.prefix_list.customContextMenuRequested.connect(self.on_prefix_context)
        left_v.addWidget(self.prefix_list)
        lists_h.addLayout(left_v)
        right_v = QVBoxLayout()
        right_v.addWidget(field("Montagem do nome"))
        self.assembly = AssemblyList(self)
        self.assembly.setMinimumHeight(150)
        self.assembly.setContextMenuPolicy(Qt.CustomContextMenu)
        self.assembly.customContextMenuRequested.connect(self.on_assembly_context)
        self.assembly.itemDoubleClicked.connect(self.on_assembly_double_clicked)
        right_v.addWidget(self.assembly)
        lists_h.addLayout(right_v)
        lists_lay.addLayout(lists_h)
        lists_lay.addWidget(hint("Duplo-clique move entre as listas · arraste para reordenar · botão direito remove"))
        lists_lay.addWidget(field("Prévia do nome"))
        self.preview = QLineEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("PreviewReadout")
        lists_lay.addWidget(self.preview)
        l2.addWidget(lists_card, 1)
        self.step_stack.addWidget(page2)

        # ---------- PASSO 3: revisar e gerar ----------
        page3 = QWidget()
        l3 = QHBoxLayout(page3)
        l3.setContentsMargins(0, 8, 0, 0)
        l3.setSpacing(12)
        sum_card = QFrame()
        sum_card.setObjectName("Panel")
        sum_card.setFixedWidth(380)
        sum_lay = QVBoxLayout(sum_card)
        sum_lay.setContentsMargins(24, 24, 24, 24)
        sum_lay.setSpacing(10)
        sum_lay.addWidget(step("RESUMO"))
        sum_lay.addWidget(field("Arquivo base"))
        self.sum_file = muted("—")
        sum_lay.addWidget(self.sum_file)
        sum_lay.addWidget(field("Destino"))
        self.sum_folder = muted("—")
        sum_lay.addWidget(self.sum_folder)
        sum_lay.addWidget(field("Quantidade"))
        self.sum_qty = muted("—")
        sum_lay.addWidget(self.sum_qty)
        sum_lay.addWidget(field("Padrão do nome"))
        self.sum_pattern = QLineEdit()
        self.sum_pattern.setReadOnly(True)
        self.sum_pattern.setObjectName("PreviewReadout")
        sum_lay.addWidget(self.sum_pattern)
        sum_lay.addWidget(separator())
        self.generate_btn = QPushButton("Gerar arquivos")
        self.generate_btn.setObjectName("PrimaryButton")
        self.generate_btn.setMinimumHeight(46)
        self.generate_btn.clicked.connect(self.on_generate)
        sum_lay.addWidget(self.generate_btn)
        sum_lay.addStretch()
        l3.addWidget(sum_card)

        int_card = QFrame()
        int_card.setObjectName("Panel")
        int_lay = QVBoxLayout(int_card)
        int_lay.setContentsMargins(24, 24, 24, 24)
        int_lay.setSpacing(10)
        int_lay.addWidget(step("CONTEÚDO INTERNO (OPCIONAL)"))
        self.internal_check = QCheckBox("Sincronizar trechos do conteúdo com a sequência")
        self.internal_check.toggled.connect(self.on_toggle_internal)
        int_lay.addWidget(self.internal_check)
        int_lay.addWidget(hint("Selecione um trecho no texto, clique com o botão direito e monte a sequência para aquele ponto."))
        self.text_editor = HoverTextEdit(self)
        self.text_editor.setReadOnly(True)
        self.text_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_editor.customContextMenuRequested.connect(self.on_text_context)
        self.text_editor.setAcceptDrops(False)
        int_lay.addWidget(self.text_editor, 1)
        int_lay.addWidget(field("Sincronizações ativas (duplo-clique edita)"))
        self.internal_configs_list = QListWidget()
        self.internal_configs_list.setMaximumHeight(110)
        self.internal_configs_list.itemDoubleClicked.connect(self.on_internal_config_item_double_clicked)
        int_lay.addWidget(self.internal_configs_list)
        l3.addWidget(int_card, 1)
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
        main_layout.addLayout(footer)

        self.goto_step(0)

    def _on_next(self):
        self.goto_step(self._wizard_step + 1)

    def _on_back(self):
        self.goto_step(self._wizard_step - 1)

    def goto_step(self, index):
        index = max(0, min(2, index))
        if index == 2 and not self._review_ready():
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

    def _review_ready(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Falta o arquivo", "Volte ao passo 1 e selecione o arquivo base.")
            return False
        if not self.selected_folder:
            QMessageBox.warning(self, "Falta a pasta", "Volte ao passo 1 e selecione a pasta de exportação.")
            return False
        if not any(b.type_ in ('num', 'alpha') for b in self.name_blocks):
            QMessageBox.warning(self, "Falta a sequência", "Volte ao passo 2 e monte o nome com ao menos um bloco de sequência.")
            return False
        return True

    def _refresh_summary(self):
        from ui_helpers import elide_label
        self.update_preview()
        self.sum_file.setText(os.path.basename(self.selected_file) if self.selected_file else "—")
        self.sum_file.setToolTip(self.selected_file)
        elide_label(self.sum_folder, self.selected_folder, 320)
        self.sum_qty.setText(f"{self.qty_spin.value()} arquivo(s)")
        self.sum_pattern.setText(self.preview.text())

    def is_selected_file_text(self):
        if not self.selected_file: return False
        _, ext = os.path.splitext(self.selected_file)
        return ext.lower() in self.TEXT_EXTENSIONS
    
    def on_select_file(self, file=None):
        if not file: file, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo")
        if file: setattr(self, 'selected_file', file); self.file_label.setText(f"{os.path.basename(file)}"); self.file_label.setToolTip(file); self.load_selected_file() if self.internal_check.isChecked() else None; self.update_preview()

    def on_select_folder(self, folder=None):
        if not folder: folder = QFileDialog.getExistingDirectory(self, "Selecione pasta de exportação")
        if folder:
            from ui_helpers import elide_label
            setattr(self, 'selected_folder', folder); elide_label(self.folder_label, folder, 380)
    
    def on_prefix_add(self):
        txt = self.prefix_input.text().strip()
        if txt and not any(item.text() == txt for item in (self.prefix_list.item(i) for i in range(self.prefix_list.count()))):
            b = BlockItem(txt, "prefix"); item = QListWidgetItem(txt); item.setData(Qt.UserRole, b); self.prefix_store.append(b); self.prefix_list.addItem(item); self.prefix_input.clear()
    
    def on_prefix_double(self, item): self.add_block_from_prefix_text(item.text())
    
    def on_prefix_context(self, pos):
        item = self.prefix_list.itemAt(pos)
        if item and QMessageBox.question(self, "Remover", f"Remover '{item.text()}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            block = item.data(Qt.UserRole); self.prefix_store.remove(block); self.prefix_list.takeItem(self.prefix_list.row(item)); self.refresh_all_views()
    
    def on_add_num_block(self):
        format_text = self.num_format.currentText()
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
    
    def add_block_from_prefix_text(self, txt):
        block_to_add = next((item.data(Qt.UserRole) for i in range(self.prefix_list.count()) if (item := self.prefix_list.item(i)).text() == txt), None)
        if block_to_add:
            final_block = block_to_add.clone() if block_to_add.type_ == 'prefix' else block_to_add
            self.name_blocks.append(final_block); self.refresh_assembly()
    
    def refresh_assembly(self):
        self.assembly.clear()
        for b in self.name_blocks:
            label = b.text if b.type_ == "prefix" else f"[{b.config.get('format', b.text)}]"
            item = QListWidgetItem(label); item.setData(Qt.UserRole, b); self.assembly.addItem(item)
        self.update_preview()
        
    def refresh_all_views(self):
        self.prefix_list.clear()
        for b in self.prefix_store:
            label = b.text if b.type_ == "prefix" else f"[{b.config.get('format', b.text)}]"
            item = QListWidgetItem(label); item.setData(Qt.UserRole, b); self.prefix_list.addItem(item)
        self.refresh_assembly()
        # Atualiza a nova lista também
        self.refresh_internal_configs_list()

    def reorder_name_blocks_from_assembly(self, *args):
        self.name_blocks = [self.assembly.item(i).data(Qt.UserRole) for i in range(self.assembly.count())]
        self.update_preview()
    
    def on_assembly_context(self, pos):
        item = self.assembly.itemAt(pos);_ = (self.name_blocks.pop(self.assembly.row(item)), self.refresh_assembly()) if item and QMessageBox.question(self, "Remover", f"Remover '{item.text()}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes else None
    
    def on_assembly_double_clicked(self, item):
        row = self.assembly.row(item)
        if row >= 0: del self.name_blocks[row]; self.refresh_assembly()
    
    def update_preview(self):
        current_blocks = self._apply_char_limit(self.name_blocks, self.char_spin.value()) if self.char_check.isChecked() else self.name_blocks; preview_name = self._generate_string_from_blocks(current_blocks, 0); ext = os.path.splitext(self.selected_file)[1] if self.selected_file else ""; self.preview.setText(f"{preview_name}{ext}")
    
    def on_toggle_internal(self, checked):
        if checked:
            if not self.selected_file: QMessageBox.warning(self, "Erro", "Selecione um arquivo primeiro!"); self.internal_check.setChecked(False); return
            if not self.is_selected_file_text(): QMessageBox.warning(self, "Aviso", "A edição de conteúdo interno só é suportada para arquivos de texto (.txt, .xml, .sii, etc.).\n\nEste arquivo será apenas copiado."); self.internal_check.setChecked(False); return
            self.load_selected_file()
        else: 
            self.text_editor.clear(); self.internal_configs.clear()
            self.internal_configs_list.clear() # Limpa a nova lista
        self.text_editor.setReadOnly(not checked)
        
    def load_selected_file(self):
        if not self.selected_file or not os.path.exists(self.selected_file): return
        try:
            with open(self.selected_file, "r", encoding="utf-8") as f: txt = f.read()
            self.internal_configs.clear()
            self.internal_configs_list.clear() # Limpa a nova lista
            html_content = f"<pre style='font-family: Consolas, monospace; font-size: 9pt; margin: 0;'>{html.escape(txt)}</pre>"; self.text_editor.setHtml(html_content)
        except Exception: 
            self.internal_check.setChecked(False); self.internal_configs_list.clear()
            QMessageBox.warning(self, "Aviso", "Não foi possível ler o arquivo como texto. A edição de conteúdo interno foi desativada.")
    
    def on_text_context(self, pos):
        menu = QMenu(); cursor = self.text_editor.textCursor(); cfg_id = self._cursor_inside_cfg(self.text_editor.cursorForPosition(pos))
        if cursor.hasSelection() and not cfg_id: menu.addAction("Configurar blocos de sequência", lambda: self.configure_blocks_for_selection(cursor))
        if cfg_id: menu.addAction("Editar configuração existente", lambda: self.edit_existing_cfg(cfg_id))
        if cursor.hasSelection(): menu.addAction("Recortar", self.text_editor.cut)
        menu.addAction("Copiar", self.text_editor.copy); menu.addAction("Colar", self.text_editor.paste); menu.addSeparator(); menu.addAction("Cancelar", lambda: None); menu.exec(self.text_editor.viewport().mapToGlobal(pos))
    
    def configure_blocks_for_selection(self, cursor):
        original_text = cursor.selectedText()
        available_blocks = [b for b in self.prefix_store]
        dlg = BlockBuilderDialog(self, available_blocks)
        if dlg.exec():
            blocks = dlg.get_result()
            if blocks:
                cid = str(uuid.uuid4()); self.internal_configs[cid] = {"blocks": blocks, "original_text": original_text}
                preview_text = self._generate_string_from_blocks(blocks, 0)
                char_format = QTextCharFormat(); char_format.setProperty(QTextFormat.Property.UserProperty, f'id="cfg-{cid}"')
                char_format.setBackground(Qt.darkGray); char_format.setForeground(Qt.white)
                font = QFont("monospace"); font.setPointSize(9); char_format.setFont(font)
                cursor.beginEditBlock(); cursor.removeSelectedText(); cursor.insertText(preview_text, char_format); cursor.endEditBlock()
                self.refresh_internal_configs_list() # Atualiza a lista
    
    def _is_cursor_on_cfg_span(self, cursor):
        prop = cursor.charFormat().property(QTextFormat.Property.UserProperty)
        return bool(prop and 'id="cfg-' in prop)
    
    def _cursor_inside_cfg(self, cursor):
        prop = cursor.charFormat().property(QTextFormat.Property.UserProperty)
        if prop and 'id="cfg-' in prop:
            match = self.CFG_RE.search(prop)
            return match.group(1) if match else None
        return None
    
    def edit_existing_cfg(self, cfg_id):
        cfg = self.internal_configs.get(cfg_id)
        if not cfg: QMessageBox.warning(self, "Erro", "Configuração não encontrada."); return
        available_blocks = [b for b in self.prefix_store]
        dlg = BlockBuilderDialog(self, available_blocks)
        for b in cfg["blocks"]:
            label = b.text if b.type_ == "prefix" else f"[{b.config.get('format', b.text)}]"
            item = QListWidgetItem(label); item.setData(Qt.UserRole, b); dlg.assembled.addItem(item)
        dlg.update_preview()
        if dlg.exec(): 
            self.internal_configs[cfg_id]["blocks"] = dlg.get_result()
            self.refresh_all_views() # Atualiza tudo, incluindo a lista e o editor
            QMessageBox.information(self, "Editado", "Configuração atualizada.")

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
    
    def _apply_char_limit(self, blocks, limit):
        temp_blocks = [b.clone() if b.type_ == 'prefix' else b for b in blocks]
        high_idx = self.qty_spin.value() - 1; current_len = len(self._generate_string_from_blocks(temp_blocks, high_idx))
        while current_len > limit:
            longest_prefix = max([b for b in temp_blocks if b.type_ == "prefix" and b.text], key=lambda p: len(p.text), default=None)
            if longest_prefix: longest_prefix.text = longest_prefix.text[:-1]; current_len = len(self._generate_string_from_blocks(temp_blocks, high_idx))
            else: break
        return temp_blocks
    
    def on_generate(self):
        if not self.selected_file: QMessageBox.warning(self, "Erro", "Selecione um arquivo de base primeiro!"); return
        if not self.selected_folder or not self.name_blocks or not any(b.type_ in ('num', 'alpha') for b in self.name_blocks): QMessageBox.warning(self, "Erro", "Verifique se a pasta de destino, e pelo menos um bloco de sequência no nome, foram definidos."); return
        qty = self.qty_spin.value()
        all_seq = [{"loc": "nome do arquivo", "block": b} for b in self.name_blocks if b.type_ in ('num', 'alpha')]; [all_seq.extend([{"loc": f"configuração interna", "block": b} for b in d["blocks"] if b.type_ in ('num', 'alpha')]) for d in self.internal_configs.values()]
        for item in all_seq:
            loc, block = item["loc"], item["block"]
            capacity, fmt = 0, block.config.get("format", "N/A")
            if block.type_ == "num": capacity = math.pow(10, len(fmt))
            else: base = (block.config.get("end_index", 0) - block.config.get("start_index", 0)) + 1; capacity = math.pow(base, len(fmt))
            if qty > capacity: QMessageBox.critical(self, "Erro de Capacidade", f"A quantidade ({qty}) excede a capacidade da sequência ({int(capacity)}).\n\nLocal: {loc}\nFormato: '{fmt}'\n\nAumente o formato ou diminua a quantidade."); return
        generated, ext = 0, os.path.splitext(self.selected_file)[1]
        for i in range(qty):
            current_name_blocks = self._apply_char_limit(self.name_blocks, self.char_spin.value()) if self.char_check.isChecked() else self.name_blocks
            filename = self._generate_string_from_blocks(current_name_blocks, i); out_path = os.path.join(self.selected_folder, filename + ext)
            try:
                if self.internal_check.isChecked() and self.is_selected_file_text():
                    doc_clone = self.text_editor.document().clone()
                    cursor = QTextCursor(doc_clone)
                    while not cursor.isNull() and not cursor.atEnd():
                        prop = cursor.charFormat().property(QTextFormat.Property.UserProperty)
                        if prop and 'id="cfg-' in prop:
                            match = self.CFG_RE.search(prop)
                            if match and (cid := match.group(1)) in self.internal_configs:
                                blocks = self.internal_configs[cid]["blocks"]
                                replacement_text = self._generate_string_from_blocks(blocks, i)
                                cursor.beginEditBlock(); cursor.select(QTextCursor.SelectionType.WordUnderCursor); cursor.removeSelectedText(); cursor.insertText(replacement_text); cursor.endEditBlock()
                        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter)
                    content_to_write = doc_clone.toPlainText()
                    with open(out_path, "w", encoding="utf-8") as f: f.write(content_to_write)
                else:
                    if not os.path.abspath(self.selected_file) == os.path.abspath(out_path):
                        shutil.copy2(self.selected_file, out_path)
                generated += 1
            except Exception as ex: QMessageBox.warning(self, "Erro", f"Falha ao gravar {out_path}: {ex}"); break
        append_history(
            "Copiador com Sequência",
            "Geração de arquivos",
            f"Base: {os.path.basename(self.selected_file)} | Gerados: {generated}/{qty} | Interno ativo: {'sim' if self.internal_check.isChecked() else 'não'}"
        )
        QMessageBox.information(self, "Concluído", f"{generated} de {qty} arquivos gerados com sucesso.")

    # ####################################################
    # ##               NOVAS FUNÇÕES AQUI               ##
    # ####################################################
    
    def refresh_internal_configs_list(self):
        """Atualiza a lista visual de configurações internas."""
        self.internal_configs_list.clear()
        
        # O 'self.internal_configs' é nosso "banco de dados"
        for cid, config_data in self.internal_configs.items():
            # Gera o preview (ex: "st_00")
            preview_text = self._generate_string_from_blocks(config_data["blocks"], 0)
            
            # Pega o texto original (ex: "st_01")
            original_text = config_data.get('original_text', '')
            if len(original_text) > 15:
                original_text = original_text[:15] + "..."
            
            item_text = f"\"{preview_text}\" (Original: \"{original_text}\")"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, cid) # Armazena o ID
            self.internal_configs_list.addItem(item)

    def on_internal_config_item_double_clicked(self, item):
        """Chamado quando o usuário dá duplo-clique na nova lista."""
        cid = item.data(Qt.ItemDataRole.UserRole)
        if cid:
            self.edit_existing_cfg(cid) # Reutiliza a função que já temos!