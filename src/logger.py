"""
Gestionnaire de logs pour LanVoice
Crée un nouveau fichier de log à chaque démarrage de l'application
"""

import logging
import os
import sys
from datetime import datetime

# Import conditionnel pour PyInstaller
try:
    from logging.handlers import RotatingFileHandler
    HAS_ROTATING_HANDLER = True
except ImportError:
    HAS_ROTATING_HANDLER = False

class LanVoiceLogger:
    def __init__(self, log_dir="logs", max_files=10):
        """
        Initialise le système de logging
        
        Args:
            log_dir: Dossier où stocker les logs
            max_files: Nombre maximum de fichiers de log à conserver
        """
        self.log_dir = log_dir
        self.max_files = max_files
        self.log_file = None
        
        # Créer le dossier de logs s'il n'existe pas
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Nettoyer les anciens logs
        self._cleanup_old_logs()
        
        # Créer le nouveau fichier de log
        self._create_log_file()
        
        # Configurer le logging
        self._setup_logging()
    
    def _cleanup_old_logs(self):
        """Supprime les anciens fichiers de log en gardant seulement les plus récents"""
        try:
            log_files = []
            for file in os.listdir(self.log_dir):
                if file.startswith("lanvoice_") and file.endswith(".log"):
                    file_path = os.path.join(self.log_dir, file)
                    log_files.append((file_path, os.path.getctime(file_path)))
            
            # Trier par date de création (plus récent en premier)
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # Supprimer les fichiers en excès
            for file_path, _ in log_files[self.max_files:]:
                try:
                    os.remove(file_path)
                    print(f"Ancien log supprimé: {file_path}")
                except Exception as e:
                    print(f"Erreur suppression log {file_path}: {e}")
                    
        except Exception as e:
            print(f"Erreur nettoyage logs: {e}")
    
    def _create_log_file(self):
        """Crée un nouveau fichier de log avec timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"lanvoice_{timestamp}.log")
        
        # Créer le fichier et écrire l'en-tête
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write(f"LanVoice - Session démarrée le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Plateforme: {sys.platform}\n")
                f.write(f"Arguments: {sys.argv}\n")
                f.write("="*80 + "\n\n")
        except Exception as e:
            print(f"Erreur création fichier log: {e}")
    
    def _setup_logging(self):
        """Configure le système de logging"""
        # Format détaillé pour les logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler pour fichier (compatible PyInstaller)
        try:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
        except Exception as e:
            # Fallback si problème avec le fichier de log
            print(f"Attention: Impossible de créer le fichier de log: {e}")
            file_handler = None
        
        # Handler pour console (optionnel, plus concis)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Configuration du logger root
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Supprimer les handlers existants
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Ajouter nos handlers
        if file_handler:
            root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Logger spécifique pour LanVoice
        self.logger = logging.getLogger('LanVoice')
        
        # Log de démarrage
        self.logger.info("="*50)
        self.logger.info("DÉMARRAGE DE LANVOICE")
        self.logger.info("="*50)
        self.logger.info(f"Fichier de log: {self.log_file}")
        self.logger.info(f"Niveau de log: DEBUG")
    
    def get_logger(self, name=None):
        """Retourne un logger avec le nom spécifié"""
        if name:
            return logging.getLogger(f'LanVoice.{name}')
        return self.logger
    
    def log_system_info(self):
        """Log les informations système détaillées"""
        logger = self.get_logger('System')
        
        try:
            import platform
            import psutil
            
            logger.info("=== INFORMATIONS SYSTÈME ===")
            logger.info(f"OS: {platform.system()} {platform.release()} {platform.version()}")
            logger.info(f"Architecture: {platform.architecture()}")
            logger.info(f"Processeur: {platform.processor()}")
            logger.info(f"RAM totale: {psutil.virtual_memory().total / (1024**3):.2f} GB")
            logger.info(f"RAM disponible: {psutil.virtual_memory().available / (1024**3):.2f} GB")
            
        except ImportError:
            logger.warning("psutil non installé, informations système limitées")
            import platform
            logger.info(f"OS: {platform.system()} {platform.release()}")
            logger.info(f"Architecture: {platform.architecture()}")
        
        except Exception as e:
            logger.error(f"Erreur récupération info système: {e}")
    
    def log_audio_devices(self):
        """Log les périphériques audio disponibles"""
        logger = self.get_logger('Audio')
        
        try:
            import pyaudio
            
            logger.info("=== PÉRIPHÉRIQUES AUDIO ===")
            audio = pyaudio.PyAudio()
            
            logger.info(f"Nombre de périphériques: {audio.get_device_count()}")
            
            for i in range(audio.get_device_count()):
                try:
                    device_info = audio.get_device_info_by_index(i)
                    logger.info(f"Device {i}: {device_info['name']}")
                    logger.info(f"  - Max input channels: {device_info['maxInputChannels']}")
                    logger.info(f"  - Max output channels: {device_info['maxOutputChannels']}")
                    logger.info(f"  - Default sample rate: {device_info['defaultSampleRate']}")
                except Exception as e:
                    logger.error(f"Erreur info device {i}: {e}")
            
            # Périphérique par défaut
            try:
                default_input = audio.get_default_input_device_info()
                logger.info(f"Périphérique entrée par défaut: {default_input['name']}")
            except:
                logger.warning("Pas de périphérique d'entrée par défaut")
            
            try:
                default_output = audio.get_default_output_device_info()
                logger.info(f"Périphérique sortie par défaut: {default_output['name']}")
            except:
                logger.warning("Pas de périphérique de sortie par défaut")
            
            audio.terminate()
            
        except ImportError:
            logger.error("PyAudio non disponible")
        except Exception as e:
            logger.error(f"Erreur énumération périphériques audio: {e}")
    
    def log_network_info(self):
        """Log les informations réseau"""
        logger = self.get_logger('Network')
        
        try:
            import socket
            
            logger.info("=== INFORMATIONS RÉSEAU ===")
            
            # Nom de l'hôte
            hostname = socket.gethostname()
            logger.info(f"Nom d'hôte: {hostname}")
            
            # Adresses IP
            try:
                # IP locale (méthode de connexion)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                logger.info(f"IP locale: {local_ip}")
            except:
                logger.warning("Impossible de déterminer l'IP locale")
            
            # Toutes les adresses
            try:
                addresses = socket.getaddrinfo(hostname, None)
                for addr in addresses:
                    if addr[0] == socket.AF_INET:  # IPv4 seulement
                        logger.info(f"Adresse IPv4: {addr[4][0]}")
            except Exception as e:
                logger.warning(f"Erreur énumération adresses: {e}")
                
        except Exception as e:
            logger.error(f"Erreur informations réseau: {e}")
    
    def log_startup_complete(self):
        """Log la fin de l'initialisation"""
        logger = self.get_logger('Startup')
        logger.info("="*50)
        logger.info("INITIALISATION TERMINÉE - APPLICATION PRÊTE")
        logger.info("="*50)

# Instance globale
_lanvoice_logger = None

def init_logging():
    """Initialise le système de logging (à appeler une seule fois au début)"""
    global _lanvoice_logger
    if _lanvoice_logger is None:
        _lanvoice_logger = LanVoiceLogger()
        
        # Log toutes les informations système au démarrage
        _lanvoice_logger.log_system_info()
        _lanvoice_logger.log_audio_devices()
        _lanvoice_logger.log_network_info()
    
    return _lanvoice_logger

def get_logger(name=None):
    """Récupère un logger (initialise le système si nécessaire)"""
    global _lanvoice_logger
    if _lanvoice_logger is None:
        init_logging()
    return _lanvoice_logger.get_logger(name)

def log_startup_complete():
    """Marque la fin de l'initialisation"""
    global _lanvoice_logger
    if _lanvoice_logger:
        _lanvoice_logger.log_startup_complete()