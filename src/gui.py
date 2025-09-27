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

from src.server import VoiceServer
from src.client import VoiceClient

class LanVoiceGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LanVoice - Chat Vocal LAN")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Variables
        self.server = None
        self.client = None
        self.server_thread = None
        self.mode = tk.StringVar(value="client")
        self.server_ip = tk.StringVar(value="127.0.0.1")
        self.server_port = tk.StringVar(value="12345")
        self.is_recording = tk.BooleanVar(value=False)
        self.is_playing = tk.BooleanVar(value=True)
        self.vox_enabled = tk.BooleanVar(value=False)
        self.threshold_value = tk.DoubleVar(value=10.0)
        self.audio_level = tk.DoubleVar(value=0.0)
        
        logger.info("Initialisation de l'interface graphique")
        self.setup_ui()
        self.setup_styles()
        
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
        
        # Titre
        title_label = ttk.Label(main_frame, text="🎤 LanVoice", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
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
        
        # VU-mètre et contrôles audio
        audio_frame = ttk.LabelFrame(main_frame, text="Audio", padding="10")
        audio_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        audio_frame.columnconfigure(1, weight=1)
        
        # VU-mètre
        ttk.Label(audio_frame, text="Niveau:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.vu_meter = ttk.Progressbar(audio_frame, variable=self.audio_level, maximum=100)
        self.vu_meter.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.level_label = ttk.Label(audio_frame, text="0%")
        self.level_label.grid(row=0, column=2, sticky=tk.W)
        
        # Contrôles VOX
        ttk.Separator(audio_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.vox_check = ttk.Checkbutton(audio_frame, text="Mode VOX (activation vocale)", 
                                        variable=self.vox_enabled, command=self.on_vox_toggle)
        self.vox_check.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Seuil
        threshold_frame = ttk.Frame(audio_frame)
        threshold_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        threshold_frame.columnconfigure(1, weight=1)
        
        ttk.Label(threshold_frame, text="Seuil:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.threshold_scale = ttk.Scale(threshold_frame, from_=0, to=50, 
                                        variable=self.threshold_value, orient='horizontal',
                                        command=self.on_threshold_change)
        self.threshold_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.threshold_label = ttk.Label(threshold_frame, text="10%")
        self.threshold_label.grid(row=0, column=2, sticky=tk.W)
        
        # Indicateur VOX
        self.vox_indicator = ttk.Label(audio_frame, text="🔇 VOX Inactif", 
                                      foreground="gray")
        self.vox_indicator.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        # Statut
        status_frame = ttk.LabelFrame(main_frame, text="Statut", padding="10")
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Prêt à se connecter", 
                                     style='Status.TLabel')
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Journal", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
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
                logger.error(f"Impossible de démarrer le serveur sur le port {port}")
            messagebox.showerror("Erreur", "Impossible de démarrer le serveur")
                
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être un nombre")
        except Exception as e:
            self.log(f"Erreur serveur: {e}")
            messagebox.showerror("Erreur", f"Erreur démarrage serveur: {e}")
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
            else:
                messagebox.showerror("Erreur", "Impossible de se connecter au serveur")
                self.client = None
                
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit être un nombre")
        except Exception as e:
            self.log(f"Erreur connexion: {e}")
            messagebox.showerror("Erreur", f"Erreur de connexion: {e}")
    
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
        self.audio_level.set(level)
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
        self.threshold_label.config(text=f"{threshold:.0f}%")
        
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
    
    def on_closing(self):
        """Gère la fermeture de l'application"""
        try:
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