"""
Script de test pour les améliorations de gestion d'erreurs dans LanVoice
Ce script teste différents scénarios d'erreur pour vérifier que les messages sont informatifs
"""

import socket
import threading
import time
import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.server import VoiceServer
    from src.client import VoiceClient
    from src.logger import init_logging, get_logger
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

def test_verbose_errors():
    """Test des améliorations de gestion d'erreurs"""
    
    print("=" * 60)
    print("🧪 TEST DES AMÉLIORATIONS D'ERREURS LANVOICE")
    print("=" * 60)
    
    # Initialiser le logging
    logger_system = init_logging()
    logger = get_logger('Test')
    
    print("\n1️⃣ Test: Port déjà utilisé")
    print("-" * 30)
    
    try:
        # Créer un socket qui va bloquer le port
        blocking_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocking_socket.bind(('0.0.0.0', 12345))
        blocking_socket.listen(1)
        print("✅ Socket bloquant créé sur le port 12345")
        
        # Essayer de créer un serveur sur le même port
        server = VoiceServer(host="0.0.0.0", port=12345)
        try:
            server.start()
            print("❌ Le serveur aurait dû échouer!")
        except OSError as e:
            print(f"✅ Erreur capturée correctement: {type(e).__name__}")
            print(f"   Message: {e}")
            print(f"   Errno: {getattr(e, 'errno', 'N/A')}")
        
        blocking_socket.close()
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    print("\n2️⃣ Test: Port invalide")
    print("-" * 30)
    
    try:
        server = VoiceServer(host="0.0.0.0", port=99999)  # Port trop élevé
        server.start()
        print("❌ Le serveur aurait dû échouer!")
    except (OSError, ValueError) as e:
        print(f"✅ Erreur capturée correctement: {type(e).__name__}")
        print(f"   Message: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
    
    print("\n3️⃣ Test: Connexion impossible")
    print("-" * 30)
    
    try:
        client = VoiceClient(host="192.168.999.999", port=12345)  # IP invalide
        success = client.connect()
        if not success:
            print("✅ Connexion échouée comme attendu")
        else:
            print("❌ La connexion aurait dû échouer!")
    except Exception as e:
        print(f"✅ Erreur capturée: {type(e).__name__}: {e}")
    
    print("\n4️⃣ Test: Résolution DNS échouée")
    print("-" * 30)
    
    try:
        client = VoiceClient(host="serveur.inexistant.local", port=12345)
        success = client.connect()
        if not success:
            print("✅ Connexion échouée comme attendu")
    except socket.gaierror as e:
        print(f"✅ Erreur DNS capturée: {e}")
    except Exception as e:
        print(f"✅ Erreur capturée: {type(e).__name__}: {e}")
    
    print("\n5️⃣ Test: Serveur fonctionnel")
    print("-" * 30)
    
    try:
        server = VoiceServer(host="127.0.0.1", port=12346)  # Port différent
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        
        time.sleep(0.5)  # Laisser le temps au serveur de démarrer
        
        if server.running:
            print("✅ Serveur démarré avec succès sur le port 12346")
            
            # Tester la connexion client
            client = VoiceClient(host="127.0.0.1", port=12346)
            if client.connect():
                print("✅ Client connecté avec succès")
                client.disconnect()
                print("✅ Client déconnecté")
            else:
                print("❌ Échec de connexion du client")
            
            server.stop()
            print("✅ Serveur arrêté")
        else:
            print("❌ Échec du démarrage du serveur")
            
    except Exception as e:
        print(f"❌ Erreur lors du test du serveur fonctionnel: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 TESTS TERMINÉS")
    print("=" * 60)
    print("\n💡 Les erreurs détaillées sont maintenant loggées dans:")
    print(f"   📁 logs/")
    print(f"   📄 Derniers logs créés")

if __name__ == "__main__":
    test_verbose_errors()