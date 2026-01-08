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
    QAbstractItemView, QMenu, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QTextFormat, QTextCharFormat, QFont

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
        bottom = QHBoxLayout(); bottom.addStretch(); ok = QPushButton("Concluir"); ok.clicked.connect(self.on_ok); cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject); bottom.addWidget(ok); bottom.addWidget(cancel); layout.addLayout(bottom)
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
    
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12,12,12,12)
        main_layout.setSpacing(10)

        # --- COLUNA ESQUERDA (Configurações) ---
        coluna_esquerda = QVBoxLayout()
        coluna_esquerda.addWidget(QLabel("<b>1. Arquivos e Quantidade:</b>"))
        fh = QHBoxLayout(); self.file_label = QLabel("Arquivo de base: Nenhum selecionado"); self.file_btn = QPushButton("Selecionar Arquivo"); self.file_btn.clicked.connect(self.on_select_file); fh.addWidget(self.file_label); fh.addWidget(self.file_btn); fh.addStretch(); coluna_esquerda.addLayout(fh)
        fh2 = QHBoxLayout(); self.folder_label = QLabel("Pasta de exportação: Nenhuma selecionada"); self.folder_btn = QPushButton("Selecionar Pasta"); self.folder_btn.clicked.connect(self.on_select_folder); fh2.addWidget(self.folder_label); fh2.addWidget(self.folder_btn); fh2.addStretch(); coluna_esquerda.addLayout(fh2)
        qh = QHBoxLayout(); qh.addWidget(QLabel("Quantidade de arquivos a gerar:")); self.qty_spin = QSpinBox(); self.qty_spin.setRange(1,9999); qh.addWidget(self.qty_spin); qh.addStretch(); coluna_esquerda.addLayout(qh)
        separator1 = QFrame(); separator1.setFrameShape(QFrame.Shape.HLine); separator1.setFrameShadow(QFrame.Shadow.Sunken); coluna_esquerda.addWidget(separator1)
        coluna_esquerda.addWidget(QLabel("<b>2. Configuração do Nome:</b>"))
        num_h = QHBoxLayout(); self.num_check = QCheckBox("Numérica"); self.num_format = QComboBox(); self.num_format.addItems(["0","00","000"]); self.num_add_btn = QPushButton("Adicionar/Atualizar Bloco"); self.num_add_btn.clicked.connect(self.on_add_num_block); num_h.addWidget(self.num_check); num_h.addWidget(QLabel("Formato:")); num_h.addWidget(self.num_format); num_h.addWidget(self.num_add_btn); num_h.addStretch(); coluna_esquerda.addLayout(num_h)
        alpha_h = QHBoxLayout(); self.alpha_check = QCheckBox("Alfabética"); self.alpha_start = QComboBox(); self.alpha_start.addItems(self.alpha_letters); self.alpha_end = QComboBox(); self.alpha_end.addItems(self.alpha_letters); self.alpha_format = QComboBox(); self.alpha_format.addItems(["a","aa","aaa"]); self.alpha_add_btn = QPushButton("Adicionar/Atualzir Bloco"); self.alpha_add_btn.clicked.connect(self.on_add_alpha_block); alpha_h.addWidget(self.alpha_check); alpha_h.addWidget(QLabel("Primeira letra:")); alpha_h.addWidget(self.alpha_start); alpha_h.addWidget(QLabel("Última letra:")); alpha_h.addWidget(self.alpha_end); alpha_h.addWidget(QLabel("Formato:")); alpha_h.addWidget(self.alpha_format); alpha_h.addWidget(self.alpha_add_btn); alpha_h.addStretch(); coluna_esquerda.addLayout(alpha_h)
        self.num_format.setEnabled(False); self.num_add_btn.setEnabled(False); self.alpha_start.setEnabled(False); self.alpha_end.setEnabled(False); self.alpha_format.setEnabled(False); self.alpha_add_btn.setEnabled(False); self.num_check.toggled.connect(lambda c: (self.num_format.setEnabled(c), self.num_add_btn.setEnabled(c))); self.alpha_check.toggled.connect(lambda c: (self.alpha_start.setEnabled(c), self.alpha_end.setEnabled(c), self.alpha_format.setEnabled(c), self.alpha_add_btn.setEnabled(c)))
        limit_h = QHBoxLayout(); self.char_check = QCheckBox("Deseja limitar a quantidade de caracteres?"); self.char_spin = QSpinBox(); self.char_spin.setRange(12,255); self.char_spin.setEnabled(False); limit_h.addWidget(self.char_check); limit_h.addWidget(QLabel("Limite:")); limit_h.addWidget(self.char_spin); limit_h.addStretch(); coluna_esquerda.addLayout(limit_h)
        self.char_check.toggled.connect(self.char_spin.setEnabled); self.char_check.toggled.connect(self.update_preview); self.char_spin.valueChanged.connect(self.update_preview)
        ph = QHBoxLayout(); self.prefix_input = QLineEdit(); self.prefix_input.setPlaceholderText("Insira os prefixos de nomes"); self.prefix_add_btn = QPushButton("Adicionar"); self.prefix_add_btn.clicked.connect(self.on_prefix_add); ph.addWidget(self.prefix_input); ph.addWidget(self.prefix_add_btn); ph.addStretch(); coluna_esquerda.addLayout(ph)
        lists_h_layout = QHBoxLayout()
        left_list_v_layout = QVBoxLayout(); left_list_v_layout.addWidget(QLabel("<b>Blocos disponíveis (duplo-clique):</b>")); self.prefix_list = QListWidget(); self.prefix_list.setDragEnabled(True); self.prefix_list.itemDoubleClicked.connect(self.on_prefix_double); self.prefix_list.setContextMenuPolicy(Qt.CustomContextMenu); self.prefix_list.customContextMenuRequested.connect(self.on_prefix_context); left_list_v_layout.addWidget(self.prefix_list); lists_h_layout.addLayout(left_list_v_layout)
        right_list_v_layout = QVBoxLayout(); right_list_v_layout.addWidget(QLabel("<b>Montagem (duplo-clique para remover):</b>")); self.assembly = AssemblyList(self); self.assembly.setContextMenuPolicy(Qt.CustomContextMenu); self.assembly.customContextMenuRequested.connect(self.on_assembly_context); self.assembly.itemDoubleClicked.connect(self.on_assembly_double_clicked); right_list_v_layout.addWidget(self.assembly); lists_h_layout.addLayout(right_list_v_layout)
        coluna_esquerda.addLayout(lists_h_layout, 1)
        ph2 = QHBoxLayout(); ph2.addWidget(QLabel("Preview do Nome:")); self.preview = QLineEdit(); self.preview.setReadOnly(True); ph2.addWidget(self.preview); coluna_esquerda.addLayout(ph2)
        coluna_esquerda.addStretch()
        main_layout.addLayout(coluna_esquerda, 1)

        # --- COLUNA DIREITA (Editor de Texto) ---
        coluna_direita = QVBoxLayout()
        coluna_direita.addWidget(QLabel("<b>3. Conteúdo Interno (Opcional):</b>"))
        self.internal_check = QCheckBox("Ativar configuração de conteúdo de texto interno"); self.internal_check.toggled.connect(self.on_toggle_internal); coluna_direita.addWidget(self.internal_check)
        self.text_editor = HoverTextEdit(self); self.text_editor.setReadOnly(True); self.text_editor.setContextMenuPolicy(Qt.CustomContextMenu); self.text_editor.customContextMenuRequested.connect(self.on_text_context)
        self.text_editor.setAcceptDrops(False)
        coluna_direita.addWidget(self.text_editor, 1) # '1' faz o editor expandir

        # ####################################################
        # ##                 NOVA LISTA AQUI                ##
        # ####################################################
        coluna_direita.addWidget(QLabel("<b>Configurações Internas Ativas (Duplo-clique para editar):</b>"))
        self.internal_configs_list = QListWidget()
        self.internal_configs_list.setMaximumHeight(100) # Altura máxima de 100px
        self.internal_configs_list.itemDoubleClicked.connect(self.on_internal_config_item_double_clicked)
        coluna_direita.addWidget(self.internal_configs_list)
        
        separator_final = QFrame(); separator_final.setFrameShape(QFrame.Shape.HLine); separator_final.setFrameShadow(QFrame.Shadow.Sunken); coluna_direita.addWidget(separator_final)
        gh = QHBoxLayout(); gh.addStretch(); self.generate_btn = QPushButton("Gerar Arquivos"); self.generate_btn.clicked.connect(self.on_generate); gh.addWidget(self.generate_btn); coluna_direita.addLayout(gh)
        main_layout.addLayout(coluna_direita, 1)

    def is_selected_file_text(self):
        if not self.selected_file: return False
        _, ext = os.path.splitext(self.selected_file)
        return ext.lower() in self.TEXT_EXTENSIONS
    
    def on_select_file(self, file=None):
        if not file: file, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo")
        if file: setattr(self, 'selected_file', file); self.file_label.setText(f"Arquivo de base: {os.path.basename(file)}"); self.load_selected_file() if self.internal_check.isChecked() else None; self.update_preview()
    
    def on_select_folder(self, folder=None):
        if not folder: folder = QFileDialog.getExistingDirectory(self, "Selecione pasta de exportação")
        if folder: setattr(self, 'selected_folder', folder); self.folder_label.setText(f"Pasta de exportação: {folder}")
    
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