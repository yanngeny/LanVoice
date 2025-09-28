"""
Interface graphique principale pour LanVoice
Permet de créer un serveur ou se connecter comme client
"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, scrolledtext
import threading
import time
import socket
import sys
import os
from datetime import datetime

# Utiliser le système de logging centralisé
try:
    from logger import get_logger
    logger = get_logger('GUI')
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Ajouter le dossier src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Imports compatibles avec PyInstaller
try:
    from src.server import VoiceServer
    from src.client import VoiceClient
    from src.config_manager import get_config_manager
    from src.settings_window import show_settings
except ImportError:
    # Si on est dans un exécutable PyInstaller
    from server import VoiceServer
    from client import VoiceClient
    from config_manager import get_config_manager
    from settings_window import show_settings

class LanVoiceGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LanVoice v2.0 - Chat Vocal LAN Optimisé")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # Gestionnaire de configuration
        self.config_manager = get_config_manager()
        self.settings_window = None
        
        # Variables
        self.server = None
        self.client = None
        self.server_thread = None
        self.mode = tk.StringVar(value="client")
        self.server_ip = tk.StringVar(value="127.0.0.1")
        self.server_port = tk.StringVar(value=str(self.config_manager.get("server_port", 12345)))
        self.is_recording = tk.BooleanVar(value=False)
        self.is_playing = tk.BooleanVar(value=True)
        self.vox_enabled = tk.BooleanVar(value=self.config_manager.get("vox_enabled", False))
        self.threshold_value = tk.DoubleVar(value=self.config_manager.get("vox_threshold", -30.0))
        self.audio_level = tk.DoubleVar(value=0.0)
        
        # Variables d'affichage
        self.current_profile = tk.StringVar(value=self.get_profile_display())
        self.performance_metrics = tk.BooleanVar(value=self.config_manager.get("show_performance_metrics", False))
        
        logger.info("Initialisation de l'interface graphique")
        self.setup_ui()
        self.setup_styles()
        
        # Chargement de la configuration
        self.load_config_settings()
        
        # Diagnostic automatique si activé
        if self.config_manager.get("auto_diagnostic", True):
            self.schedule_auto_diagnostic()
        
        # Gestion de la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Interface graphique initialisée")
        logger.debug(f"Fenêtre: {self.root.geometry()}, Mode: {self.mode.get()}")
    
    def setup_styles(self):
        """Configure les styles ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Style pour les boutons principaux
        style.configure('Action.TButton', 
                       font=('Arial', 10, 'bold'),
                       padding=(10, 5))
        
        # Style pour les indicateurs de statut
        style.configure('Status.TLabel',
                       font=('Arial', 9),
                       padding=(5, 2))
        
        # Style pour les titres
        style.configure('Title.TLabel',
                       font=('Arial', 12, 'bold'),
                       padding=(0, 10))
        
        # Styles pour le VU-mètre
        style.configure('Green.Horizontal.TProgressbar', background='green')
        style.configure('Yellow.Horizontal.TProgressbar', background='orange')
        style.configure('Red.Horizontal.TProgressbar', background='red')
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration de la grille
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # En-tête avec titre et bouton paramètres
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(header_frame, text="🎤 LanVoice v2.0", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Bouton paramètres avec icône engrenage
        settings_button = ttk.Button(header_frame, text="⚙️", width=4,
                                   command=self.open_settings,
                                   style='Action.TButton')
        settings_button.grid(row=0, column=2, sticky=tk.E)
        
        # Informations de profil audio
        profile_frame = ttk.Frame(header_frame)
        profile_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(profile_frame, text="📊 Profil:", font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W)
        self.profile_label = ttk.Label(profile_frame, textvariable=self.current_profile, 
                                     font=('Arial', 9, 'bold'), foreground='blue')
        self.profile_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Bouton diagnostic rapide
        diag_button = ttk.Button(profile_frame, text="🔍 Diagnostic", 
                               command=self.quick_diagnostic)
        diag_button.grid(row=0, column=2, sticky=tk.E)
        
        # Sélection du mode
        mode_frame = ttk.LabelFrame(main_frame, text="Mode", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="🖥️ Serveur (héberger)", 
                       variable=self.mode, value="server",
                       command=self.on_mode_change).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        ttk.Radiobutton(mode_frame, text="👤 Client (rejoindre)", 
                       variable=self.mode, value="client",
                       command=self.on_mode_change).grid(row=0, column=1, sticky=tk.W)
        
        # Configuration réseau
        network_frame = ttk.LabelFrame(main_frame, text="Configuration Réseau", padding="10")
        network_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        network_frame.columnconfigure(1, weight=1)
        
        ttk.Label(network_frame, text="Adresse IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.ip_entry = ttk.Entry(network_frame, textvariable=self.server_ip)
        self.ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(network_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 10))
        self.port_entry = ttk.Entry(network_frame, textvariable=self.server_port, width=10)
        self.port_entry.grid(row=0, column=3, sticky=tk.W)
        
        # Boutons de contrôle
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.connect_button = ttk.Button(control_frame, text="Se connecter", 
                                        command=self.toggle_connection, 
                                        style='Action.TButton')
        self.connect_button.grid(row=0, column=0, padx=(0, 10))
        
        self.record_button = ttk.Button(control_frame, text="🎤 Parler", 
                                       command=self.toggle_recording,
                                       state='disabled')
        self.record_button.grid(row=0, column=1, padx=(0, 10))
        
        self.play_button = ttk.Button(control_frame, text="🔊 Écouter", 
                                     command=self.toggle_playing,
                                     state='disabled')
        self.play_button.grid(row=0, column=2)
        
        # Statut
        status_frame = ttk.LabelFrame(main_frame, text="Statut", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Prêt à se connecter", 
                                     style='Status.TLabel')
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Journal", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bouton pour obtenir l'IP locale
        ttk.Button(network_frame, text="IP Locale", 
                  command=self.get_local_ip).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Initialiser l'interface
        self.on_mode_change()
        self.log("Application démarrée")
    
    def on_mode_change(self):
        """Appelé quand le mode change"""
        mode = self.mode.get()
        logger.info(f"Changement de mode: {mode}")
        
        if mode == "server":
            self.server_ip.set("0.0.0.0")
            self.ip_entry.config(state='disabled')
            self.connect_button.config(text="Démarrer serveur")
            logger.debug("Interface configurée en mode serveur")
        else:
            self.server_ip.set("127.0.0.1")
            self.ip_entry.config(state='normal')
            self.connect_button.config(text="Se connecter")
            logger.debug("Interface configurée en mode client")
    
    def get_local_ip(self):
        """Obtient l'adresse IP locale"""
        try:
            # Méthode pour obtenir l'IP locale
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            if self.mode.get() == "client":
                self.server_ip.set(local_ip)
            
            self.log(f"IP locale détectée: {local_ip}")
            messagebox.showinfo("IP Locale", f"Votre adresse IP locale est: {local_ip}")
            
        except Exception as e:
            self.log(f"Erreur détection IP: {e}")
            messagebox.showerror("Erreur", f"Impossible de détecter l'IP locale: {e}")
    
    def toggle_connection(self):
        """Active/désactive la connexion"""
        if self.mode.get() == "server":
            if self.server is None:
                self.start_server()
            else:
                self.stop_server()
        else:
            if self.client is None or not self.client.connected:
                self.connect_client()
            else:
                self.disconnect_client()
    
    def start_server(self):
        """Démarre le serveur"""
        try:
            port = int(self.server_port.get())
            
            # Validation du port
            if not (1 <= port <= 65535):
                raise ValueError(f"Le port doit être entre 1 et 65535. Port fourni: {port}")
            
            logger.info(f"Tentative de démarrage du serveur sur le port {port}")
            self.server = VoiceServer(host="0.0.0.0", port=port)
            
            # Démarrer le serveur dans un thread
            self.server_thread = threading.Thread(target=self.server.start, daemon=True)
            self.server_thread.start()
            
            # Attendre un peu pour vérifier que le serveur démarre
            time.sleep(0.1)
            
            if self.server.running:
                self.connect_button.config(text="Arrêter serveur")
                self.record_button.config(state='normal')
                self.play_button.config(state='normal')
                self.update_status("Serveur actif - En attente de connexions")
                self.log(f"Serveur démarré sur le port {port}")
                logger.info(f"Serveur démarré avec succès - Port: {port}, Thread: {self.server_thread.name}")
                
                # Démarrer la lecture automatiquement pour le serveur
                if self.client is None:
                    self.client = VoiceClient(status_callback=self.client_status_update)
                    # Configurer les callbacks pour le VU-mètre et VOX
                    self.client.level_callback = self.audio_level_update
                    self.client.vox_callback = self.vox_state_update
                    self.client.audio = __import__('pyaudio').PyAudio()
                    self.client.start_playing()
                    self.is_playing.set(True)
                    self.play_button.config(text="🔇 Couper son")
            else:
                self.server = None
                error_msg = f"Impossible de démarrer le serveur sur le port {port}"
                logger.error(error_msg)
                logger.error("Causes possibles: port déjà utilisé, permissions insuffisantes, adresse non valide")
                detailed_msg = f"Erreur lors du démarrage du serveur sur le port {port}.\n\nCauses possibles:\n• Port déjà utilisé par une autre application\n• Permissions insuffisantes\n• Adresse IP non valide\n• Pare-feu bloquant la connexion"
                messagebox.showerror("Erreur de démarrage du serveur", detailed_msg)
                
        except ValueError as e:
            error_msg = f"Le port doit être un nombre valide (1-65535). Valeur reçue: {self.server_port.get()}"
            logger.error(error_msg)
            messagebox.showerror("Erreur de port", error_msg)
        except Exception as e:
            error_msg = f"Erreur inattendue lors du démarrage du serveur: {type(e).__name__}: {str(e)}"
            self.log(f"Erreur serveur: {e}")
            logger.error(error_msg)
            logger.error(f"Port: {port}, Thread: {threading.current_thread().name}")
            detailed_msg = f"Une erreur inattendue s'est produite:\n\nType: {type(e).__name__}\nMessage: {str(e)}\n\nVérifiez les logs pour plus de détails."
            messagebox.showerror("Erreur critique du serveur", detailed_msg)
            self.server = None
    
    def stop_server(self):
        """Arrête le serveur"""
        if self.server:
            self.server.stop()
            self.server = None
        
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.connect_button.config(text="Démarrer serveur")
        self.record_button.config(state='disabled', text="🎤 Parler")
        self.play_button.config(state='disabled', text="🔊 Écouter")
        self.is_recording.set(False)
        self.is_playing.set(False)
        self.update_status("Serveur arrêté")
        self.log("Serveur arrêté")
    
    def connect_client(self):
        """Connecte le client au serveur"""
        try:
            host = self.server_ip.get()
            port = int(self.server_port.get())
            
            self.client = VoiceClient(host=host, port=port, 
                                    status_callback=self.client_status_update)
            
            # Configurer les callbacks pour le VU-mètre et VOX
            self.client.level_callback = self.audio_level_update
            self.client.vox_callback = self.vox_state_update
            
            if self.client.connect():
                self.connect_button.config(text="Se déconnecter")
                self.record_button.config(state='normal')
                self.play_button.config(state='normal')
                
                # Démarrer la lecture automatiquement
                if self.client.start_playing():
                    self.is_playing.set(True)
                    self.play_button.config(text="🔇 Couper son")
                
                self.log(f"Connecté au serveur {host}:{port}")
                logger.info(f"✅ Connexion client réussie vers {host}:{port}")
            else:
                error_msg = f"Impossible de se connecter au serveur {host}:{port}"
                logger.error(error_msg)
                logger.error("Causes possibles: serveur indisponible, port fermé, réseau inaccessible")
                detailed_msg = f"Connexion échouée vers {host}:{port}\n\nCauses possibles:\n• Serveur non démarré ou indisponible\n• Port fermé ou filtré par un pare-feu\n• Adresse IP incorrecte ou inaccessible\n• Problème réseau (LAN/WiFi)\n• Serveur saturé (trop de connexions)"
                messagebox.showerror("Erreur de connexion", detailed_msg)
                self.client = None
                
        except ValueError as e:
            error_msg = f"Le port doit être un nombre valide (1-65535). Valeur reçue: {self.server_port.get()}"
            logger.error(error_msg)
            messagebox.showerror("Erreur de port", error_msg)
        except ConnectionRefusedError as e:
            error_msg = f"Connexion refusée par {host}:{port} - Le serveur refuse les connexions"
            logger.error(error_msg)
            detailed_msg = f"Le serveur {host}:{port} refuse les connexions.\n\nCauses possibles:\n• Serveur non démarré\n• Port incorrect\n• Pare-feu bloquant les connexions"
            messagebox.showerror("Connexion refusée", detailed_msg)
        except socket.timeout as e:
            error_msg = f"Timeout de connexion vers {host}:{port}"
            logger.error(error_msg)
            messagebox.showerror("Timeout de connexion", f"Impossible de joindre le serveur {host}:{port}\n\nLe serveur met trop de temps à répondre.")
        except socket.gaierror as e:
            error_msg = f"Erreur de résolution d'adresse: {host} - {e}"
            logger.error(error_msg)
            messagebox.showerror("Adresse introuvable", f"Impossible de résoudre l'adresse: {host}\n\nVérifiez que l'adresse IP ou le nom d'hôte est correct.")
        except Exception as e:
            error_msg = f"Erreur inattendue de connexion: {type(e).__name__}: {str(e)}"
            self.log(f"Erreur connexion: {e}")
            logger.error(error_msg)
            logger.error(f"Host: {host}, Port: {port}")
            detailed_msg = f"Erreur inattendue lors de la connexion:\n\nType: {type(e).__name__}\nMessage: {str(e)}\n\nVérifiez les logs pour plus de détails."
            messagebox.showerror("Erreur critique de connexion", detailed_msg)
    
    def disconnect_client(self):
        """Déconnecte le client"""
        if self.client:
            try:
                self.client.disconnect()
            except Exception as e:
                self.log(f"Erreur lors de la déconnexion: {e}")
            finally:
                self.client = None
        
        self.connect_button.config(text="Se connecter")
        self.record_button.config(state='disabled', text="🎤 Parler")
        self.play_button.config(state='disabled', text="🔊 Écouter")
        self.is_recording.set(False)
        self.is_playing.set(False)
        self.update_status("Déconnecté")
        self.log("Déconnecté du serveur")
    
    def toggle_recording(self):
        """Active/désactive l'enregistrement"""
        if not self.client:
            return
        
        if self.is_recording.get():
            self.client.stop_recording()
            self.is_recording.set(False)
            self.record_button.config(text="🎤 Parler")
            self.log("Microphone désactivé")
        else:
            if self.client.start_recording():
                self.is_recording.set(True)
                self.record_button.config(text="🎤 Arrêter")
                self.log("Microphone activé")
            else:
                messagebox.showerror("Erreur", "Impossible d'activer le microphone")
    
    def toggle_playing(self):
        """Active/désactive la lecture"""
        if not self.client:
            return
        
        if self.is_playing.get():
            self.client.stop_playing()
            self.is_playing.set(False)
            self.play_button.config(text="🔊 Écouter")
            self.log("Haut-parleurs désactivés")
        else:
            if self.client.start_playing():
                self.is_playing.set(True)
                self.play_button.config(text="🔇 Couper son")
                self.log("Haut-parleurs activés")
            else:
                messagebox.showerror("Erreur", "Impossible d'activer les haut-parleurs")
    
    def client_status_update(self, status):
        """Callback pour les mises à jour de statut du client"""
        self.root.after(0, lambda: self.update_status(status))
    
    def audio_level_update(self, level):
        """Callback pour mettre à jour le VU-mètre"""
        self.root.after(0, lambda: self.update_vu_meter(level))
    
    def vox_state_update(self, active):
        """Callback pour mettre à jour l'indicateur VOX"""
        self.root.after(0, lambda: self.update_vox_indicator(active))
    
    def update_status(self, status):
        """Met à jour le label de statut"""
        self.status_label.config(text=status)
    
    def update_vu_meter(self, level):
        """Met à jour le VU-mètre"""
        # Convertir dB vers pourcentage pour l'affichage de la barre
        display_level = max(0, min(100, (level + 60) * 100 / 60))  # -60dB à 0dB -> 0 à 100%
        self.audio_level.set(display_level)
        self.level_label.config(text=f"{level:.0f}%") 
        
        # Changer la couleur selon le niveau
        if level > 80:
            self.vu_meter.config(style='Red.Horizontal.TProgressbar')
        elif level > 50:
            self.vu_meter.config(style='Yellow.Horizontal.TProgressbar')
        else:
            self.vu_meter.config(style='Green.Horizontal.TProgressbar')
    
    def update_vox_indicator(self, active):
        """Met à jour l'indicateur VOX"""
        if active:
            self.vox_indicator.config(text="🔊 VOX Actif", foreground="green")
        else:
            self.vox_indicator.config(text="🔇 VOX Inactif", foreground="gray")
    
    def on_vox_toggle(self):
        """Gestionnaire pour l'activation/désactivation du VOX"""
        if self.client:
            self.client.set_vox_enabled(self.vox_enabled.get())
            if self.vox_enabled.get():
                self.log("Mode VOX activé")
                # Désactiver le bouton manuel de micro
                self.record_button.config(state='disabled')
            else:
                self.log("Mode VOX désactivé")
                # Réactiver le bouton manuel de micro
                if self.client.connected:
                    self.record_button.config(state='normal')
    
    def on_threshold_change(self, value):
        """Gestionnaire pour le changement de seuil"""
        threshold = float(value)
        self.threshold_label.config(text=f"{threshold:.0f} dB")
        
        if self.client:
            self.client.set_threshold(threshold)
    
    def log(self, message):
        """Ajoute un message au journal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        # Log aussi dans le système centralisé
        logger.info(f"UI: {message}")
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def get_profile_display(self):
        """Obtient l'affichage du profil audio actuel"""
        profile = self.config_manager.get("audio_profile", "auto")
        profile_names = {
            "auto": "🤖 Auto",
            "ultra_low_latency": "⚡ Ultra Low (~2.9ms)",
            "low_latency": "🚀 Low (~5.8ms)",
            "quality": "🎵 Quality (~11.6ms)",
            "bandwidth_saving": "💾 Bandwidth (~23.2ms)"
        }
        return profile_names.get(profile, "🤖 Auto")
    
    def load_config_settings(self):
        """Charge les paramètres depuis la configuration"""
        try:
            # Met à jour les variables depuis la configuration
            self.server_port.set(str(self.config_manager.get("server_port", 12345)))
            self.vox_enabled.set(self.config_manager.get("vox_enabled", False))
            self.threshold_value.set(self.config_manager.get("vox_threshold", -30.0))
            
            # Met à jour l'affichage du profil
            self.current_profile.set(self.get_profile_display())
            
            logger.info("Paramètres chargés depuis la configuration")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            self.log(f"⚠️ Erreur configuration: {e}")
    
    def save_current_settings(self):
        """Sauvegarde les paramètres actuels"""
        try:
            updates = {
                "server_port": int(self.server_port.get()),
                "vox_enabled": self.vox_enabled.get(),
                "vox_threshold": self.threshold_value.get()
            }
            
            self.config_manager.update_multiple(updates, save_immediately=True)
            logger.info("Paramètres sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
    
    def open_settings(self):
        """Ouvre la fenêtre des paramètres avancés"""
        try:
            # Sauvegarde les paramètres actuels avant d'ouvrir
            self.save_current_settings()
            
            # Ouvre la fenêtre des paramètres
            self.settings_window = show_settings(self.root, self.config_manager)
            
            # Programme une vérification périodique pour les changements
            self.check_config_changes()
            
            self.log("⚙️ Paramètres avancés ouverts")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture des paramètres: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir les paramètres: {e}")
    
    def check_config_changes(self):
        """Vérifie les changements de configuration et met à jour l'interface"""
        try:
            # Met à jour l'affichage du profil
            new_profile = self.get_profile_display()
            if new_profile != self.current_profile.get():
                self.current_profile.set(new_profile)
                self.log(f"📊 Profil mis à jour: {new_profile}")
            
            # Met à jour les autres paramètres si nécessaire
            new_port = str(self.config_manager.get("server_port", 12345))
            if new_port != self.server_port.get():
                self.server_port.set(new_port)
            
            new_vox = self.config_manager.get("vox_enabled", False)
            if new_vox != self.vox_enabled.get():
                self.vox_enabled.set(new_vox)
            
            new_threshold = self.config_manager.get("vox_threshold", -30.0)
            if abs(new_threshold - self.threshold_value.get()) > 0.1:
                self.threshold_value.set(new_threshold)
            
            # Reprogramme la vérification si la fenêtre des paramètres est encore ouverte
            if (self.settings_window and 
                hasattr(self.settings_window, 'window') and 
                self.settings_window.window and 
                self.settings_window.window.winfo_exists()):
                self.root.after(1000, self.check_config_changes)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des changements: {e}")
    
    def quick_diagnostic(self):
        """Lance un diagnostic rapide intégré"""
        try:
            self.log("🔍 Diagnostic rapide en cours...")
            
            def run_integrated_diagnostic():
                try:
                    import pyaudio
                    import psutil
                    
                    # Test audio détaillé
                    p = pyaudio.PyAudio()
                    device_count = p.get_device_count()
                    
                    input_devices = 0
                    output_devices = 0
                    for i in range(device_count):
                        info = p.get_device_info_by_index(i)
                        if info['maxInputChannels'] > 0:
                            input_devices += 1
                        if info['maxOutputChannels'] > 0:
                            output_devices += 1
                    
                    p.terminate()
                    
                    # Test système
                    cpu_percent = psutil.cpu_percent(interval=0.5)
                    ram_percent = psutil.virtual_memory().percent
                    
                    # Diagnostic complet avec détails
                    import platform
                    import socket
                    
                    # Informations système détaillées
                    system_info = platform.system()
                    cpu_count = psutil.cpu_count()
                    ram_total = psutil.virtual_memory().total / (1024**3)  # GB
                    ram_available = psutil.virtual_memory().available / (1024**3)  # GB
                    
                    # Test réseau local
                    try:
                        hostname = socket.gethostname()
                        local_ip = socket.gethostbyname(hostname)
                    except:
                        hostname = "Inconnu"
                        local_ip = "127.0.0.1"
                    
                    # Évaluation performances
                    if cpu_percent < 20 and ram_percent < 50:
                        perf_status = "🏆 EXCELLENTES"
                        recommended_profile = "⚡ Ultra Low Latency (~2.9ms)"
                        perf_color = "🟢"
                    elif cpu_percent < 40 and ram_percent < 70:
                        perf_status = "👍 BONNES"
                        recommended_profile = "🚀 Low Latency (~5.8ms)"
                        perf_color = "🟡"
                    else:
                        perf_status = "⚠️ LIMITÉES"
                        recommended_profile = "🎵 Quality (~23ms)"
                        perf_color = "🔴"
                    
                    # Messages du rapport complet
                    messages = [
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "📋 RAPPORT DE DIAGNOSTIC LANVOICE COMPLET",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "",
                        "�️ INFORMATIONS SYSTÈME:",
                        f"   OS: {system_info}",
                        f"   Hostname: {hostname}",
                        f"   IP locale: {local_ip}",
                        f"   CPU: {cpu_count} coeurs - Utilisation: {cpu_percent:.1f}%",
                        f"   RAM: {ram_available:.1f}GB libre / {ram_total:.1f}GB total ({ram_percent:.1f}%)",
                        "",
                        "🎵 PÉRIPHÉRIQUES AUDIO:",
                        f"   Périphériques totaux: {device_count}",
                        f"   🎤 Entrées (microphones): {input_devices}",
                        f"   🔊 Sorties (haut-parleurs): {output_devices}",
                        "",
                        "⚡ ÉVALUATION PERFORMANCES:",
                        f"   Statut global: {perf_status}",
                        f"   {perf_color} CPU Load: {'Faible' if cpu_percent < 30 else 'Modérée' if cpu_percent < 60 else 'Élevée'}",
                        f"   {perf_color} RAM Usage: {'Faible' if ram_percent < 50 else 'Modérée' if ram_percent < 75 else 'Élevée'}",
                        "",
                        "🎯 RECOMMANDATIONS:",
                        f"   Profil optimal: {recommended_profile}",
                        f"   Latence estimée: {'< 5ms' if cpu_percent < 20 else '5-15ms' if cpu_percent < 40 else '> 15ms'}",
                        f"   Qualité recommandée: {'Maximum' if cpu_percent < 30 else 'Élevée' if cpu_percent < 60 else 'Standard'}",
                        "",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                        "✅ Diagnostic terminé - Système prêt pour LanVoice",
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                    ]
                    
                    # Envoyer tous les messages via after() avec un délai plus court
                    for i, message in enumerate(messages):
                        self.root.after(i * 50, lambda msg=message: self.log(msg))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"⚠️ Erreur diagnostic: {str(e)}"))
            
            # Lance le diagnostic dans un thread séparé
            threading.Thread(target=run_integrated_diagnostic, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement du diagnostic: {e}")
            self.log(f"⚠️ Erreur diagnostic: {e}")
    
    def schedule_auto_diagnostic(self):
        """Programme un diagnostic automatique au démarrage"""
        try:
            # Lance le diagnostic automatique après 2 secondes
            self.root.after(2000, self.auto_diagnostic)
        except Exception as e:
            logger.error(f"Erreur lors de la programmation du diagnostic: {e}")
    
    def auto_diagnostic(self):
        """Exécute un diagnostic automatique au démarrage"""
        try:
            self.log("🤖 Diagnostic automatique...")
            
            # Version simplifiée du diagnostic pour le démarrage
            def simple_diagnostic():
                try:
                    import pyaudio
                    import psutil
                    
                    # Vérification rapide PyAudio
                    p = pyaudio.PyAudio()
                    device_count = p.get_device_count()
                    p.terminate()
                    
                    # Vérification ressources système
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    ram_percent = psutil.virtual_memory().percent
                    
                    def update_result():
                        if device_count > 0:
                            self.log(f"✅ Système prêt: {device_count} périph. audio, CPU: {cpu_percent:.0f}%, RAM: {ram_percent:.0f}%")
                            
                            # Recommandation automatique de profil
                            if cpu_percent < 30 and ram_percent < 50:
                                recommended = "⚡ Ultra Low Latency recommandé"
                            elif cpu_percent < 60:
                                recommended = "🚀 Low Latency recommandé"
                            else:
                                recommended = "🎵 Quality recommandé"
                            
                            self.log(f"📊 {recommended}")
                        else:
                            self.log("⚠️ Aucun périphérique audio détecté")
                    
                    self.root.after(0, update_result)
                    
                except Exception as e:
                    def show_diag_error():
                        self.log(f"⚠️ Diagnostic limité: {str(e)[:30]}...")
                    self.root.after(0, show_diag_error)
            
            threading.Thread(target=simple_diagnostic, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Erreur diagnostic automatique: {e}")
    
    def on_closing(self):
        """Gère la fermeture de l'application"""
        try:
            # Sauvegarde les paramètres actuels
            self.save_current_settings()
            
            # Arrêter le serveur si actif
            if self.server:
                self.server.stop()
                self.server = None
            
            # Déconnecter le client si connecté
            if self.client:
                self.client.disconnect()
                self.client = None
            
            # Attendre un peu pour que les threads se terminent proprement
            time.sleep(0.5)
            
        except Exception as e:
            self.log(f"Erreur lors de la fermeture: {e}")
        finally:
            # Fermer l'application
            self.root.destroy()
    
    def run(self):
        """Lance l'application"""
        self.root.mainloop()

def main():
    """Point d'entrée principal"""
    try:
        app = LanVoiceGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Erreur Fatale", f"Erreur lors du démarrage: {e}")

if __name__ == "__main__":
    main()