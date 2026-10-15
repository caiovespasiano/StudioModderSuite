# paths.py — resolução de caminhos que funciona em dev e no .exe congelado.
import os
import sys


def resource_path(relative_path):
    """Caminho de um recurso empacotado.

    Dev: pasta do projeto. Congelado (PyInstaller onefile): a pasta temporária
    _MEIPASS para onde o PyInstaller extrai as 'datas' do .spec.

    Importante: nada aqui depende do diretório atual (CWD), que no .exe é
    outro e provoca WinError 3 (caminho não encontrado).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def app_dir():
    """Pasta gravável do app: a do .exe quando congelado, a do script em dev."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def find_texconv():
    """Procura o texconv.exe em dev e dentro do executável.

    Dev: tools/texconv/texconv.exe. Congelado: _MEIPASS/tools/texconv/texconv.exe
    e, como alternativa, tools/texconv/texconv.exe ao lado do .exe.
    """
    candidates = [
        os.path.join(resource_path("tools"), "texconv", "texconv.exe"),
        os.path.join(app_dir(), "tools", "texconv", "texconv.exe"),
        os.path.join(os.getcwd(), "tools", "texconv", "texconv.exe"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return ""