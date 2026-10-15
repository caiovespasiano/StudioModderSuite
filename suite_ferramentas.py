# suite_ferramentas.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QPushButton, QDialog, QVBoxLayout, QTextEdit, QHBoxLayout, QMessageBox
from PySide6.QtGui import QIcon

from aba_copiadora import AbaCopiadora
from aba_renomeador import AbaRenomeador
from aba_multi_copiador import AbaMultiCopiador
from aba_otimizador_dds import AbaOtimizadorDDS
# NOVA IMPORTAÇÃO
from aba_otimizador_tga import AbaOtimizadorTGA
from app_state import get_history, clear_history

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Modder Suite v1.0")
        self.resize(1280, 800)
        
        self.setWindowIcon(QIcon("meu_icone.ico"))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_definitions = [
            ("Copiador com Sequência", AbaCopiadora),
            ("Renomeador em Lote", AbaRenomeador),
            ("Copiador Múltiplo", AbaMultiCopiador),
            ("Otimizador DDS", AbaOtimizadorDDS),
            ("Otimizador TGA", AbaOtimizadorTGA),
        ]
        self.loaded_tabs = [None] * len(self.tab_definitions)

        for title, _factory in self.tab_definitions:
            self.tabs.addTab(QWidget(), title)

        self.btn_history = QPushButton("Histórico")
        self.btn_history.clicked.connect(self.show_history_dialog)
        self.tabs.setCornerWidget(self.btn_history)

        self.tabs.currentChanged.connect(self.ensure_tab_loaded)
        self.ensure_tab_loaded(0)

    def ensure_tab_loaded(self, index):
        if index < 0 or index >= len(self.tab_definitions):
            return
        if self.loaded_tabs[index] is not None:
            return

        _title, factory = self.tab_definitions[index]
        tab_widget = factory()
        self.loaded_tabs[index] = tab_widget
        self.tabs.removeTab(index)
        self.tabs.insertTab(index, tab_widget, self.tab_definitions[index][0])
        self.tabs.setCurrentIndex(index)

    def show_history_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Histórico de Operações")
        dialog.resize(760, 480)

        layout = QVBoxLayout(dialog)
        text_area = QTextEdit()
        text_area.setReadOnly(True)

        history = get_history(limit=300)
        if history:
            lines = []
            for item in reversed(history):
                lines.append(f"[{item.get('timestamp', '-')}] {item.get('tool', '-')}: {item.get('action', '-')}")
                lines.append(f"  {item.get('details', '')}")
                lines.append("")
            text_area.setPlainText("\n".join(lines))
        else:
            text_area.setPlainText("Nenhuma operação registrada ainda.")

        layout.addWidget(text_area)

        actions = QHBoxLayout()
        actions.addStretch()

        btn_clear = QPushButton("Limpar Histórico")
        btn_close = QPushButton("Fechar")

        def on_clear():
            if QMessageBox.question(dialog, "Confirmar", "Deseja limpar todo o histórico?") == QMessageBox.StandardButton.Yes:
                clear_history()
                text_area.setPlainText("Nenhuma operação registrada ainda.")

        btn_clear.clicked.connect(on_clear)
        btn_close.clicked.connect(dialog.accept)

        actions.addWidget(btn_clear)
        actions.addWidget(btn_close)
        layout.addLayout(actions)

        dialog.exec()