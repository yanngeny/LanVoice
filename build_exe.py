"""
Script de build pour créer un exécutable de LanVoice avec PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_dirs():
    """Nettoie les dossiers de build précédents"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Nettoyage du dossier {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Nettoyer les fichiers .spec
    for spec_file in Path('.').glob('*.spec'):
        print(f"Suppression de {spec_file}...")
        spec_file.unlink()

def create_executable():
    """Crée l'exécutable avec PyInstaller"""
    print("Création de l'exécutable LanVoice...")
    
    # Options PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',                    # Un seul fichier exécutable
        '--windowed',                   # Interface graphique (pas de console)
        '--name=LanVoice',             # Nom de l'exécutable
        '--icon=assets/icon.ico',      # Icône (si disponible)
        '--add-data=src;src',          # Inclure le dossier src
        '--hidden-import=pyaudio',     # Import PyAudio explicitement
        '--hidden-import=numpy',       # Import numpy pour le VU-mètre
        '--hidden-import=tkinter',     # Import tkinter explicitement
        '--hidden-import=tkinter.ttk', # Import tkinter.ttk explicitement
        '--clean',                     # Nettoyer les fichiers temporaires
        'main.py'                      # Script principal
    ]
    
    # Retirer l'icône si elle n'existe pas
    if not os.path.exists('assets/icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
    
    try:
        # Exécuter PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Exécutable créé avec succès!")
        print(f"Fichier généré: dist/LanVoice.exe")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la création de l'exécutable:")
        print(f"Code de retour: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller n'est pas installé.")
        print("Installez-le avec: pip install pyinstaller")
        return False

def create_icon():
    """Crée une icône simple si elle n'existe pas"""
    icon_path = Path('assets/icon.ico')
    
    if not icon_path.exists():
        print("Création d'une icône par défaut...")
        # On ne crée pas d'icône pour simplifier
        # L'utilisateur peut ajouter sa propre icône dans assets/icon.ico
        pass

def test_dependencies():
    """Teste que toutes les dépendances sont installées"""
    print("Vérification des dépendances...")
    
    required_packages = ['pyaudio', 'pyinstaller']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installé")
        except ImportError:
            print(f"❌ {package} manquant")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstallez les packages manquants avec:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_spec_file():
    """Crée un fichier .spec personnalisé pour plus de contrôle"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=['pyaudio', 'tkinter', 'threading', 'socket', 'struct'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LanVoice',
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
)
'''
    
    with open('LanVoice.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("Fichier .spec créé")

def build_with_spec():
    """Build avec le fichier .spec"""
    try:
        result = subprocess.run(['pyinstaller', 'LanVoice.spec'], 
                              check=True, capture_output=True, text=True)
        print("✅ Build avec .spec réussi!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur build avec .spec: {e}")
        return False

def main():
    """Fonction principale"""
    print("=" * 50)
    print("🚀 Build LanVoice - Générateur d'exécutable")
    print("=" * 50)
    
    # Vérifier les dépendances
    if not test_dependencies():
        return False
    
    # Nettoyer les builds précédents
    clean_build_dirs()
    
    # Créer l'icône par défaut si nécessaire
    create_icon()
    
    # Méthode 1: Essayer avec la ligne de commande simple
    print("\n📦 Tentative de build simple...")
    if create_executable():
        print("\n🎉 Build terminé avec succès!")
        print("📁 Votre exécutable se trouve dans le dossier 'dist/'")
        print("📋 Vous pouvez maintenant distribuer LanVoice.exe")
        return True
    
    # Méthode 2: Essayer avec un fichier .spec
    print("\n📦 Tentative de build avec fichier .spec...")
    create_spec_file()
    if build_with_spec():
        print("\n🎉 Build avec .spec terminé avec succès!")
        return True
    
    print("\n❌ Impossible de créer l'exécutable")
    print("💡 Conseils de dépannage:")
    print("   - Vérifiez que PyInstaller est installé: pip install pyinstaller")
    print("   - Vérifiez que PyAudio est installé: pip install pyaudio")
    print("   - Essayez de lancer directement: pyinstaller main.py")
    
    return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✨ Build terminé! Vous pouvez maintenant utiliser dist/LanVoice.exe")
        input("Appuyez sur Entrée pour continuer...")
    else:
        print("\n💥 Échec du build")
        input("Appuyez sur Entrée pour continuer...")
    
    sys.exit(0 if success else 1)