# suite_ferramentas.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QIcon

from aba_copiadora import AbaCopiadora
from aba_renomeador import AbaRenomeador
from aba_multi_copiador import AbaMultiCopiador
from aba_otimizador_dds import AbaOtimizadorDDS
# NOVA IMPORTAÇÃO
from aba_otimizador_tga import AbaOtimizadorTGA

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Modder Suite v1.0")
        self.resize(1280, 800)
        
        self.setWindowIcon(QIcon("meu_icone.ico"))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_copiadora = AbaCopiadora()
        self.tab_renomeador = AbaRenomeador()
        self.tab_multi_copiador = AbaMultiCopiador()
        self.tab_otimizador = AbaOtimizadorDDS()
        # NOVA INSTÂNCIA
        self.tab_otimizador_tga = AbaOtimizadorTGA()
        
        self.tabs.addTab(self.tab_copiadora, "Copiador com Sequência")
        self.tabs.addTab(self.tab_renomeador, "Renomeador em Lote")
        self.tabs.addTab(self.tab_multi_copiador, "Copiador Múltiplo")
        self.tabs.addTab(self.tab_otimizador, "Otimizador DDS")
        self.tabs.addTab(self.tab_otimizador_tga, "Otimizador TGA")