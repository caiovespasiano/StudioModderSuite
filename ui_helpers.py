# ui_helpers.py — peças compartilhadas de layout (seções, divisórias, elisão).
from PySide6.QtWidgets import QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt


def step(text):
    """Título de seção: pequeno, maiúsculo, discreto."""
    w = QLabel(text.upper())
    w.setObjectName("StepTitle")
    return w


def field(text):
    """Rótulo de campo: pequeno e apagado, para o valor respirar embaixo."""
    w = QLabel(text)
    w.setObjectName("FieldLabel")
    return w


def value(text=""):
    """Valor/estado de um campo: tamanho normal,-legível."""
    w = QLabel(text)
    w.setObjectName("FieldValue")
    return w


def hint(text):
    """Dica auxiliar: pequena e cinza, nunca ocupa mais que o necessário."""
    w = QLabel(text)
    w.setObjectName("Hint")
    w.setWordWrap(True)
    w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    return w


def muted(text=""):
    """Texto de estado (ex.: 'Nenhum arquivo selecionado').

    Sem wordWrap de propósito: quebra de linha inflava a altura da linha e
    abria buracos verticais no layout. Caminhos longos usam elide_label().
    """
    w = QLabel(text)
    w.setObjectName("FieldValue")
    w.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
    return w


def separator():
    f = QFrame()
    f.setObjectName("Separator")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(2)
    return f


def elide_label(label, text, width=360):
    """Mostra o texto elidido (caminho longo) e guarda o valor real no tooltip."""
    metrics = label.fontMetrics()
    label.setText(metrics.elidedText(text, Qt.TextElideMode.ElideMiddle, max(120, width)))
    label.setToolTip(text)
    label.setWordWrap(False)