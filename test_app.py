"""
Script de test pour LanVoice
Teste les fonctionnalités de base sans interface graphique
"""

import sys
import os
import time
import threading

# Ajouter le dossier src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from server import VoiceServer
from client import VoiceClient

def test_server_start_stop():
    """Test du démarrage et arrêt du serveur"""
    print("🧪 Test serveur - démarrage/arrêt...")
    
    server = VoiceServer(host="127.0.0.1", port=12346)  # Port différent pour éviter les conflits
    
    # Démarrer le serveur dans un thread
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    
    # Attendre que le serveur démarre
    time.sleep(1)
    
    if server.running:
        print("✅ Serveur démarré avec succès")
        
        # Arrêter le serveur
        server.stop()
        time.sleep(1)
        
        if not server.running:
            print("✅ Serveur arrêté avec succès")
            return True
        else:
            print("❌ Erreur: serveur non arrêté")
            return False
    else:
        print("❌ Erreur: serveur non démarré")
        return False

def test_client_connection():
    """Test de connexion du client"""
    print("🧪 Test client - connexion...")
    
    # Démarrer un serveur de test
    server = VoiceServer(host="127.0.0.1", port=12347)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)
    
    if not server.running:
        print("❌ Impossible de démarrer le serveur de test")
        return False
    
    # Tester la connexion client
    client = VoiceClient(host="127.0.0.1", port=12347)
    
    try:
        if client.connect():
            print("✅ Client connecté avec succès")
            
            # Test de déconnexion
            client.disconnect()
            time.sleep(0.5)
            
            if not client.connected:
                print("✅ Client déconnecté avec succès")
                result = True
            else:
                print("❌ Erreur: client non déconnecté")
                result = False
        else:
            print("❌ Erreur: impossible de connecter le client")
            result = False
    
    except Exception as e:
        print(f"❌ Erreur lors du test client: {e}")
        result = False
    
    finally:
        # Nettoyer
        server.stop()
        time.sleep(0.5)
    
    return result

def test_audio_devices():
    """Test de détection des périphériques audio"""
    print("🧪 Test périphériques audio...")
    
    try:
        client = VoiceClient()
        devices = client.get_audio_devices()
        
        if devices['input'] or devices['output']:
            print(f"✅ Périphériques détectés: {len(devices['input'])} entrées, {len(devices['output'])} sorties")
            return True
        else:
            print("⚠️ Aucun périphérique audio détecté")
            return True  # Ce n'est pas forcément une erreur
    
    except Exception as e:
        print(f"❌ Erreur détection audio: {e}")
        return False

def test_import_modules():
    """Test d'importation des modules"""
    print("🧪 Test importation des modules...")
    
    try:
        import pyaudio
        print("✅ PyAudio importé avec succès")
        
        import tkinter
        print("✅ Tkinter importé avec succès")
        
        from server import VoiceServer
        from client import VoiceClient
        from gui import LanVoiceGUI
        print("✅ Modules LanVoice importés avec succès")
        
        return True
    
    except Exception as e:
        print(f"❌ Erreur importation: {e}")
        return False

def main():
    """Lance tous les tests"""
    print("=" * 50)
    print("🚀 Tests LanVoice")
    print("=" * 50)
    
    tests = [
        ("Importation des modules", test_import_modules),
        ("Périphériques audio", test_audio_devices),
        ("Serveur démarrage/arrêt", test_server_start_stop),
        ("Connexion client", test_client_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'application est prête.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les dépendances.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    input("\nAppuyez sur Entrée pour continuer...")
    sys.exit(0 if success else 1)