#!/usr/bin/env python3
"""
LanVoice - Gestionnaire de Configuration v2.0
Gère la sauvegarde et le chargement des paramètres utilisateur
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    """Gestionnaire de configuration pour LanVoice"""
    
    def __init__(self, config_file: str = "lanvoice_config.json"):
        """
        Initialise le gestionnaire de configuration
        
        Args:
            config_file: Nom du fichier de configuration
        """
        self.config_file = self._get_config_path(config_file)
        self.config_data = {}
        self.default_config = self._get_default_config()
        self.load_config()
    
    def _get_config_path(self, filename: str) -> Path:
        """
        Obtient le chemin du fichier de configuration
        
        Args:
            filename: Nom du fichier de configuration
            
        Returns:
            Path vers le fichier de configuration
        """
        # Utilise le répertoire de l'application ou le répertoire utilisateur
        app_dir = Path.cwd()
        if app_dir.is_dir() and os.access(app_dir, os.W_OK):
            return app_dir / filename
        else:
            # Utilise le répertoire utilisateur si le répertoire app n'est pas accessible
            user_dir = Path.home() / ".lanvoice"
            user_dir.mkdir(exist_ok=True)
            return user_dir / filename
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration par défaut
        
        Returns:
            Configuration par défaut
        """
        return {
            # Paramètres audio
            "audio_profile": "auto",  # auto, ultra_low_latency, low_latency, quality, bandwidth_saving
            "custom_sample_rate": 44100,
            "custom_buffer_size": 1024,
            "compression_enabled": True,
            "compression_level": 1,
            
            # Paramètres VOX
            "vox_enabled": False,
            "vox_threshold": -30.0,  # Seuil en dB
            "vox_delay": 500,  # ms
            "vox_hangtime": 1000,  # ms
            
            # Paramètres réseau
            "server_port": 12345,
            "connection_timeout": 10,
            "tcp_nodelay": True,
            
            # Paramètres interface
            "auto_diagnostic": True,
            "show_performance_metrics": False,
            "theme": "light",  # light, dark, auto
            "language": "fr",  # fr, en
            
            # Paramètres avancés
            "thread_priority": "high",  # high, normal, low
            "experimental_features": False,
            "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
            
            # Historique des diagnostics
            "last_diagnostic_date": None,
            "diagnostic_results": {},
            
            # Paramètres de performance
            "cpu_optimization": True,
            "memory_optimization": True,
            "network_optimization": True
        }
    
    def load_config(self) -> bool:
        """
        Charge la configuration depuis le fichier
        
        Returns:
            True si la configuration a été chargée avec succès
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge avec la configuration par défaut pour assurer la compatibilité
                self.config_data = self.default_config.copy()
                self.config_data.update(loaded_config)
                
                logging.info(f"Configuration chargée depuis {self.config_file}")
                return True
            else:
                # Utilise la configuration par défaut
                self.config_data = self.default_config.copy()
                logging.info("Configuration par défaut utilisée")
                return False
                
        except Exception as e:
            logging.warning(f"Erreur lors du chargement de la configuration: {e}")
            self.config_data = self.default_config.copy()
            return False
    
    def save_config(self) -> bool:
        """
        Sauvegarde la configuration dans le fichier
        
        Returns:
            True si la configuration a été sauvegardée avec succès
        """
        try:
            # Créer le répertoire parent si nécessaire
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Configuration sauvegardée dans {self.config_file}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtient une valeur de configuration
        
        Args:
            key: Clé de configuration
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            Valeur de configuration
        """
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> bool:
        """
        Définit une valeur de configuration
        
        Args:
            key: Clé de configuration
            value: Nouvelle valeur
            save_immediately: Sauvegarde immédiatement le fichier
            
        Returns:
            True si la valeur a été définie avec succès
        """
        try:
            old_value = self.config_data.get(key)
            self.config_data[key] = value
            
            if save_immediately:
                success = self.save_config()
                if not success:
                    # Restaure l'ancienne valeur en cas d'erreur
                    if old_value is not None:
                        self.config_data[key] = old_value
                    return False
            
            logging.debug(f"Configuration mise à jour: {key} = {value}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la définition de la configuration {key}: {e}")
            return False
    
    def update_multiple(self, updates: Dict[str, Any], save_immediately: bool = True) -> bool:
        """
        Met à jour plusieurs valeurs de configuration
        
        Args:
            updates: Dictionnaire des mises à jour
            save_immediately: Sauvegarde immédiatement le fichier
            
        Returns:
            True si toutes les valeurs ont été mises à jour avec succès
        """
        try:
            old_values = {}
            
            # Sauvegarde les anciennes valeurs
            for key in updates.keys():
                old_values[key] = self.config_data.get(key)
            
            # Applique les nouvelles valeurs
            self.config_data.update(updates)
            
            if save_immediately:
                success = self.save_config()
                if not success:
                    # Restaure les anciennes valeurs en cas d'erreur
                    for key, old_value in old_values.items():
                        if old_value is not None:
                            self.config_data[key] = old_value
                    return False
            
            logging.info(f"Configuration mise à jour: {len(updates)} paramètres modifiés")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return False
    
    def reset_to_defaults(self, save_immediately: bool = True) -> bool:
        """
        Remet la configuration aux valeurs par défaut
        
        Args:
            save_immediately: Sauvegarde immédiatement le fichier
            
        Returns:
            True si la remise à zéro a été effectuée avec succès
        """
        try:
            self.config_data = self.default_config.copy()
            
            if save_immediately:
                return self.save_config()
            
            logging.info("Configuration remise aux valeurs par défaut")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la remise à zéro de la configuration: {e}")
            return False
    
    def get_audio_profile_settings(self) -> Dict[str, Any]:
        """
        Obtient les paramètres du profil audio actuel
        
        Returns:
            Paramètres du profil audio
        """
        profile = self.get("audio_profile", "auto")
        
        # Import ici pour éviter les dépendances circulaires
        try:
            from src.audio_config import AudioConfig
            audio_config = AudioConfig()
            
            if profile == "auto":
                settings = audio_config.get_optimal_profile()
            else:
                settings = audio_config.get_profile(profile)
            
            # Ajoute les paramètres personnalisés
            if self.get("custom_sample_rate"):
                settings["sample_rate"] = self.get("custom_sample_rate")
            if self.get("custom_buffer_size"):
                settings["buffer_size"] = self.get("custom_buffer_size")
            
            return settings
            
        except ImportError:
            # Configuration par défaut si audio_config n'est pas disponible
            return {
                "sample_rate": self.get("custom_sample_rate", 44100),
                "buffer_size": self.get("custom_buffer_size", 1024),
                "format": "int16"
            }
    
    def get_vox_settings(self) -> Dict[str, Any]:
        """
        Obtient les paramètres VOX
        
        Returns:
            Paramètres VOX
        """
        return {
            "enabled": self.get("vox_enabled", False),
            "threshold": self.get("vox_threshold", -30.0),
            "delay": self.get("vox_delay", 500),
            "hangtime": self.get("vox_hangtime", 1000)
        }
    
    def get_network_settings(self) -> Dict[str, Any]:
        """
        Obtient les paramètres réseau
        
        Returns:
            Paramètres réseau
        """
        return {
            "port": self.get("server_port", 12345),
            "timeout": self.get("connection_timeout", 10),
            "tcp_nodelay": self.get("tcp_nodelay", True),
            "compression": self.get("compression_enabled", True),
            "compression_level": self.get("compression_level", 1)
        }
    
    def export_config(self, export_path: str) -> bool:
        """
        Exporte la configuration vers un fichier
        
        Args:
            export_path: Chemin d'export
            
        Returns:
            True si l'export a été effectué avec succès
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Configuration exportée vers {export_file}")
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de l'export de la configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """
        Importe la configuration depuis un fichier
        
        Args:
            import_path: Chemin d'import
            
        Returns:
            True si l'import a été effectué avec succès
        """
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                logging.error(f"Fichier d'import non trouvé: {import_file}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge avec la configuration par défaut
            new_config = self.default_config.copy()
            new_config.update(imported_config)
            
            self.config_data = new_config
            success = self.save_config()
            
            if success:
                logging.info(f"Configuration importée depuis {import_file}")
            
            return success
            
        except Exception as e:
            logging.error(f"Erreur lors de l'import de la configuration: {e}")
            return False

# Instance globale du gestionnaire de configuration
config_manager = ConfigManager()

def get_config_manager() -> ConfigManager:
    """
    Obtient l'instance globale du gestionnaire de configuration
    
    Returns:
        Instance du gestionnaire de configuration
    """
    return config_manager