# main.py (Este é o Launcher)
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from theme import apply_theme

# ####################################################
# ##       FUNÇÃO CRÍTICA PARA A COMPILAÇÃO (.EXE)  ##
# ####################################################
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funcionando em dev e no PyInstaller """
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver "congelado", pega o caminho do script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Modder - Seletor de Ferramentas")
        self.resize(520, 620)
        self.setObjectName("AppRoot")

        # Usa a função resource_path para garantir que o ícone carregue no .exe
        self.setWindowIcon(QIcon(resource_path("meu_icone.ico")))

        self.janela_ferramentas = None
        self.janela_editor_sii = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(72, 48, 72, 32)
        outer.setSpacing(10)

        # A janela É a superfície — sem card interno redundante.
        # Logo com respiro: a arte encosta nas bordas do PNG, então o
        # pixmap é menor que o label para não parecer cortada.
        try:
            pixmap = QPixmap(resource_path("github_mark.svg"))
            if pixmap.isNull():
                pixmap = QPixmap(resource_path("meu_icone.ico"))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setFixedSize(88, 88)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                outer.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        except Exception as e:
            print(f"Erro ao carregar a imagem: {e}")

        title = QLabel("Studio Modder")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        subtitle = QLabel("Selecione a suíte para começar")
        subtitle.setObjectName("LoginSub")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(subtitle)

        outer.addSpacing(14)

        btn_ferramentas_arquivo = QPushButton("Abrir Ferramentas de Arquivo")
        btn_ferramentas_arquivo.setObjectName("PrimaryButton")
        btn_ferramentas_arquivo.setMinimumHeight(48)
        btn_ferramentas_arquivo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ferramentas_arquivo.clicked.connect(self.abrir_suite_ferramentas)

        # Botão para o nosso próximo projeto!
        btn_editor_sii = QPushButton("Editor de Defs (.sii / .sui) — em breve")
        btn_editor_sii.setMinimumHeight(48)
        btn_editor_sii.setEnabled(False)

        outer.addWidget(btn_ferramentas_arquivo)
        outer.addWidget(btn_editor_sii)

        hint = QLabel("Copiador, renomeador e otimizadores DDS/TGA em um só lugar.")
        hint.setObjectName("Muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        outer.addWidget(hint)

        outer.addStretch()

        credits_label = QLabel('<a href="https://github.com/caiovespasiano/StudioModderSuite" style="color:#a5b4fc;">github.com/caiovespasiano/StudioModderSuite</a>')
        credits_label.setObjectName("Link")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setOpenExternalLinks(True)
        outer.addWidget(credits_label)


    def abrir_suite_ferramentas(self):
        if not self.janela_ferramentas:
            try:
                from suite_ferramentas import JanelaPrincipal as JanelaFerramentas
                self.janela_ferramentas = JanelaFerramentas()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro Crítico",
                    "Não foi possível abrir a suíte de ferramentas.\n\n"
                    f"Detalhes: {e}"
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