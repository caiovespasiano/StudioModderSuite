# suite_ferramentas.py
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QDialog, QVBoxLayout,
    QTextEdit, QHBoxLayout, QMessageBox, QStackedWidget, QLabel, QFrame,
    QButtonGroup,
)
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices
from PySide6.QtCore import Qt, QUrl, QSize

from theme import apply_theme

GITHUB_URL = "https://github.com/caiovespasiano/StudioModderSuite"


def make_github_button(parent=None):
    btn = QPushButton(parent)
    btn.setObjectName("IconButton")
    btn.setIcon(QIcon("github_mark.svg"))
    btn.setIconSize(QSize(22, 22))
    btn.setFixedSize(38, 38)
    btn.setToolTip("Abrir repositório no GitHub")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
    return btn

from aba_copiadora import AbaCopiadora
from aba_renomeador import AbaRenomeador
from aba_multi_copiador import AbaMultiCopiador
from aba_otimizador_dds import AbaOtimizadorDDS
from aba_otimizador_tga import AbaOtimizadorTGA
from app_state import get_history, clear_history

# Tokens ERP Hub6 proposta-1 (light clean) adaptados p/ QSS (ver theme.py).
SECTION_SUBTITLES = {
    "Copiador com Sequência": "Gere cópias em sequência a partir de um arquivo molde",
    "Renomeador em Lote": "Renomeie vários arquivos para um padrão limpo",
    "Copiador Múltiplo": "Copie um arquivo para várias pastas de uma vez",
    "Otimizador DDS": "Redimensione e converta texturas .dds via texconv",
    "Otimizador TGA": "Redimensione texturas .tga via Pillow",
}


def apply_theme(app=None):
    from theme import apply_theme as _apply

    _apply(app)


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        apply_theme(QApplication.instance())
        self.setWindowTitle("Studio Modder Suite v1.0")
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)

        self.setWindowIcon(QIcon("meu_icone.ico"))

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- Sidebar (232px, compacta) ----
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(232)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 12)
        side_layout.setSpacing(2)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo_label = QLabel()
        pix = QPixmap("logo_dimitrius.png")
        if pix.isNull():
            pix = QPixmap("meu_icone.ico")
        if not pix.isNull():
            logo_label.setPixmap(
                pix.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        logo_label.setFixedSize(32, 32)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(logo_label)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_title = QLabel("Studio Modder")
        brand_title.setObjectName("BrandTitle")
        brand_sub = QLabel("SUITE")
        brand_sub.setObjectName("BrandSub")
        brand_text.addWidget(brand_title)
        brand_text.addWidget(brand_sub)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)
        side_layout.addSpacing(14)

        self.tab_definitions = [
            ("Copiador com Sequência", AbaCopiadora),
            ("Renomeador em Lote", AbaRenomeador),
            ("Copiador Múltiplo", AbaMultiCopiador),
            ("Otimizador DDS", AbaOtimizadorDDS),
            ("Otimizador TGA", AbaOtimizadorTGA),
        ]
        self.loaded_tabs = [None] * len(self.tab_definitions)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        for i, (title, _factory) in enumerate(self.tab_definitions):
            btn = QPushButton(title)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, idx=i: self.set_current_index(idx))
            self.nav_group.addButton(btn, i)
            side_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        side_layout.addStretch()
        side_layout.addWidget(make_github_button(self), alignment=Qt.AlignmentFlag.AlignHCenter)

        root_layout.addWidget(sidebar)

        # ---- Área principal: header + conteúdo ----
        main_col = QWidget()
        main_col.setObjectName("AppRoot")
        main_layout = QVBoxLayout(main_col)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.section_title = QLabel(self.tab_definitions[0][0])
        self.section_title.setObjectName("SectionTitle")
        self.section_subtitle = QLabel(SECTION_SUBTITLES.get(self.tab_definitions[0][0], ""))
        self.section_subtitle.setObjectName("SectionSubtitle")
        title_col.addWidget(self.section_title)
        title_col.addWidget(self.section_subtitle)
        header_layout.addLayout(title_col)
        header_layout.addStretch()

        self.btn_history = QPushButton("Histórico")
        self.btn_history.clicked.connect(self.show_history_dialog)
        header_layout.addWidget(self.btn_history)

        main_layout.addWidget(header)

        self.stack = QStackedWidget()
        for _title, _factory in self.tab_definitions:
            self.stack.addWidget(QWidget())
        main_layout.addWidget(self.stack, 1)

        root_layout.addWidget(main_col, 1)

        # Compat: alguns testes antigos usam .tabs; mantém alias para o stack.
        self.tabs = self.stack

        self.nav_buttons[0].setChecked(True)
        self.set_current_index(0)

    def set_current_index(self, index):
        if index < 0 or index >= len(self.tab_definitions):
            return
        self.ensure_tab_loaded(index)
        self.stack.setCurrentIndex(index)
        title = self.tab_definitions[index][0]
        self.section_title.setText(title)
        self.section_subtitle.setText(SECTION_SUBTITLES.get(title, ""))
        if self.nav_buttons[index] is not None and not self.nav_buttons[index].isChecked():
            self.nav_buttons[index].setChecked(True)

    PRIMARY_KEYWORDS = ("OTIMIZAR", "GERAR", "RENOMEAR", "CALCULAR", "SALVAR", "COPIAR")

    def _tidy_tab(self, tab_widget):
        # Contém o espalhamento: ritmo vertical uniforme e 1 ação primária
        # por aba, sem reescrever a lógica de cada ferramenta.
        layout = tab_widget.layout()
        if layout is not None:
            try:
                layout.setContentsMargins(16, 16, 16, 16)
                layout.setSpacing(10)
            except Exception:
                pass
        try:
            for btn in tab_widget.findChildren(QPushButton):
                text = (btn.text() or "").upper()
                if any(k in text for k in self.PRIMARY_KEYWORDS):
                    if btn.objectName() != "NavButton":
                        btn.setObjectName("PrimaryButton")
                        btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    break
        except Exception:
            pass

    def ensure_tab_loaded(self, index):
        if index < 0 or index >= len(self.tab_definitions):
            return
        if self.loaded_tabs[index] is not None:
            return

        _title, factory = self.tab_definitions[index]
        tab_widget = factory()
        self._tidy_tab(tab_widget)
        self.loaded_tabs[index] = tab_widget
        old = self.stack.widget(index)
        self.stack.removeWidget(old)
        if old is not None:
            old.deleteLater()
        self.stack.insertWidget(index, tab_widget)
        self.stack.setCurrentIndex(index)

    def show_history_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Histórico de Operações")
        dialog.resize(760, 480)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
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
        btn_close.setObjectName("PrimaryButton")

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
