# theme.py — design system ERP Hub6 proposta-1 adaptado p/ Qt (light clean).
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

APP_QSS = """
QMainWindow { background: #f6f7f9; }
QWidget#AppRoot { background: #f6f7f9; }
QFrame#Sidebar { background: #ffffff; border: none; border-right: 1px solid #e8ebf0; }
QLabel#BrandTitle { font-size: 15px; font-weight: 800; color: #0f172a; }
QLabel#BrandSub { font-size: 10px; font-weight: 600; color: #94a3b8; }
QLabel#SectionTitle { font-size: 22px; font-weight: 800; color: #0f172a; }
QLabel#SectionSubtitle { font-size: 12px; color: #64748b; }
QLabel#Muted { color: #64748b; font-size: 12px; }
QFrame#HeaderBar { background: transparent; border: none; border-bottom: 1px solid #e8ebf0; }
QFrame#LoginCard { background: #ffffff; border: 1px solid #e8ebf0; border-radius: 20px; }
QLabel#LoginTitle { font-size: 20px; font-weight: 800; color: #0f172a; }
QLabel#LoginSub { font-size: 13px; color: #64748b; }
QPushButton#NavButton {
    text-align: left; border: 1px solid transparent; border-radius: 10px;
    padding: 10px 12px; color: #64748b; font-size: 13px; font-weight: 500;
    background: transparent;
}
QPushButton#NavButton:hover { background: #f1f5f9; color: #0f172a; }
QPushButton#NavButton:checked { background: #eef2ff; color: #4f46e5; font-weight: 600; }
QPushButton {
    border: 1px solid #e8ebf0; border-radius: 10px; background: #ffffff;
    color: #0f172a; padding: 7px 14px; font-size: 13px; font-weight: 600;
}
QPushButton:hover { background: #f8fafc; border-color: #d6dbe4; }
QPushButton:pressed { background: #eef2ff; }
QPushButton:disabled { color: #94a3b8; background: #f8fafc; border-color: #eef1f6; }
QPushButton#PrimaryButton { background: #111827; color: #ffffff; border: 1px solid #111827; }
QPushButton#PrimaryButton:hover { background: #1f2937; border-color: #1f2937; }
QPushButton#PrimaryButton:disabled { background: #e2e8f0; border-color: #e2e8f0; color: #94a3b8; }
QLineEdit, QComboBox {
    border: 1px solid #dfe3ea; border-radius: 10px; background: #ffffff;
    padding: 7px 10px; font-size: 13px; color: #0f172a;
    selection-background-color: #eef2ff;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #4f46e5; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView {
    background: #ffffff; border: 1px solid #e8ebf0;
    selection-background-color: #eef2ff; selection-color: #4f46e5;
}
QTableWidget {
    background: #ffffff; border: 1px solid #eef1f6; border-radius: 12px;
    gridline-color: #eef1f6; font-size: 13px; color: #0f172a;
}
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected { background: #eef2ff; color: #0f172a; }
QHeaderView::section {
    background: #ffffff; color: #94a3b8; border: none;
    border-bottom: 1px solid #e8ebf0; padding: 8px; font-size: 11px; font-weight: 600;
}
QCheckBox { font-size: 13px; color: #0f172a; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 5px; border: 1px solid #dfe3ea; background: #ffffff; }
QCheckBox::indicator:checked { background: #4f46e5; border: 1px solid #4f46e5; }
QListWidget { border: 1px solid #eef1f6; border-radius: 12px; background: #ffffff; font-size: 13px; }
QListWidget::item:selected { background: #eef2ff; color: #4f46e5; }
QTextEdit { border: 1px solid #e8ebf0; border-radius: 12px; background: #ffffff; padding: 8px; font-size: 13px; color: #0f172a; }
QDialog { background: #f6f7f9; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #dfe3ea; border-radius: 6px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; border: none; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #dfe3ea; border-radius: 6px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; background: none; border: none; }
"""


def apply_theme(app=None):
    app = app or QApplication.instance()
    if app is None:
        return
    if app.property("smsThemeApplied"):
        return
    app.setProperty("smsThemeApplied", True)
    base = QFont("Inter, Segoe UI", 10)
    base.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(base)
    app.setStyleSheet(APP_QSS)
