"""
LanVoice - Application de chat vocal en réseau local
Point d'entrée principal de l'application
"""

import sys
import os

# Ajouter le dossier src au path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Initialiser le logging en premier (import après ajout du chemin)
from src.logger import init_logging, get_logger, log_startup_complete

def main():
    """Point d'entrée principal de l'application"""
    # Initialiser le système de logging
    logger_system = init_logging()
    logger = get_logger('Main')
    
    logger.info("Démarrage de l'application LanVoice")
    
    try:
        # Vérifier que les dépendances sont installées
        logger.info("Vérification des dépendances...")
        try:
            import pyaudio
            logger.info("PyAudio: OK")
            import tkinter
            logger.info("Tkinter: OK")
            import numpy
            logger.info("Numpy: OK")
        except ImportError as e:
            logger.error(f"Dépendance manquante: {e}")
            print(f"Erreur: Dépendance manquante - {e}")
            print("Veuillez installer les dépendances avec: pip install -r requirements.txt")
            sys.exit(1)
        
        logger.info("Toutes les dépendances sont disponibles")
        
        # Lancer l'interface graphique
        logger.info("Démarrage de l'interface graphique...")
        log_startup_complete()
        
        from src.gui import main as gui_main
        gui_main()
        
        logger.info("Application fermée normalement")
        
    except KeyboardInterrupt:
        logger.info("Application fermée par l'utilisateur (Ctrl+C)")
        print("\nApplication fermée par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur fatale lors du démarrage: {e}", exc_info=True)
        print(f"Erreur lors du démarrage de l'application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()