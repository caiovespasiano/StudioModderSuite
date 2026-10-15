# theme.py — dark graphite denso (conforto visual), tokens calm/neutral.
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

# Ordem de preferência. "Inter" só é usada se realmente estiver instalada;
# caso contrário cai na primeira fonte de sistema que existir (nunca em fallback
# silencioso, que é o que causava larguras e alturas imprevisíveis).
FONT_PREFERENCE = ["Inter", "Segoe UI Variable Text", "Segoe UI", "Tahoma", "Arial"]


def resolve_ui_font():
    """Devolve a primeira família de FONT_PREFERENCE instalada no sistema."""
    _ = QApplication.instance()  # garante que o QGuiApplication já existe
    families = set(QFontDatabase.families())
    for name in FONT_PREFERENCE:
        if name in families:
            return name
    return QFontDatabase().systemFont(QFontDatabase.SystemFont.GeneralFont).family()

APP_QSS = """
QMainWindow { background: #141414; }
QWidget#AppRoot { background: #141414; }
QFrame#Sidebar { background: #1a1a1a; border: none; border-right: 1px solid #262626; }
QLabel#BrandTitle { font-size: 14px; font-weight: 700; color: #e9e9e9; }
QLabel#BrandSub { font-size: 10px; font-weight: 600; color: #8f8f8f; }
QLabel#SectionTitle { font-size: 20px; font-weight: 700; color: #e9e9e9; }
QLabel#SectionSubtitle { font-size: 12px; color: #9a9a9a; }
QLabel#Muted { color: #8f8f8f; font-size: 12px; }
QLabel#Link { color: #a5b4fc; font-size: 12px; }
QLabel { color: #d6d6d6; }
QLabel#StepTitle { font-size: 11px; font-weight: 700; color: #8f8f8f; }
QLabel#FieldLabel { font-size: 11px; font-weight: 600; color: #7e7e7e; }
QLabel#FieldValue { font-size: 13px; color: #d6d6d6; }
QLabel#Hint { font-size: 11px; color: #7e7e7e; }
QLineEdit#PreviewReadout { font-size: 14px; font-weight: 600; background: #202020; padding: 9px 10px; }
QFrame#Panel { background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 12px; }
QFrame#Separator { border: none; border-top: 1px solid #2a2a2a; }
QPushButton#StepButton { background: transparent; border: 1px solid #2a2a2a; border-radius: 8px; padding: 7px 10px; color: #8f8f8f; font-size: 12px; font-weight: 600; }
QPushButton#StepButton:checked { background: rgba(99,102,241,0.16); color: #a5b4fc; border-color: #6366f1; }
QPushButton#StepButton:hover:!checked { background: #262626; color: #e9e9e9; }
QProgressBar { border: 1px solid #2a2a2a; border-radius: 6px; background: #202020; height: 8px; text-align: center; }
QProgressBar::chunk { background: #6366f1; border-radius: 6px; }
QLabel { color: #d6d6d6; }
QFrame#HeaderBar { background: transparent; border: none; border-bottom: 1px solid #262626; }
QFrame#LoginCard { background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 16px; }
QLabel#LoginTitle { font-size: 20px; font-weight: 700; color: #e9e9e9; }
QLabel#LoginSub { font-size: 13px; color: #9a9a9a; }
QPushButton#NavButton {
    text-align: left; border: 1px solid transparent; border-radius: 8px;
    padding: 9px 12px; color: #9a9a9a; font-size: 13px; font-weight: 500;
    background: transparent; min-width: 0;
}
QPushButton#NavButton:hover { background: #262626; color: #e9e9e9; }
QPushButton#NavButton:checked { background: rgba(99,102,241,0.16); color: #a5b4fc; font-weight: 600; }
QPushButton {
    border: 1px solid #333333; border-radius: 8px; background: #262626;
    color: #e9e9e9; padding: 6px 12px; font-size: 13px; font-weight: 500;
}
QPushButton:hover { background: #2e2e2e; border-color: #3d3d3d; }
QPushButton:pressed { background: #333333; }
QPushButton:disabled { color: #6b6b6b; background: #202020; border-color: #2a2a2a; }
QPushButton#IconButton { background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 4px; }
QPushButton#IconButton:hover { background: #262626; border-color: #333333; }
QPushButton#StepButton { background: transparent; border: 1px solid #2a2a2a; border-radius: 8px; padding: 8px 18px; color: #8f8f8f; font-size: 12px; font-weight: 600; }
QPushButton#StepButton:hover { background: #262626; color: #e9e9e9; }
QPushButton#StepButton:checked { background: rgba(99,102,241,0.16); color: #a5b4fc; border-color: #6366f1; }
QPushButton#PrimaryButton { background: #6366f1; color: #ffffff; border: 1px solid #6366f1; font-weight: 600; }
QPushButton#PrimaryButton:hover { background: #818cf8; border-color: #818cf8; }
QPushButton#PrimaryButton:disabled { background: #2e2e2e; border-color: #2e2e2e; color: #6b6b6b; }
QLineEdit, QComboBox, QSpinBox {
    border: 1px solid #333333; border-radius: 8px; background: #262626;
    padding: 6px 9px; font-size: 13px; color: #e9e9e9;
    selection-background-color: rgba(99,102,241,0.4);
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #6366f1; }
QLineEdit:read-only { background: #202020; color: #b5b5b5; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #262626; border: 1px solid #333333; color: #e9e9e9;
    selection-background-color: rgba(99,102,241,0.35); selection-color: #ffffff;
}
QTableWidget {
    background: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 10px;
    gridline-color: #2a2a2a; font-size: 13px; color: #e9e9e9;
    alternate-background-color: #202020;
}
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected { background: rgba(99,102,241,0.28); color: #ffffff; }
QHeaderView { height: 34px; }
QHeaderView::section {
    background: #1e1e1e; color: #8f8f8f; border: none;
    border-bottom: 1px solid #2a2a2a; padding: 7px 10px; font-size: 11px; font-weight: 600;
}
QTableCornerButton::section { background: #1e1e1e; border: none; }
QCheckBox { font-size: 13px; color: #d6d6d6; spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #4a4a4a; background: #262626; }
QCheckBox::indicator:checked { background: #6366f1; border: 1px solid #6366f1; }
QListWidget { border: 1px solid #2a2a2a; border-radius: 10px; background: #1e1e1e; font-size: 13px; color: #d6d6d6; }
QListWidget::item { padding: 4px; }
QListWidget::item:selected { background: rgba(99,102,241,0.28); color: #ffffff; }
QListWidget::item:hover { background: #262626; }
QTextEdit { border: 1px solid #2a2a2a; border-radius: 10px; background: #1e1e1e; padding: 8px; font-size: 13px; color: #e9e9e9; }
QDialog { background: #141414; }
QMessageBox QLabel { color: #e9e9e9; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #333333; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #3d3d3d; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; border: none; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #333333; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #3d3d3d; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; background: none; border: none; }
QToolTip { background: #262626; color: #e9e9e9; border: 1px solid #333333; padding: 4px 6px; }
"""


def apply_theme(app=None):
    app = app or QApplication.instance()
    if app is None:
        return
    app.setProperty("smsThemeApplied", True)
    family = resolve_ui_font()
    base = QFont(family, 10)
    base.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(base)
    app.setStyleSheet(APP_QSS)
