# main.py — Launcher / seletor de ferramentas
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QLabel, QSizePolicy,
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices

from theme import apply_theme
from paths import resource_path

GITHUB_URL = "https://github.com/caiovespasiano/StudioModderSuite"


def make_github_button(parent=None):
    """Botão-ícone que abre o repositório."""
    btn = QPushButton(parent)
    btn.setObjectName("IconButton")
    btn.setIcon(QIcon(resource_path("github_mark.svg")))
    btn.setIconSize(QSize(20, 20))
    btn.setFixedSize(36, 36)
    btn.setToolTip("Abrir repositório no GitHub")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
    return btn


class Launcher(QWidget):
    """Tela inicial: um bloco centralizado, com rodapé compacto."""

    CONTENT_WIDTH = 460

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Modder")
        self.setObjectName("AppRoot")
        self.setWindowIcon(QIcon(resource_path("meu_icone.ico")))

        self.janela_ferramentas = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        center = QVBoxLayout()
        center.setContentsMargins(32, 32, 32, 24)
        center.setSpacing(0)
        # O bloco fica centralizado nos dois eixos; a janela nasce do tamanho
        # do conteúdo, então não sobra vão morto embaixo do GitHub.
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        column = QWidget()
        column.setFixedWidth(self.CONTENT_WIDTH)
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedHeight(84)
        pixmap = QPixmap(resource_path("logo_dimitrius.png"))
        if pixmap.isNull():
            pixmap = QPixmap(resource_path("meu_icone.ico"))
        if not pixmap.isNull():
            # A arte encosta nas bordas do PNG: desenho menor que a área,
            # centralizada, para não parecer cortada.
            logo_label.setPixmap(
                pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        col.addWidget(logo_label)

        title = QLabel("Studio Modder")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        subtitle = QLabel("Selecione a suíte para começar")
        subtitle.setObjectName("LoginSub")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(subtitle)

        col.addSpacing(18)

        btn_ferramentas = QPushButton("Abrir Ferramentas de Arquivo")
        btn_ferramentas.setObjectName("PrimaryButton")
        btn_ferramentas.setMinimumHeight(46)
        btn_ferramentas.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ferramentas.clicked.connect(self.abrir_suite_ferramentas)
        col.addWidget(btn_ferramentas)

        btn_editor = QPushButton("Editor de Defs (.sii / .sui) — em breve")
        btn_editor.setMinimumHeight(46)
        btn_editor.setEnabled(False)
        col.addWidget(btn_editor)

        col.addSpacing(6)

        hint = QLabel("Copiador, renomeador e otimizadores DDS/TGA em um só lugar.")
        hint.setObjectName("Hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        col.addWidget(hint)

        col.addSpacing(14)

        # Rodapé: créditos à esquerda, ícone do GitHub à direita (linha única).
        footer = QHBoxLayout()
        footer.setSpacing(10)
        credits = QLabel("Studio Modder Suite v1.0")
        credits.setObjectName("Muted")
        credits.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        footer.addWidget(credits, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        footer.addWidget(make_github_button(self), 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        col.addLayout(footer)

        center.addWidget(column)
        root.addLayout(center)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()

    def abrir_suite_ferramentas(self):
        if not self.janela_ferramentas:
            try:
                from suite_ferramentas import JanelaPrincipal

                self.janela_ferramentas = JanelaPrincipal()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro Crítico",
                    "Não foi possível abrir a suíte de ferramentas.\n\n"
                    f"Detalhes: {e}",
                )
                return

        self.janela_ferramentas.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())