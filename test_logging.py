"""
Test du système de logging de LanVoice
"""

import sys
import os
import time

# Ajouter le dossier src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_logging_system():
    """Test complet du système de logging"""
    print("=" * 60)
    print("🧪 Test du système de logging LanVoice")
    print("=" * 60)
    
    try:
        # Initialiser le logging
        from logger import init_logging, get_logger, log_startup_complete
        
        print("1. Initialisation du système de logging...")
        logger_system = init_logging()
        
        print("2. Test des différents loggers...")
        
        # Logger principal
        main_logger = get_logger('Test')
        main_logger.info("Test du logger principal")
        main_logger.debug("Message de debug")
        main_logger.warning("Message d'avertissement")
        main_logger.error("Message d'erreur de test")
        
        # Loggers spécialisés
        server_logger = get_logger('Server')
        server_logger.info("Test du logger serveur")
        
        client_logger = get_logger('Client')
        client_logger.info("Test du logger client")
        
        gui_logger = get_logger('GUI')
        gui_logger.info("Test du logger interface")
        
        # Test avec exception
        try:
            raise ValueError("Exception de test")
        except Exception as e:
            main_logger.error("Test de logging d'exception", exc_info=True)
        
        print("3. Test des fonctionnalités avancées...")
        
        # Test logging des informations système
        system_logger = get_logger('System')
        system_logger.info("Test informations système")
        
        # Finaliser
        log_startup_complete()
        
        print(f"4. Fichier de log créé: {logger_system.log_file}")
        print("✅ Test du logging terminé avec succès!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_log_content():
    """Affiche le contenu du dernier log créé"""
    try:
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            print("❌ Aucun dossier de logs trouvé")
            return
        
        # Trouver le fichier de log le plus récent
        log_files = [f for f in os.listdir(logs_dir) if f.startswith("lanvoice_") and f.endswith(".log")]
        if not log_files:
            print("❌ Aucun fichier de log trouvé")
            return
        
        latest_log = max(log_files, key=lambda f: os.path.getctime(os.path.join(logs_dir, f)))
        log_path = os.path.join(logs_dir, latest_log)
        
        print(f"\n📄 Contenu du log: {latest_log}")
        print("=" * 60)
        
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        
        print("=" * 60)
        print(f"📊 Taille du fichier: {os.path.getsize(log_path)} bytes")
        
    except Exception as e:
        print(f"❌ Erreur lecture du log: {e}")

def main():
    """Fonction principale de test"""
    success = test_logging_system()
    
    if success:
        print("\n" + "=" * 60)
        choice = input("Voulez-vous voir le contenu du log créé ? (o/n): ").lower().strip()
        
        if choice in ['o', 'oui', 'y', 'yes']:
            show_log_content()
    
    input("\nAppuyez sur Entrée pour continuer...")
    return success

if __name__ == "__main__":
    main()