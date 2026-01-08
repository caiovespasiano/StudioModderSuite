# main.py (Este é o Launcher)
import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

# Importa a janela principal da nossa suíte de ferramentas
try:
    from suite_ferramentas import JanelaPrincipal as JanelaFerramentas
except ImportError:
    QMessageBox.critical(None, "Erro Crítico", "Não foi possível encontrar o arquivo 'suite_ferramentas.py'.\nVerifique se o arquivo está na mesma pasta.")
    sys.exit()

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
        self.resize(450, 250) # Voltando ao tamanho original
        
        # Usa a função resource_path para garantir que o ícone carregue no .exe
        self.setWindowIcon(QIcon(resource_path("meu_icone.ico")))

        self.janela_ferramentas = None
        self.janela_editor_sii = None

        layout = QVBoxLayout(self)
        layout.setSpacing(20) 
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch() 
        layout.addSpacing(20) 

        # IMAGEM
        try:
            # Usa resource_path aqui também
            pixmap = QPixmap(resource_path("logo_dimitrius.png"))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(logo_label)
        except Exception as e:
            print(f"Erro ao carregar a imagem: {e}")

        layout.addSpacing(20)

        # ####################################################
        # ##               TEXTO DO BOTÃO ATUALIZADO        ##
        # ####################################################
        btn_ferramentas_arquivo = QPushButton("Abrir Ferramentas de Arquivo\n(Funções Básicas)")
        btn_ferramentas_arquivo.setMinimumHeight(70)
        btn_ferramentas_arquivo.clicked.connect(self.abrir_suite_ferramentas)
        
        # Botão para o nosso próximo projeto!
        btn_editor_sii = QPushButton("Abrir Editor de Defs (.sii / .sui)\n(Em Desenvolvimento)")
        btn_editor_sii.setMinimumHeight(70)
        btn_editor_sii.setEnabled(False) 

        layout.addWidget(btn_ferramentas_arquivo)
        layout.addWidget(btn_editor_sii)
        layout.addStretch() 
        
        credits_label = QLabel("Desenvolvido por: Dimitrius Caio Vespasiano")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setStyleSheet("font-size: 9pt; color: #888888;") 
        layout.addWidget(credits_label)


    def abrir_suite_ferramentas(self):
        if not self.janela_ferramentas:
            self.janela_ferramentas = JanelaFerramentas()
        self.janela_ferramentas.show() 
        self.close() 


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show() 
    sys.exit(app.exec())