# ui_helpers.py — peças compartilhadas de layout (seções, divisórias, elisão).
from PySide6.QtWidgets import QLabel, QFrame
from PySide6.QtCore import Qt


def step(text):
    w = QLabel(text)
    w.setObjectName("StepTitle")
    return w


def field(text):
    w = QLabel(text)
    w.setObjectName("FieldLabel")
    return w


def hint(text):
    w = QLabel(text)
    w.setObjectName("Hint")
    w.setWordWrap(True)
    return w


def muted(text=""):
    w = QLabel(text)
    w.setObjectName("Muted")
    w.setWordWrap(True)
    return w


def separator():
    f = QFrame()
    f.setObjectName("Separator")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(2)
    return f


def elide_label(label, text, width=360):
    label.setText(label.fontMetrics().elidedText(text, Qt.TextElideMode.ElideMiddle, width))
    label.setToolTip(text)
