# PY2EXE // By Fistikcan

import sys
import os
import subprocess
import threading
import json
import webbrowser
import socket
import multiprocessing

import webview

def ensure_single_instance():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', 51234))
        return sock
    except socket.error:
        sys.exit(0)

_single_instance_sock = ensure_single_instance()

class Api:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def choose_file(self):
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=('Python Files (*.py)',)
        )
        return result[0] if result else None

    def browse_file(self):
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=('All Files (*.*)',)
        )
        return result[0] if result else None

    def browse_folder(self):
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    def open_url(self, url):
        webbrowser.open(url)

    def start_build(self, script_path, args):
        def build():
            cmd = [sys.executable, "-m", "PyInstaller", script_path] + args
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            progress = 0
            for line in process.stdout:
                safe_line = json.dumps(line)
                webview.windows[0].evaluate_js(f"addLogLine({safe_line});")
                lower = line.lower()
                if "analyzing" in lower:
                    progress = 10
                    webview.windows[0].evaluate_js(f"updateProgress({progress}, 'analyzing');")
                elif "processing" in lower:
                    progress = 25
                    webview.windows[0].evaluate_js(f"updateProgress({progress}, 'processing');")
                elif "building pkg" in lower or "building package" in lower:
                    progress = 50
                    webview.windows[0].evaluate_js(f"updateProgress({progress}, 'packaging');")
                elif "building exe" in lower:
                    progress = 75
                    webview.windows[0].evaluate_js(f"updateProgress({progress}, 'building_exe');")
                elif "copying" in lower:
                    progress = 90
                    webview.windows[0].evaluate_js(f"updateProgress({progress}, 'copying');")
                elif "completed" in lower or "success" in lower:
                    progress = 100
                    webview.windows[0].evaluate_js(f"updateProgress({progress}, 'completed');")
            process.wait()
            if progress < 100:
                webview.windows[0].evaluate_js("updateProgress(100, 'completed');")
            webview.windows[0].evaluate_js("buildFinished();")
        threading.Thread(target=build, daemon=True).start()
        return True

api = Api()

options = [
    {"section": "Çıktı Formatı"},
    {"flag": "--onefile", "desc_tr": "Tek bir exe dosyası oluşturur.", "desc_en": "Create a single exe file.", "type": "bool", "group": "output_mode"},
    {"flag": "--onedir", "desc_tr": "Klasör yapısında çıktı oluşturur.", "desc_en": "Output as a directory structure.", "type": "bool", "group": "output_mode"},

    {"section": "Genel Ayarlar"},
    {"flag": "--name", "desc_tr": "Uygulama adını belirler.", "desc_en": "Set the application name.", "type": "text", "placeholder": "UygulamaAdı"},
    {"flag": "--distpath", "desc_tr": "Çıktı klasörü.", "desc_en": "Output directory.", "type": "path", "placeholder": "dist/"},
    {"flag": "--workpath", "desc_tr": "Geçici dosya klasörü.", "desc_en": "Temporary build directory.", "type": "path", "placeholder": "build/"},
    {"flag": "--specpath", "desc_tr": "Spec dosyası dizini.", "desc_en": "Spec file directory.", "type": "path", "placeholder": "."},
    {"flag": "--contents-directory", "desc_tr": "İçerik alt klasörü.", "desc_en": "Subfolder for contents.", "type": "text", "placeholder": "internal"},
    {"flag": "--clean", "desc_tr": "Önceki geçici dosyaları temizler.", "desc_en": "Clean previous build files.", "type": "bool"},
    {"flag": "--noconfirm", "desc_tr": "Çıktı klasörünü sormadan üzerine yazar.", "desc_en": "Overwrite output without asking.", "type": "bool"},
    {"flag": "--log-level", "desc_tr": "Günlük seviyesi.", "desc_en": "Log level.", "type": "choice", "choices": ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]},
    {"flag": "--debug", "desc_tr": "Hata ayıklama modu.", "desc_en": "Debug mode.", "type": "text", "placeholder": "all"},
    {"flag": "--optimize", "desc_tr": "Python optimizasyon seviyesi (0,1,2).", "desc_en": "Python optimization level (0,1,2).", "type": "int", "placeholder": "0"},
    {"flag": "--python-option", "desc_tr": "Python yorumlayıcı seçeneği.", "desc_en": "Python interpreter option.", "type": "text", "placeholder": "X"},
    {"flag": "--strip", "desc_tr": "Sembolleri kaldırır.", "desc_en": "Strip symbols.", "type": "bool"},

    {"section": "Dahil Etme / Hariç Tutma"},
    {"flag": "--add-data", "desc_tr": "Veri dosyası ekle (kaynak:hedef).", "desc_en": "Add data file (source:dest).", "type": "text", "placeholder": "veri.txt:.", "multiple": True},
    {"flag": "--add-binary", "desc_tr": "Binary dosya ekle (kaynak:hedef).", "desc_en": "Add binary file (source:dest).", "type": "text", "placeholder": "lib.dll:.", "multiple": True},
    {"flag": "--paths", "desc_tr": "Modül arama yolları (; ile ayır).", "desc_en": "Module search paths (; separated).", "type": "text", "placeholder": "C:\\eklentiler", "multiple": True},
    {"flag": "--hidden-import", "desc_tr": "Gizli modül ekle.", "desc_en": "Add hidden import.", "type": "text", "placeholder": "modül_adı", "multiple": True},
    {"flag": "--collect-submodules", "desc_tr": "Paketin tüm alt modüllerini topla.", "desc_en": "Collect all submodules.", "type": "text", "placeholder": "paket", "multiple": True},
    {"flag": "--collect-data", "desc_tr": "Paketin veri dosyalarını topla.", "desc_en": "Collect package data.", "type": "text", "placeholder": "paket", "multiple": True},
    {"flag": "--collect-binaries", "desc_tr": "Paketin binary’lerini topla.", "desc_en": "Collect package binaries.", "type": "text", "placeholder": "paket", "multiple": True},
    {"flag": "--collect-all", "desc_tr": "Paketin tüm kaynaklarını topla.", "desc_en": "Collect all package resources.", "type": "text", "placeholder": "paket", "multiple": True},
    {"flag": "--copy-metadata", "desc_tr": "Meta veriyi kopyala.", "desc_en": "Copy metadata.", "type": "text", "placeholder": "paket", "multiple": True},
    {"flag": "--recursive-copy-metadata", "desc_tr": "Meta veriyi alt paketlerle kopyala.", "desc_en": "Recursively copy metadata.", "type": "text", "placeholder": "paket", "multiple": True},
    {"flag": "--additional-hooks-dir", "desc_tr": "Ek hook dizini.", "desc_en": "Additional hooks directory.", "type": "path", "multiple": True},
    {"flag": "--runtime-hook", "desc_tr": "Çalışma zamanı hook dosyası.", "desc_en": "Runtime hook file.", "type": "path", "multiple": True},
    {"flag": "--exclude-module", "desc_tr": "Modülü hariç tut.", "desc_en": "Exclude module.", "type": "text", "placeholder": "modül", "multiple": True},

    {"section": "Konsol / Pencere Modu"},
    {"flag": "--console", "desc_tr": "Konsol penceresini aç.", "desc_en": "Open console window.", "type": "bool", "group": "console_mode"},
    {"flag": "--noconsole", "desc_tr": "Konsolu tamamen gizle.", "desc_en": "Hide console completely.", "type": "bool", "group": "console_mode"},
    {"flag": "--windowed", "desc_tr": "Konsol penceresi olmadan başlat.", "desc_en": "Run without console window.", "type": "bool", "group": "console_mode"},
    {"flag": "--nowindowed", "desc_tr": "Konsol penceresini zorla göster.", "desc_en": "Force console window.", "type": "bool", "group": "console_mode"},
    {"flag": "--hide-console", "desc_tr": "Konsolu gizle.", "desc_en": "Hide console.", "type": "bool", "group": "console_mode"},

    {"section": "Windows / macOS"},
    {"flag": "--icon", "desc_tr": "Uygulama simgesi (.ico/.icns).", "desc_en": "Application icon (.ico/.icns).", "type": "path"},
    {"flag": "--version-file", "desc_tr": "Sürüm bilgi dosyası (Windows).", "desc_en": "Version file (Windows).", "type": "path"},
    {"flag": "--manifest", "desc_tr": "Uygulama manifest dosyası (Windows).", "desc_en": "Manifest file (Windows).", "type": "path"},
    {"flag": "--resource", "desc_tr": "Kaynak ekle (Windows).", "desc_en": "Add resource (Windows).", "type": "text", "placeholder": "DOSYA,1,ICON"},
    {"flag": "--uac-admin", "desc_tr": "Yönetici olarak çalıştır (Windows).", "desc_en": "Run as admin (Windows).", "type": "bool"},
    {"flag": "--uac-uiaccess", "desc_tr": "UI erişimi iste (Windows).", "desc_en": "Request UI access (Windows).", "type": "bool"},
    {"flag": "--win-private-assemblies", "desc_tr": "Özel derlemeleri dahil et (Windows).", "desc_en": "Include private assemblies (Windows).", "type": "bool"},
    {"flag": "--win-no-prefer-redirects", "desc_tr": "Yönlendirmeyi devre dışı bırak (Windows).", "desc_en": "Disable redirects (Windows).", "type": "bool"},
    {"flag": "--argv-emulation", "desc_tr": "Argüman emülasyonu (macOS).", "desc_en": "Argument emulation (macOS).", "type": "bool"},
    {"flag": "--osx-bundle-identifier", "desc_tr": "Paket kimliği (macOS).", "desc_en": "Bundle identifier (macOS).", "type": "text", "placeholder": "com.uygulama"},
    {"flag": "--codesign-identity", "desc_tr": "Kod imzalama kimliği (macOS).", "desc_en": "Codesign identity (macOS).", "type": "text"},
    {"flag": "--osx-entitlements-file", "desc_tr": "Yetki dosyası (macOS).", "desc_en": "Entitlements file (macOS).", "type": "path"},
    {"flag": "--target-architecture", "desc_tr": "Hedef mimari.", "desc_en": "Target architecture.", "type": "choice", "choices": ["x86", "x64", "arm64"]},
    {"flag": "--target-arch", "desc_tr": "Hedef mimari (kısa).", "desc_en": "Target architecture (short).", "type": "choice", "choices": ["x86", "x64", "arm64"]},

    {"section": "Diğer"},
    {"flag": "--upx-dir", "desc_tr": "UPX sıkıştırıcı dizini.", "desc_en": "UPX directory.", "type": "path"},
    {"flag": "--noupx", "desc_tr": "UPX kullanma.", "desc_en": "Disable UPX.", "type": "bool"},
    {"flag": "--upx-exclude", "desc_tr": "UPX dışlanacak dosya.", "desc_en": "UPX exclude file.", "type": "text", "multiple": True},
    {"flag": "--runtime-tmpdir", "desc_tr": "Geçici çalışma dizini.", "desc_en": "Runtime temp directory.", "type": "path"},
    {"flag": "--splash", "desc_tr": "Açılış ekranı resmi.", "desc_en": "Splash image.", "type": "path"},
    {"flag": "--disable-windowed-traceback", "desc_tr": "Hata penceresini kapat.", "desc_en": "Disable error window.", "type": "bool"},
    {"flag": "--bootloader-ignore-signals", "desc_tr": "Sinyalleri yoksay.", "desc_en": "Ignore signals.", "type": "bool"}
]

options_json = json.dumps(options)

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    body {{
        background: #1e1e1e;
        color: #e0e0e0;
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow: hidden;
        user-select: none;
    }}
    .header {{
        background: #2d2d2d;
        padding: 12px 20px;
        font-size: 20px;
        font-weight: bold;
        color: #93c90f;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        flex-wrap: wrap;
    }}
    .header .title {{ flex: 1; white-space: nowrap; }}
    .header button {{
        background: #3a3a3a;
        color: #ccc;
        border: none;
        border-radius: 6px;
        padding: 4px 12px;
        cursor: pointer;
        font-size: 13px;
        font-weight: bold;
        transition: background 0.2s;
    }}
    .header button:hover {{ background: #4a4a4a; }}
    .github-link {{
        color: #aaa;
        font-size: 13px;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        margin-left: 10px;
    }}
    .github-link:hover {{ color: #93c90f; }}

    .content {{
        flex: 1;
        position: relative;
        overflow: hidden;
    }}
    .page {{
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        padding: 20px;
        opacity: 0;
        transform: translateY(12px);
        transition: opacity 0.35s ease, transform 0.35s ease;
        pointer-events: none;
        display: flex;
        flex-direction: column;
    }}
    .page.active {{
        opacity: 1;
        transform: translateY(0);
        pointer-events: auto;
    }}
    .footer {{
        background: #2d2d2d;
        padding: 10px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.5);
        gap: 10px;
    }}
    button {{
        background: #93c90f;
        border: none;
        color: #1e1e1e;
        font-weight: bold;
        padding: 8px 18px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        transition: background 0.2s, transform 0.1s, box-shadow 0.2s;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }}
    button:hover {{ background: #a8e010; transform: scale(1.03); box-shadow: 0 4px 12px rgba(147, 201, 15, 0.3); }}
    button:active {{ transform: scale(0.98); }}
    button.secondary {{
        background: #3a3a3a;
        color: #ccc;
    }}
    button.secondary:hover {{ background: #4a4a4a; }}

    .drop-zone {{
        flex: 1;
        border: 2px dashed #555;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 15px;
        transition: border-color 0.2s, background 0.2s, transform 0.2s;
        background: #252525;
        cursor: pointer;
    }}
    .drop-zone:hover {{ border-color: #93c90f; background: #2a3320; }}
    .file-path {{
        margin-top: 10px;
        font-size: 13px;
        color: #aaa;
        word-break: break-all;
        text-align: center;
    }}

    .options-container {{
        flex: 1;
        overflow-y: auto;
        padding-right: 8px;
    }}
    .section-title {{
        font-weight: bold;
        color: #93c90f;
        margin: 18px 0 8px;
        font-size: 15px;
        border-bottom: 1px solid #333;
        padding-bottom: 4px;
    }}
    .options-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
        gap: 10px;
        margin-bottom: 10px;
    }}
    .option-card {{
        background: #2a2a2a;
        border-radius: 8px;
        padding: 10px 12px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        transition: background 0.2s, box-shadow 0.2s;
        border: 1px solid #333;
        position: relative;
    }}
    .option-card:hover {{ background: #333; box-shadow: 0 2px 8px rgba(0,0,0,0.4); }}
    .option-label {{
        flex: 1;
        font-size: 13px;
        font-weight: 500;
        min-width: 120px;
        text-align: left;
        padding-left: 4px;
    }}
    .option-input {{
        background: #1e1e1e;
        border: 1px solid #555;
        color: #ddd;
        padding: 4px 8px;
        border-radius: 4px;
        width: 100%;
        margin-top: 6px;
        font-size: 12px;
        display: none;
    }}
    .option-card.checked .option-input {{ display: block; }}
    .option-input-group {{
        width: 100%;
        margin-top: 6px;
        display: none;
        flex-direction: column;
        gap: 4px;
    }}
    .option-card.checked .option-input-group {{ display: flex; }}
    .input-row {{
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .input-row input {{
        flex: 1;
        background: #1e1e1e;
        border: 1px solid #555;
        color: #ddd;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
    }}
    .add-btn {{
        background: #555;
        border: none;
        color: #ccc;
        font-weight: bold;
        padding: 2px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        line-height: 1;
        margin-left: auto;
        transition: background 0.2s, color 0.2s;
    }}
    .add-btn:hover {{ background: #93c90f; color: #1e1e1e; }}
    .toggle {{
        position: relative;
        width: 40px;
        height: 20px;
        margin-right: 6px;
    }}
    .toggle input {{ opacity: 0; width: 0; height: 0; }}
    .slider {{
        position: absolute;
        cursor: pointer;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: #555;
        border-radius: 20px;
        transition: 0.2s;
    }}
    .slider:before {{
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 2px;
        bottom: 2px;
        background-color: white;
        border-radius: 50%;
        transition: 0.2s;
    }}
    input:checked + .slider {{ background-color: #93c90f; }}
    input:checked + .slider:before {{ transform: translateX(20px); }}

    .info-icon {{
        margin-left: 8px;
        margin-right: 4px;
        color: #aaa;
        cursor: help;
        font-weight: bold;
        position: relative;
        font-size: 14px;
        z-index: 5;
        order: 1;
    }}
    .browse-btn {{
        background: #3a3a3a;
        color: #ccc;
        border: none;
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 4px;
        cursor: pointer;
        font-size: 12px;
        order: 0;
        margin-right: 4px;
    }}
    .browse-btn:hover {{ background: #555; }}

    .tooltip {{
        display: none;
        position: absolute;
        background: #444;
        color: #eee;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        white-space: normal;
        max-width: 220px;
        width: max-content;
        z-index: 100;
        border: 1px solid #93c90f;
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        pointer-events: none;
        line-height: 1.4;
        text-align: left;
    }}
    .info-icon:hover .tooltip,
    .info-icon.show-tooltip .tooltip {{ display: block; }}

    .tooltip-top {{ bottom: 120%; left: 50%; transform: translateX(-50%); }}
    .tooltip-bottom {{ top: 120%; left: 50%; transform: translateX(-50%); }}
    .tooltip-left {{ right: 110%; top: 50%; transform: translateY(-50%); }}
    .tooltip-right {{ left: 110%; top: 50%; transform: translateY(-50%); }}

    .build-status {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 20px;
        flex: 1;
    }}
    .spinner {{
        width: 60px;
        height: 60px;
        border: 4px solid #333;
        border-top-color: #93c90f;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .checkmark {{
        display: none;
        width: 60px;
        height: 60px;
    }}
    .checkmark svg {{
        width: 100%;
        height: 100%;
        stroke: #93c90f;
        stroke-width: 4;
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
        animation: draw 0.5s ease forwards;
    }}
    @keyframes draw {{
        from {{ stroke-dashoffset: 100; }}
        to {{ stroke-dashoffset: 0; }}
    }}
    .status-text {{
        font-size: 16px;
        color: #ccc;
        text-align: center;
        min-height: 24px;
    }}
    .progress-container {{
        width: 80%;
        max-width: 400px;
        background: #333;
        border-radius: 8px;
        height: 10px;
        overflow: hidden;
    }}
    .progress-fill {{
        width: 0%;
        height: 100%;
        background: linear-gradient(90deg, #93c90f, #c3f040);
        border-radius: 8px;
        transition: width 0.3s ease;
    }}
    .console-wrapper {{
        display: none;
        flex-direction: column;
        max-height: 40%;
        margin-top: 10px;
    }}
    .console {{
        flex: 1;
        background: #111;
        border-radius: 8px;
        padding: 15px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #93c90f;
        white-space: pre-wrap;
        margin-bottom: 8px;
        min-height: 80px;
        max-height: 150px;
    }}
    .terminal-toggle {{
        align-self: center;
        margin-top: 5px;
    }}
    .back-home-btn {{
        display: none;
        margin-top: 20px;
    }}
    .browse-output-btn {{
        display: none;
        margin-top: 10px;
    }}
</style>
</head>
<body>
<div class="header">
    <span class="title">🐍 PY2EXE // By Fıstıkcan</span>
    <button id="langBtn">EN</button>
    <div class="github-link" id="githubLink">
        <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
        GitHub
    </div>
</div>

<div class="content">
    <div id="page1" class="page active">
        <div class="drop-zone" id="dropZone">
            <div style="font-size: 32px;">📁</div>
            <div id="dropText">Python dosyasını seçmek için tıklayın</div>
            <div style="font-size: 13px; color: #888;" id="dropSubText">veya bu alana tıklayın</div>
            <button id="selectBtn" style="margin-top: 5px;" data-key="select_file">Dosya Seç</button>
        </div>
        <div class="file-path" id="filePathDisplay"></div>
    </div>

    <div id="page2" class="page">
        <div style="margin-bottom: 12px; font-weight: bold; color: #93c90f; font-size: 15px;" data-key="build_options">Derleme Seçenekleri</div>
        <div class="options-container" id="optionsContainer"></div>
    </div>

    <div id="page3" class="page">
        <div class="build-status" id="buildStatus">
            <div class="spinner" id="spinner"></div>
            <div class="checkmark" id="checkmark">
                <svg viewBox="0 0 100 100">
                    <path d="M20 50 L40 70 L80 30" stroke-dasharray="100" stroke-dashoffset="100"/>
                </svg>
            </div>
            <div class="status-text" id="statusText">Hazırlanıyor...</div>
            <div class="progress-container">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <button class="back-home-btn secondary" id="backHomeBtn" data-key="back_home">Ana Ekrana Dön</button>
            <button class="browse-output-btn secondary" id="browseOutputBtn">📂 Çıktı Klasörünü Aç</button>
        </div>
        <div class="console-wrapper" id="consoleWrapper">
            <div class="console" id="consoleOutput"></div>
        </div>
        <button class="terminal-toggle secondary" id="terminalToggle" style="display:none;" data-key="show_terminal">📄 Terminali Göster</button>
    </div>
</div>

<div class="footer">
    <button id="backBtn" class="secondary" style="display:none;">← <span data-key="back">Geri</span></button>
    <button id="nextBtn"><span data-key="next">İleri</span> →</button>
    <button id="buildBtn" style="display:none;" data-key="start_build">🚀 Derlemeyi Başlat</button>
</div>

<script>
    const OPTIONS = {options_json};

    const LANG = {{
        tr: {{
            select_file: "Dosya Seç",
            drop_text: "Python dosyasını seçmek için tıklayın",
            drop_sub: "veya bu alana tıklayın",
            build_options: "Derleme Seçenekleri",
            back: "Geri",
            next: "İleri",
            start_build: "🚀 Derlemeyi Başlat",
            show_terminal: "📄 Terminali Göster",
            hide_terminal: "📄 Terminali Gizle",
            back_home: "Ana Ekrana Dön",
            preparing: "Hazırlanıyor...",
            analyzing: "Analiz ediliyor...",
            processing: "Modüller işleniyor...",
            packaging: "Paket oluşturuluyor...",
            building_exe: "EXE oluşturuluyor...",
            copying: "Dosyalar kopyalanıyor...",
            completed: "✅ Derleme tamamlandı!",
            section_output: "Çıktı Formatı",
            section_general: "Genel Ayarlar",
            section_includes: "Dahil Etme / Hariç Tutma",
            section_console: "Konsol / Pencere Modu",
            section_platform: "Windows / macOS",
            section_other: "Diğer"
        }},
        en: {{
            select_file: "Select File",
            drop_text: "Click to select Python file",
            drop_sub: "or click this area",
            build_options: "Build Options",
            back: "Back",
            next: "Next",
            start_build: "🚀 Start Build",
            show_terminal: "📄 Show Terminal",
            hide_terminal: "📄 Hide Terminal",
            back_home: "Back to Home",
            preparing: "Preparing...",
            analyzing: "Analyzing...",
            processing: "Processing modules...",
            packaging: "Building package...",
            building_exe: "Building EXE...",
            copying: "Copying files...",
            completed: "✅ Build completed!",
            section_output: "Output Format",
            section_general: "General Settings",
            section_includes: "Includes / Excludes",
            section_console: "Console / Window Mode",
            section_platform: "Windows / macOS",
            section_other: "Other"
        }}
    }};

    let currentLang = 'tr';
    let currentPage = 1;
    let selectedFile = null;
    let terminalVisible = false;

    const page1 = document.getElementById('page1');
    const page2 = document.getElementById('page2');
    const page3 = document.getElementById('page3');
    const backBtn = document.getElementById('backBtn');
    const nextBtn = document.getElementById('nextBtn');
    const buildBtn = document.getElementById('buildBtn');
    const dropZone = document.getElementById('dropZone');
    const filePathDisplay = document.getElementById('filePathDisplay');
    const optionsContainer = document.getElementById('optionsContainer');
    const consoleOutput = document.getElementById('consoleOutput');
    const consoleWrapper = document.getElementById('consoleWrapper');
    const terminalToggle = document.getElementById('terminalToggle');
    const statusText = document.getElementById('statusText');
    const progressFill = document.getElementById('progressFill');
    const buildStatusDiv = document.getElementById('buildStatus');
    const backHomeBtn = document.getElementById('backHomeBtn');
    const browseOutputBtn = document.getElementById('browseOutputBtn');
    const spinner = document.getElementById('spinner');
    const checkmark = document.getElementById('checkmark');
    const langBtn = document.getElementById('langBtn');

    function applyLang(lang) {{
        currentLang = lang;
        document.querySelectorAll('[data-key]').forEach(el => {{
            const key = el.getAttribute('data-key');
            if (LANG[lang][key]) el.textContent = LANG[lang][key];
        }});
        document.getElementById('dropText').textContent = LANG[lang].drop_text;
        document.getElementById('dropSubText').textContent = LANG[lang].drop_sub;
        if (statusText.getAttribute('data-key') === 'preparing') statusText.textContent = LANG[lang].preparing;
        document.querySelectorAll('.section-title').forEach(title => {{
            const sec = title.getAttribute('data-section');
            if (sec && LANG[lang][sec]) title.textContent = LANG[lang][sec];
        }});
        if (terminalVisible) terminalToggle.textContent = LANG[lang].hide_terminal;
        else terminalToggle.textContent = LANG[lang].show_terminal;
        langBtn.textContent = lang === 'tr' ? 'EN' : 'TR';
        document.querySelectorAll('.info-icon').forEach(icon => {{
            const flag = icon.getAttribute('data-flag');
            const option = OPTIONS.find(o => o.flag === flag);
            if (option) {{
                const tooltip = icon.querySelector('.tooltip');
                if (tooltip) {{
                    tooltip.textContent = lang === 'tr' ? option.desc_tr : option.desc_en;
                }}
            }}
        }});
    }}

    langBtn.addEventListener('click', () => {{
        applyLang(currentLang === 'tr' ? 'en' : 'tr');
    }});

    function showPage(page) {{
        currentPage = page;
        page1.classList.toggle('active', page === 1);
        page2.classList.toggle('active', page === 2);
        page3.classList.toggle('active', page === 3);
        backBtn.style.display = page > 1 ? 'inline-block' : 'none';
        nextBtn.style.display = page === 1 ? 'inline-block' : 'none';
        buildBtn.style.display = page === 2 ? 'inline-block' : 'none';
        if (page === 3) {{
            terminalToggle.style.display = 'inline-block';
            backHomeBtn.style.display = 'none';
            browseOutputBtn.style.display = 'none';
        }} else {{
            terminalToggle.style.display = 'none';
            consoleWrapper.style.display = 'none';
            terminalVisible = false;
            terminalToggle.textContent = LANG[currentLang].show_terminal;
            backHomeBtn.style.display = 'none';
            browseOutputBtn.style.display = 'none';
            spinner.style.display = 'block';
            checkmark.style.display = 'none';
        }}
    }}

    async function pickFile(e) {{
        e.stopPropagation();
        const path = await pywebview.api.choose_file();
        if (path) setSelectedFile(path);
    }}

    document.getElementById('selectBtn').addEventListener('click', pickFile);
    dropZone.addEventListener('click', pickFile);
    dropZone.addEventListener('dragover', (e) => {{ e.preventDefault(); dropZone.classList.add('drag-over'); }});
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', (e) => {{ e.preventDefault(); dropZone.classList.remove('drag-over'); pickFile(e); }});

    function setSelectedFile(path) {{
        selectedFile = path;
        filePathDisplay.textContent = 'Seçilen: ' + path;
        showPage(2);
    }}

    nextBtn.addEventListener('click', () => {{
        if (!selectedFile) {{
            alert('Lütfen önce bir Python dosyası seçin.');
            return;
        }}
        showPage(2);
    }});
    backBtn.addEventListener('click', () => {{
        if (currentPage === 2) showPage(1);
        else if (currentPage === 3) showPage(2);
    }});

    document.getElementById('githubLink').addEventListener('click', () => {{
        pywebview.api.open_url('https://github.com/Fistikcan');
    }});

    terminalToggle.addEventListener('click', () => {{
        terminalVisible = !terminalVisible;
        if (terminalVisible) {{
            consoleWrapper.style.display = 'flex';
            terminalToggle.textContent = LANG[currentLang].hide_terminal;
        }} else {{
            consoleWrapper.style.display = 'none';
            terminalToggle.textContent = LANG[currentLang].show_terminal;
        }}
    }});

    backHomeBtn.addEventListener('click', () => {{
        showPage(1);
        consoleOutput.textContent = '';
    }});

    browseOutputBtn.addEventListener('click', () => {{
        pywebview.api.browse_folder();
    }});

    function buildOptionsUI() {{
        optionsContainer.innerHTML = '';
        let gridDiv = null;

        OPTIONS.forEach(opt => {{
            if (opt.section) {{
                const title = document.createElement('div');
                title.className = 'section-title';
                const sectionMap = {{
                    'Çıktı Formatı': 'section_output',
                    'Genel Ayarlar': 'section_general',
                    'Dahil Etme / Hariç Tutma': 'section_includes',
                    'Konsol / Pencere Modu': 'section_console',
                    'Windows / macOS': 'section_platform',
                    'Diğer': 'section_other'
                }};
                const secKey = sectionMap[opt.section] || 'section_other';
                title.setAttribute('data-section', secKey);
                title.textContent = LANG[currentLang][secKey] || opt.section;
                optionsContainer.appendChild(title);
                gridDiv = document.createElement('div');
                gridDiv.className = 'options-grid';
                optionsContainer.appendChild(gridDiv);
                return;
            }}

            if (!gridDiv) {{
                gridDiv = document.createElement('div');
                gridDiv.className = 'options-grid';
                optionsContainer.appendChild(gridDiv);
            }}

            const card = document.createElement('div');
            card.className = 'option-card';
            const flag = opt.flag;
            const group = opt.group;
            const multiple = opt.multiple || false;

            const toggle = document.createElement('label');
            toggle.className = 'toggle';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.dataset.flag = flag;
            if (group) checkbox.dataset.group = group;
            toggle.appendChild(checkbox);
            const slider = document.createElement('span');
            slider.className = 'slider';
            toggle.appendChild(slider);

            const label = document.createElement('span');
            label.className = 'option-label';
            label.textContent = flag;

            const info = document.createElement('span');
            info.className = 'info-icon';
            info.setAttribute('data-flag', flag);
            info.textContent = '?';
            const tooltip = document.createElement('span');
            tooltip.className = 'tooltip';
            tooltip.textContent = currentLang === 'tr' ? opt.desc_tr : opt.desc_en;
            info.appendChild(tooltip);
            info.addEventListener('click', (e) => {{
                e.stopPropagation();
                info.classList.add('show-tooltip');
                setTimeout(() => info.classList.remove('show-tooltip'), 1000);
            }});

            let inputContainer = null;
            if (['text', 'path', 'int', 'choice'].includes(opt.type) && !multiple) {{
                inputContainer = document.createElement('input');
                inputContainer.className = 'option-input';
                inputContainer.placeholder = opt.placeholder || '';
                if (opt.type === 'int') inputContainer.type = 'number';
                else inputContainer.type = 'text';
                if (opt.type === 'choice' && opt.choices) {{
                    inputContainer = document.createElement('select');
                    inputContainer.className = 'option-input';
                    opt.choices.forEach(c => {{
                        const optEl = document.createElement('option');
                        optEl.value = c;
                        optEl.textContent = c;
                        inputContainer.appendChild(optEl);
                    }});
                }}
            }} else if (multiple) {{
                inputContainer = document.createElement('div');
                inputContainer.className = 'option-input-group';
                addInputRow(inputContainer, opt.placeholder || '');
                const addBtn = document.createElement('button');
                addBtn.className = 'add-btn';
                addBtn.textContent = '+';
                addBtn.style.marginLeft = 'auto';
                addBtn.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    addInputRow(inputContainer, opt.placeholder || '');
                }});
                card.appendChild(addBtn);
            }}

            checkbox.addEventListener('change', function() {{
                if (group) {{
                    if (this.checked) {{
                        document.querySelectorAll(`input[data-group="${{group}}"]`).forEach(cb => {{
                            if (cb !== this) {{
                                cb.checked = false;
                                cb.closest('.option-card').classList.remove('checked');
                            }}
                        }});
                        card.classList.add('checked');
                    }} else {{
                        card.classList.remove('checked');
                    }}
                }} else {{
                    if (checkbox.checked) card.classList.add('checked');
                    else card.classList.remove('checked');
                }}
            }});

            card.appendChild(toggle);
            card.appendChild(label);

            if (opt.type === 'path' && !multiple) {{
                const browse = document.createElement('button');
                browse.className = 'browse-btn';
                browse.textContent = '📂';
                browse.addEventListener('click', async (e) => {{
                    e.stopPropagation();
                    const p = await pywebview.api.browse_file();
                    if (p && inputContainer) inputContainer.value = p;
                }});
                card.appendChild(browse);
            }}

            card.appendChild(info);
            if (inputContainer) card.appendChild(inputContainer);
            gridDiv.appendChild(card);
        }});

        adjustTooltips();
        window.addEventListener('resize', adjustTooltips);
    }}

    function addInputRow(container, placeholder) {{
        const row = document.createElement('div');
        row.className = 'input-row';
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = placeholder;
        const removeBtn = document.createElement('button');
        removeBtn.className = 'add-btn';
        removeBtn.textContent = '×';
        removeBtn.style.background = '#555';
        removeBtn.addEventListener('click', (e) => {{
            e.stopPropagation();
            row.remove();
        }});
        row.appendChild(input);
        row.appendChild(removeBtn);
        container.appendChild(row);
    }}

    function adjustTooltips() {{
        document.querySelectorAll('.info-icon').forEach(icon => {{
            const tooltip = icon.querySelector('.tooltip');
            if (!tooltip) return;
            const rect = icon.getBoundingClientRect();
            const winW = window.innerWidth, winH = window.innerHeight;
            tooltip.classList.remove('tooltip-top', 'tooltip-bottom', 'tooltip-left', 'tooltip-right');

            if (rect.left < 160) {{
                tooltip.classList.add('tooltip-right');
            }} else if (rect.right > winW - 160) {{
                tooltip.classList.add('tooltip-left');
            }} else if (rect.top < 140) {{
                tooltip.classList.add('tooltip-bottom');
            }} else if (rect.bottom > winH - 140) {{
                tooltip.classList.add('tooltip-top');
            }} else {{
                tooltip.classList.add('tooltip-top');
            }}
        }});
    }}

    buildOptionsUI();
    applyLang('tr');

    buildBtn.addEventListener('click', () => {{
        if (!selectedFile) {{
            alert('Dosya seçilmedi.');
            return;
        }}
        const args = [];
        document.querySelectorAll('#optionsContainer input[type=checkbox]:checked').forEach(cb => {{
            const flag = cb.dataset.flag;
            const card = cb.closest('.option-card');
            const inputs = card.querySelectorAll('input.option-input, select.option-input, .input-row input');
            if (inputs.length > 0) {{
                inputs.forEach(inp => {{
                    if (inp.value.trim() !== '') {{
                        args.push(flag, inp.value.trim());
                    }}
                }});
            }} else {{
                args.push(flag);
            }}
        }});

        consoleOutput.textContent = '';
        progressFill.style.width = '0%';
        statusText.textContent = LANG[currentLang].preparing;
        statusText.setAttribute('data-key', 'preparing');
        terminalVisible = false;
        consoleWrapper.style.display = 'none';
        terminalToggle.textContent = LANG[currentLang].show_terminal;
        backHomeBtn.style.display = 'none';
        browseOutputBtn.style.display = 'none';
        spinner.style.display = 'block';
        checkmark.style.display = 'none';
        showPage(3);
        pywebview.api.start_build(selectedFile, args);
    }});

    window.addLogLine = function(line) {{
        consoleOutput.textContent += line;
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }};

    window.updateProgress = function(percent, stage) {{
        progressFill.style.width = percent + '%';
        const msg = LANG[currentLang][stage] || stage;
        statusText.textContent = msg;
    }};

    window.buildFinished = function() {{
        statusText.textContent = LANG[currentLang].completed;
        statusText.setAttribute('data-key', 'completed');
        backHomeBtn.style.display = 'inline-block';
        browseOutputBtn.style.display = 'inline-block';
        spinner.style.display = 'none';
        checkmark.style.display = 'block';
    }};
</script>
</body>
</html>
"""

if __name__ == "__main__":
    multiprocessing.freeze_support()
    window = webview.create_window(
        "PY2EXE // By Fıstıkcan",
        html=html,
        js_api=api,
        width=670,
        height=580,
        resizable=True
    )
    api.set_window(window)
    webview.start(debug=False)
