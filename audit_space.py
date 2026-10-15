# audit_space.py — mede espaço morto (faixas vazias) em cada tela.
import os
import sys

from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtGui import QFontDatabase, QFont

app = QApplication(sys.argv)
QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.No
QMessageBox.critical = lambda *a, **k: QMessageBox.StandardButton.No
QMessageBox.information = lambda *a, **k: QMessageBox.StandardButton.Yes
QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes

from theme import apply_theme
apply_theme(app)

TOL = 24  # px tolerados antes de considerar "espaço morto"


def content_rect(host):
    """Retângulo que engloba todos os filhos visíveis de host."""
    rects = [c.geometry() for c in host.children()
             if isinstance(c, QWidget) and c.isVisible() and not c.isWindow()]
    if not rects:
        return None
    r = rects[0]
    for g in rects[1:]:
        r = r.united(g)
    return r


def report(name, host, pad=16):
    area = host.rect()
    box = content_rect(host)
    if box is None:
        print(f"{name}: sem filhos")
        return
    left = box.left() - area.left()
    right = area.right() - box.right()
    top = box.top() - area.top()
    bottom = area.bottom() - box.bottom()
    flags = []
    if right > TOL: flags.append(f"DIREITA {right}px")
    if bottom > TOL: flags.append(f"BAIXO {bottom}px")
    if left > TOL: flags.append(f"ESQUERDA {left}px")
    if top > TOL: flags.append(f"CIMA {top}px")
    status = " | ".join(flags) if flags else "OK (sem faixa morta)"
    print(f"{name:<26} {status}")


from main import Launcher
l = Launcher()
l.show()
app.processEvents()
report("LAUNCHER", l)

from suite_ferramentas import JanelaPrincipal
w = JanelaPrincipal()
w.resize(1280, 800)
w.show()
app.processEvents()

content = w.centralWidget()

# Copiador: 3 passos
w.set_current_index(0)
c = w.loaded_tabs[0]
c.selected_file = "C:/mods/skin_base.tobj"
c.selected_folder = "C:/mods/veiculos/texturas_skin"
from aba_copiadora import BlockItem
c.name_blocks = [BlockItem("skin_", "prefix"), BlockItem("NUMÉRICA", "num", {"format": "00"})]
c.refresh_assembly()
for s in range(3):
    c.goto_step(s)
    app.processEvents()
    report(f"COPIADOR paso {s+1}", content)

# Renomeador: 3 passos
w.set_current_index(1)
r = w.loaded_tabs[1]
r.arquivos_selecionados = ["C:/mods/a.dds", "C:/mods/b.dds", "C:/mods/c.dds"]
r.popular_tabela()
from aba_renomeador import BlockItem as RB
r.name_blocks = [RB("skin_", "prefix"), RB("NUMÉRICA", "num", {"format": "00"})]
r.refresh_assembly()
for s in range(3):
    r.goto_step(s)
    app.processEvents()
    report(f"RENOM passo {s+1}", content)

# Multiplo
w.set_current_index(2)
m = w.loaded_tabs[2]
m.pasta_raiz = "C:/mods"
m.popular_lista_pastas()
app.processEvents()
report("MULTIPLO", content)

# Otimizadores
for idx, nm in ((3, "DDS"), (4, "TGA")):
    w.set_current_index(idx)
    tab = w.loaded_tabs[idx]
    if idx == 3:
        tab.on_scan_finished([[f"C:/mods/t{i}.dds", 4096, 4096, "BC3_UNORM", False] for i in range(6)])
    else:
        tab.on_scan_finished([[f"C:/mods/t{i}.tga", 4096, 4096, "RGB"] for i in range(6)])
    app.processEvents()
    report(f"OTIMIZADOR {nm}", content)

app.quit()
