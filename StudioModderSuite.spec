# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('meu_icone.ico', '.'), ('logo_dimitrius.png', '.'), ('github_mark.svg', '.'), ('tools/texconv/texconv.exe', 'tools/texconv'), ('tools/texconv/LICENSE.txt', 'tools/texconv')],
    hiddenimports=['PySide6.QtXml', 'suite_ferramentas', 'theme', 'ui_helpers', 'paths', 'app_state', 'aba_copiadora', 'aba_renomeador', 'aba_multi_copiador', 'aba_otimizador_dds', 'aba_otimizador_tga', 'PIL', 'PIL.Image'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='StudioModderSuite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['meu_icone.ico'],
)
