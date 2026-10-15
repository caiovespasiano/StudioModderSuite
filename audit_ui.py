# audit_ui.py — renderiza cada tela com fonte real e aponta sobreposições/fixos.
import os
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QComboBox, QSpinBox, QLineEdit, QCheckBox,
    QMessageBox
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QFontDatabase

OUT = os.path.join(os.environ.get("TEMP", "."), "opencode", "audit")
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv)

# Auditoria não é interativa: neutraliza diálogos modais.
QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.No
QMessageBox.critical = lambda *a, **k: QMessageBox.StandardButton.No
QMessageBox.information = lambda *a, **k: QMessageBox.StandardButton.Yes
QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes

from theme import apply_theme, APP_QSS
apply_theme(app)

fam = QFontDatabase.families()
pick = next((f for f in fam if "Segoe UI" in f), None) or (fam[0] if fam else None)
if pick:
    app.setFont(QFont(pick, 10))
print("fonte:", pick)


def overlaps(a, b):
    if a is None or b is None:
        return 0
    if a.parentWidget() is not b.parentWidget():
        return 0
    r1, r2 = a.geometry(), b.geometry()
    if a.isHidden() or b.isHidden() or not a.isVisible() or not b.isVisible():
        return 0
    return 1 if r1.intersects(r2) else 0


def audit(name, host):
    print(f"\n=== {name} ===")
    # 1. widgets clipped por texto
    for w in host.findChildren(QWidget):
        if not w.isVisible():
            continue
        if isinstance(w, QPushButton):
            need = w.fontMetrics().horizontalAdvance(w.text()) + 34
            if w.size().width() < need and w.layout() is None:
                print(f"  [TEXTO CORTE] {w.objectName() or 'QPushButton'} '{w.text()}' w={w.size().width()} need>={need}")
        elif isinstance(w, QLabel):
            txt = w.text()
            if not txt:
                continue
            elided = w.fontMetrics().elidedText(txt, Qt.TextElideMode.ElideRight, w.width())
            if elided != txt and not w.wordWrap():
                print(f"  [LABEL CORTADO] '{txt[:50]}' w={w.width()} hint={w.toolTip()[:30]}")
    # 2. sobreposições entre irmãos
    kids = [w for w in host.findChildren(QWidget) if w.parentWidget() is host]
    kids = [w for w in kids if w.isVisible()]
    rects = [(w, w.geometry()) for w in kids]
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i][0], rects[j][0]
            if a.parentWidget() is not b.parentWidget():
                continue
            ov = overlaps(a, b)
            if ov and not (isinstance(a, QWidget) and isinstance(b, QWidget) and (a.windowFlags() & Qt.WindowType.Widget)):
                print(f"  [SOBREPOSTO] {a.objectName() or type(a).__name__} <-> {b.objectName() or type(b).__name__}")
    # 3. margins/spacing dos layouts
    for lay in host.findChildren(type(host.layout()) if host.layout() else object):
        pass
    print("  size:", host.size().width(), "x", host.size().height())


from main import Launcher
l = Launcher()
l.resize(560, 700)
l.show()
app.processEvents()
l.grab().save(os.path.join(OUT, "launcher.png"))
audit("LAUNCHER", l)

from suite_ferramentas import JanelaPrincipal
w = JanelaPrincipal()
w.show()
for i in range(5):
    app.processEvents()

names = ["cop1", "cop2", "cop3", "ren1", "ren2", "ren3", "multi", "dds", "tga"]
# Copiador passos
c = w.loaded_tabs[0] if w.loaded_tabs[0] else None
w.set_current_index(0)
c = w.loaded_tabs[0]
c.selected_file = "C:/mods/skin_base.tobj"
c.selected_folder = "C:/mods/veiculos/texturas_skin"
from aba_copiadora import BlockItem
c.name_blocks = [BlockItem("skin_", "prefix"), BlockItem("NUMÉRICA", "num", {"format": "00"})]
c.refresh_assembly()
for s, nm in ((0, "cop1"), (1, "cop2"), (2, "cop3")):
    c.goto_step(s)
    app.processEvents()
    w.grab().save(os.path.join(OUT, nm + ".png"))
    audit("COPIADOR paso " + str(s + 1), w.centralWidget())

w.set_current_index(1)
r = w.loaded_tabs[1]
r.arquivos_selecionados = ["C:/mods/a.dds", "C:/mods/b.dds", "C:/mods/c.dds"]
r.popular_tabela()
from aba_renomeador import BlockItem as RB
r.name_blocks = [RB("skin_", "prefix"), RB("NUMÉRICA", "num", {"format": "00"})]
r.refresh_assembly()
for s, nm in ((0, "ren1"), (1, "ren2"), (2, "ren3")):
    r.goto_step(s)
    app.processEvents()
    w.grab().save(os.path.join(OUT, nm + ".png"))
    audit("RENOM passo " + str(s + 1), w.centralWidget())

w.set_current_index(2)
m = w.loaded_tabs[2]
m.pasta_raiz = "C:/mods"
m.popular_lista_pastas()
app.processEvents()
w.grab().save(os.path.join(OUT, "multi.png"))
audit("MULTI", w.centralWidget())

for idx, nm in ((3, "dds"), (4, "tga")):
    w.set_current_index(idx)
    tab = w.loaded_tabs[idx]
    cls = "AbaOtimizadorDDS" if idx == 3 else "AbaOtimizadorTGA"
    ext = "dds" if idx == 3 else "tga"
    if idx == 3:
        res = [[f"C:/mods/texture_{i}.dds", 4096, 4096, "BC3_UNORM", False] for i in range(6)]
    else:
        res = [[f"C:/mods/texture_{i}.tga", 4096, 4096, "RGB"] for i in range(6)]
    tab.on_scan_finished(res)
    app.processEvents()
    w.grab().save(os.path.join(OUT, nm + ".png"))
    audit(nm.upper(), w.centralWidget())

print("\nSAIDA:", OUT)
app.quit()