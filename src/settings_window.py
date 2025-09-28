#!/usr/bin/env python3
"""
LanVoice - Interface des Paramètres Avancés v2.0
Fenêtre de configuration avec contrôles audio, VOX et diagnostic
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

class SettingsWindow:
    """Fenêtre des paramètres avancés"""
    
    def __init__(self, parent, config_manager):
        """
        Initialise la fenêtre des paramètres
        
        Args:
            parent: Fenêtre parent
            config_manager: Gestionnaire de configuration
        """
        self.parent = parent
        self.config_manager = config_manager
        self.window = None
        self.diagnostic_window = None
        self.vars = {}
        
        # Profils audio disponibles
        self.audio_profiles = {
            "auto": "🤖 Détection Automatique",
            "ultra_low_latency": "⚡ Ultra Low Latency (~2.9ms)",
            "low_latency": "🚀 Low Latency (~5.8ms)", 
            "quality": "🎵 Quality (~11.6ms)",
            "bandwidth_saving": "💾 Bandwidth Saving (~23.2ms)"
        }
    
    def show(self):
        """Affiche la fenêtre des paramètres"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ Paramètres Avancés - LanVoice v2.0")
        self.window.geometry("800x700")
        self.window.resizable(True, True)
        
        # Icône de la fenêtre
        try:
            self.window.iconbitmap("icon.ico")
        except:
            pass
        
        # Configuration de la grille
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Création du notebook pour les onglets
        self.notebook = ttk.Notebook(self.window)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Onglets
        self.create_audio_tab()
        self.create_vox_tab()
        self.create_network_tab()
        self.create_diagnostic_tab()
        self.create_advanced_tab()
        
        # Boutons en bas
        self.create_buttons()
        
        # Charge les valeurs actuelles
        self.load_current_values()
        
        # Centre la fenêtre
        self.center_window()
    
    def create_audio_tab(self):
        """Crée l'onglet des paramètres audio"""
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="🎵 Audio")
        
        # Configuration de la grille
        audio_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Titre
        title_label = ttk.Label(audio_frame, text="Paramètres Audio", font=("Arial", 12, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(10, 20), sticky="w")
        row += 1
        
        # Profil audio
        ttk.Label(audio_frame, text="Profil Audio:").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['audio_profile'] = tk.StringVar()
        profile_combo = ttk.Combobox(audio_frame, textvariable=self.vars['audio_profile'], 
                                   values=list(self.audio_profiles.values()), 
                                   state="readonly", width=40)
        profile_combo.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=5)
        profile_combo.bind('<<ComboboxSelected>>', self.on_profile_change)
        row += 1
        
        # Séparateur
        separator1 = ttk.Separator(audio_frame, orient="horizontal")
        separator1.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=15)
        row += 1
        
        # Paramètres personnalisés
        custom_label = ttk.Label(audio_frame, text="Paramètres Personnalisés", font=("Arial", 10, "bold"))
        custom_label.grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w", padx=10)
        row += 1
        
        # Fréquence d'échantillonnage
        ttk.Label(audio_frame, text="Fréquence d'échantillonnage (Hz):").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['sample_rate'] = tk.IntVar()
        sample_rate_frame = ttk.Frame(audio_frame)
        sample_rate_frame.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=5)
        sample_rate_frame.columnconfigure(0, weight=1)
        
        sample_rate_scale = ttk.Scale(sample_rate_frame, from_=8000, to=48000, 
                                    variable=self.vars['sample_rate'], orient="horizontal")
        sample_rate_scale.grid(row=0, column=0, sticky="ew")
        sample_rate_label = ttk.Label(sample_rate_frame, textvariable=self.vars['sample_rate'])
        sample_rate_label.grid(row=0, column=1, padx=(10, 0))
        
        # Presets pour sample rate
        preset_frame = ttk.Frame(sample_rate_frame)
        preset_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(preset_frame, text="8kHz", width=6, 
                  command=lambda: self.vars['sample_rate'].set(8000)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="22kHz", width=6,
                  command=lambda: self.vars['sample_rate'].set(22050)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="44kHz", width=6,
                  command=lambda: self.vars['sample_rate'].set(44100)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="48kHz", width=6,
                  command=lambda: self.vars['sample_rate'].set(48000)).pack(side="left", padx=2)
        row += 1
        
        # Taille du buffer
        ttk.Label(audio_frame, text="Taille du buffer (échantillons):").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['buffer_size'] = tk.IntVar()
        buffer_frame = ttk.Frame(audio_frame)
        buffer_frame.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=5)
        buffer_frame.columnconfigure(0, weight=1)
        
        buffer_scale = ttk.Scale(buffer_frame, from_=128, to=8192, 
                               variable=self.vars['buffer_size'], orient="horizontal")
        buffer_scale.grid(row=0, column=0, sticky="ew")
        buffer_label = ttk.Label(buffer_frame, textvariable=self.vars['buffer_size'])
        buffer_label.grid(row=0, column=1, padx=(10, 0))
        
        # Presets pour buffer size
        buffer_preset_frame = ttk.Frame(buffer_frame)
        buffer_preset_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(buffer_preset_frame, text="256", width=6,
                  command=lambda: self.vars['buffer_size'].set(256)).pack(side="left", padx=2)
        ttk.Button(buffer_preset_frame, text="512", width=6,
                  command=lambda: self.vars['buffer_size'].set(512)).pack(side="left", padx=2)
        ttk.Button(buffer_preset_frame, text="1024", width=6,
                  command=lambda: self.vars['buffer_size'].set(1024)).pack(side="left", padx=2)
        ttk.Button(buffer_preset_frame, text="2048", width=6,
                  command=lambda: self.vars['buffer_size'].set(2048)).pack(side="left", padx=2)
        row += 1
        
        # Séparateur
        separator2 = ttk.Separator(audio_frame, orient="horizontal")
        separator2.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=15)
        row += 1
        
        # Compression
        compression_label = ttk.Label(audio_frame, text="Compression Audio", font=("Arial", 10, "bold"))
        compression_label.grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w", padx=10)
        row += 1
        
        self.vars['compression_enabled'] = tk.BooleanVar()
        compression_check = ttk.Checkbutton(audio_frame, text="Activer la compression audio", 
                                         variable=self.vars['compression_enabled'])
        compression_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1
        
        # Niveau de compression
        ttk.Label(audio_frame, text="Niveau de compression:").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['compression_level'] = tk.IntVar()
        compression_scale = ttk.Scale(audio_frame, from_=1, to=9, 
                                    variable=self.vars['compression_level'], orient="horizontal")
        compression_scale.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=5)
        row += 1
        
        # Info compression
        info_frame = ttk.Frame(audio_frame)
        info_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        info_text = "💡 Niveau 1: Rapide, faible compression | Niveau 9: Lent, compression maximale"
        ttk.Label(info_frame, text=info_text, foreground="gray", font=("Arial", 8)).pack()
    
    def create_vox_tab(self):
        """Crée l'onglet des paramètres VOX"""
        vox_frame = ttk.Frame(self.notebook)
        self.notebook.add(vox_frame, text="🎤 VOX")
        
        vox_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Titre
        title_label = ttk.Label(vox_frame, text="Voice Activated Transmission (VOX)", font=("Arial", 12, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(10, 20), sticky="w")
        row += 1
        
        # Activation VOX
        self.vars['vox_enabled'] = tk.BooleanVar()
        vox_check = ttk.Checkbutton(vox_frame, text="Activer VOX (transmission automatique)", 
                                  variable=self.vars['vox_enabled'],
                                  command=self.on_vox_toggle)
        vox_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=10)
        row += 1
        
        # Frame pour les paramètres VOX
        self.vox_params_frame = ttk.LabelFrame(vox_frame, text="Paramètres VOX", padding=10)
        self.vox_params_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.vox_params_frame.columnconfigure(1, weight=1)
        row += 1
        
        vox_row = 0
        
        # Seuil VOX
        ttk.Label(self.vox_params_frame, text="Seuil de déclenchement (dB):").grid(row=vox_row, column=0, sticky="w", pady=5)
        self.vars['vox_threshold'] = tk.DoubleVar()
        threshold_frame = ttk.Frame(self.vox_params_frame)
        threshold_frame.grid(row=vox_row, column=1, sticky="ew", pady=5)
        threshold_frame.columnconfigure(0, weight=1)
        
        threshold_scale = ttk.Scale(threshold_frame, from_=-60.0, to=-10.0, 
                                  variable=self.vars['vox_threshold'], orient="horizontal")
        threshold_scale.grid(row=0, column=0, sticky="ew")
        self.threshold_label = ttk.Label(threshold_frame, text="-30 dB")
        self.threshold_label.grid(row=0, column=1, padx=(10, 0))
        
        # Mise à jour de l'affichage du seuil
        def update_threshold_display(*args):
            value = self.vars['vox_threshold'].get()
            self.threshold_label.config(text=f"{value:.0f} dB")
        self.vars['vox_threshold'].trace('w', update_threshold_display)
        vox_row += 1
        
        # Délai d'activation
        ttk.Label(self.vox_params_frame, text="Délai d'activation (ms):").grid(row=vox_row, column=0, sticky="w", pady=5)
        self.vars['vox_delay'] = tk.IntVar()
        delay_scale = ttk.Scale(self.vox_params_frame, from_=0, to=2000, 
                              variable=self.vars['vox_delay'], orient="horizontal")
        delay_scale.grid(row=vox_row, column=1, sticky="ew", pady=5)
        vox_row += 1
        
        # Temps de maintien
        ttk.Label(self.vox_params_frame, text="Temps de maintien (ms):").grid(row=vox_row, column=0, sticky="w", pady=5)
        self.vars['vox_hangtime'] = tk.IntVar()
        hangtime_scale = ttk.Scale(self.vox_params_frame, from_=100, to=5000, 
                                 variable=self.vars['vox_hangtime'], orient="horizontal")
        hangtime_scale.grid(row=vox_row, column=1, sticky="ew", pady=5)
        vox_row += 1
        
        # Indicateur de niveau audio
        level_frame = ttk.LabelFrame(vox_frame, text="Niveau Audio en Temps Réel", padding=10)
        level_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        level_frame.columnconfigure(0, weight=1)
        
        self.audio_level_var = tk.DoubleVar()
        self.audio_level_bar = ttk.Progressbar(level_frame, variable=self.audio_level_var, 
                                             maximum=0.1, mode='determinate')
        self.audio_level_bar.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.level_label = ttk.Label(level_frame, text="Niveau: 0.000")
        self.level_label.grid(row=1, column=0, pady=5)
        
        # Bouton de test VOX
        test_button = ttk.Button(level_frame, text="🎤 Test VOX en Temps Réel", 
                               command=self.start_vox_test)
        test_button.grid(row=2, column=0, pady=10)
        
        # Instructions
        info_text = ("💡 Le VOX active automatiquement la transmission quand le niveau audio "
                    "dépasse le seuil défini. Ajustez le seuil selon votre environnement.")
        info_label = ttk.Label(vox_frame, text=info_text, wraplength=750, 
                             foreground="gray", font=("Arial", 9))
        info_label.grid(row=row+1, column=0, columnspan=2, padx=10, pady=10, sticky="w")
    
    def create_network_tab(self):
        """Crée l'onglet des paramètres réseau"""
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="🌐 Réseau")
        
        network_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Titre
        title_label = ttk.Label(network_frame, text="Paramètres Réseau", font=("Arial", 12, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(10, 20), sticky="w")
        row += 1
        
        # Port serveur
        ttk.Label(network_frame, text="Port serveur:").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['server_port'] = tk.IntVar()
        port_spinbox = ttk.Spinbox(network_frame, from_=1024, to=65535, 
                                 textvariable=self.vars['server_port'], width=10)
        port_spinbox.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 1
        
        # Timeout de connexion
        ttk.Label(network_frame, text="Timeout de connexion (s):").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['connection_timeout'] = tk.IntVar()
        timeout_scale = ttk.Scale(network_frame, from_=5, to=60, 
                                variable=self.vars['connection_timeout'], orient="horizontal")
        timeout_scale.grid(row=row, column=1, sticky="ew", padx=(5, 10), pady=5)
        row += 1
        
        # TCP_NODELAY
        self.vars['tcp_nodelay'] = tk.BooleanVar()
        tcp_check = ttk.Checkbutton(network_frame, text="Activer TCP_NODELAY (réduit la latence)", 
                                  variable=self.vars['tcp_nodelay'])
        tcp_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1
        
        # Optimisations réseau
        ttk.Label(network_frame, text="Optimisations Réseau", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(20, 10), sticky="w", padx=10)
        row += 1
        
        self.vars['network_optimization'] = tk.BooleanVar()
        network_opt_check = ttk.Checkbutton(network_frame, text="Optimisations réseau automatiques", 
                                          variable=self.vars['network_optimization'])
        network_opt_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1
        
        # Test de connectivité
        test_frame = ttk.LabelFrame(network_frame, text="Test de Connectivité", padding=10)
        test_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        test_frame.columnconfigure(0, weight=1)
        
        ttk.Button(test_frame, text="🔍 Tester la Connectivité Réseau", 
                  command=self.test_network).pack(pady=10)
        
        self.network_status_label = ttk.Label(test_frame, text="Cliquez pour tester la connectivité", 
                                            foreground="gray")
        self.network_status_label.pack()
    
    def create_diagnostic_tab(self):
        """Crée l'onglet de diagnostic"""
        diagnostic_frame = ttk.Frame(self.notebook)
        self.notebook.add(diagnostic_frame, text="🔍 Diagnostic")
        
        diagnostic_frame.columnconfigure(0, weight=1)
        diagnostic_frame.rowconfigure(1, weight=1)
        
        # Titre et description
        title_label = ttk.Label(diagnostic_frame, text="Diagnostic Système", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, pady=(10, 5), sticky="w")
        
        desc_label = ttk.Label(diagnostic_frame, 
                             text="Analysez votre système pour détecter et résoudre les problèmes audio/réseau",
                             foreground="gray")
        desc_label.grid(row=0, column=0, pady=(0, 20), sticky="w")
        
        # Zone de résultats
        self.diagnostic_text = scrolledtext.ScrolledText(diagnostic_frame, height=25, wrap=tk.WORD)
        self.diagnostic_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Boutons de diagnostic
        button_frame = ttk.Frame(diagnostic_frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text="🚀 Lancer Diagnostic Complet", 
                  command=self.run_full_diagnostic).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="🎵 Test Audio Rapide", 
                  command=self.run_audio_test).grid(row=0, column=1, padx=10)
        
        ttk.Button(button_frame, text="📋 Sauvegarder Rapport", 
                  command=self.save_diagnostic_report).grid(row=0, column=2, padx=(10, 0))
        
        # Détection automatique
        auto_frame = ttk.LabelFrame(diagnostic_frame, text="Détection Automatique", padding=10)
        auto_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(10, 0))
        auto_frame.columnconfigure(1, weight=1)
        
        self.vars['auto_diagnostic'] = tk.BooleanVar()
        auto_check = ttk.Checkbutton(auto_frame, text="Diagnostic automatique au démarrage", 
                                   variable=self.vars['auto_diagnostic'])
        auto_check.grid(row=0, column=0, sticky="w")
        
        ttk.Button(auto_frame, text="⚙️ Configuration Automatique", 
                  command=self.auto_configure).grid(row=0, column=1, sticky="e")
    
    def create_advanced_tab(self):
        """Crée l'onglet des paramètres avancés"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="⚡ Avancé")
        
        advanced_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Titre
        title_label = ttk.Label(advanced_frame, text="Paramètres Avancés", font=("Arial", 12, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(10, 20), sticky="w")
        row += 1
        
        # Priorité des threads
        ttk.Label(advanced_frame, text="Priorité des threads audio:").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['thread_priority'] = tk.StringVar()
        priority_combo = ttk.Combobox(advanced_frame, textvariable=self.vars['thread_priority'], 
                                    values=["high", "normal", "low"], state="readonly")
        priority_combo.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 1
        
        # Optimisations
        optimizations_frame = ttk.LabelFrame(advanced_frame, text="Optimisations Système", padding=10)
        optimizations_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        optimizations_frame.columnconfigure(0, weight=1)
        
        self.vars['cpu_optimization'] = tk.BooleanVar()
        ttk.Checkbutton(optimizations_frame, text="Optimisations CPU", 
                       variable=self.vars['cpu_optimization']).pack(anchor="w", pady=2)
        
        self.vars['memory_optimization'] = tk.BooleanVar()
        ttk.Checkbutton(optimizations_frame, text="Optimisations mémoire", 
                       variable=self.vars['memory_optimization']).pack(anchor="w", pady=2)
        
        self.vars['experimental_features'] = tk.BooleanVar()
        experimental_check = ttk.Checkbutton(optimizations_frame, text="⚠️ Fonctionnalités expérimentales", 
                                           variable=self.vars['experimental_features'])
        experimental_check.pack(anchor="w", pady=2)
        row += 1
        
        # Niveau de log
        ttk.Label(advanced_frame, text="Niveau de logging:").grid(row=row, column=0, sticky="w", padx=(10, 5), pady=5)
        self.vars['log_level'] = tk.StringVar()
        log_combo = ttk.Combobox(advanced_frame, textvariable=self.vars['log_level'], 
                               values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly")
        log_combo.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 1
        
        # Interface
        interface_frame = ttk.LabelFrame(advanced_frame, text="Interface", padding=10)
        interface_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        interface_frame.columnconfigure(1, weight=1)
        
        ttk.Label(interface_frame, text="Thème:").grid(row=0, column=0, sticky="w", pady=5)
        self.vars['theme'] = tk.StringVar()
        theme_combo = ttk.Combobox(interface_frame, textvariable=self.vars['theme'], 
                                 values=["light", "dark", "auto"], state="readonly")
        theme_combo.grid(row=0, column=1, sticky="w", pady=5)
        
        self.vars['show_performance_metrics'] = tk.BooleanVar()
        ttk.Checkbutton(interface_frame, text="Afficher métriques de performance", 
                       variable=self.vars['show_performance_metrics']).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        row += 1
        
        # Configuration
        config_frame = ttk.LabelFrame(advanced_frame, text="Configuration", padding=10)
        config_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Button(config_frame, text="📁 Exporter Configuration", 
                  command=self.export_config).grid(row=0, column=0, padx=(0, 5), pady=5)
        ttk.Button(config_frame, text="📂 Importer Configuration", 
                  command=self.import_config).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="🔄 Restaurer Défauts", 
                  command=self.reset_to_defaults).grid(row=0, column=2, padx=(5, 0), pady=5)
    
    def create_buttons(self):
        """Crée les boutons de contrôle"""
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        button_frame.columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text="💾 Sauvegarder", 
                  command=self.save_settings).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="✅ Appliquer", 
                  command=self.apply_settings).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="❌ Annuler", 
                  command=self.cancel).grid(row=0, column=2, padx=(10, 0))
    
    def load_current_values(self):
        """Charge les valeurs actuelles depuis la configuration"""
        try:
            # Profil audio
            current_profile = self.config_manager.get("audio_profile", "auto")
            profile_display = self.audio_profiles.get(current_profile, self.audio_profiles["auto"])
            self.vars['audio_profile'].set(profile_display)
            
            # Paramètres audio
            self.vars['sample_rate'].set(self.config_manager.get("custom_sample_rate", 44100))
            self.vars['buffer_size'].set(self.config_manager.get("custom_buffer_size", 1024))
            self.vars['compression_enabled'].set(self.config_manager.get("compression_enabled", True))
            self.vars['compression_level'].set(self.config_manager.get("compression_level", 1))
            
            # VOX
            self.vars['vox_enabled'].set(self.config_manager.get("vox_enabled", False))
            self.vars['vox_threshold'].set(self.config_manager.get("vox_threshold", -30.0))
            self.vars['vox_delay'].set(self.config_manager.get("vox_delay", 500))
            self.vars['vox_hangtime'].set(self.config_manager.get("vox_hangtime", 1000))
            
            # Réseau
            self.vars['server_port'].set(self.config_manager.get("server_port", 12345))
            self.vars['connection_timeout'].set(self.config_manager.get("connection_timeout", 10))
            self.vars['tcp_nodelay'].set(self.config_manager.get("tcp_nodelay", True))
            self.vars['network_optimization'].set(self.config_manager.get("network_optimization", True))
            
            # Diagnostic
            self.vars['auto_diagnostic'].set(self.config_manager.get("auto_diagnostic", True))
            
            # Avancé
            self.vars['thread_priority'].set(self.config_manager.get("thread_priority", "high"))
            self.vars['cpu_optimization'].set(self.config_manager.get("cpu_optimization", True))
            self.vars['memory_optimization'].set(self.config_manager.get("memory_optimization", True))
            self.vars['experimental_features'].set(self.config_manager.get("experimental_features", False))
            self.vars['log_level'].set(self.config_manager.get("log_level", "INFO"))
            self.vars['theme'].set(self.config_manager.get("theme", "light"))
            self.vars['show_performance_metrics'].set(self.config_manager.get("show_performance_metrics", False))
            
            # Met à jour l'état VOX
            self.on_vox_toggle()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des paramètres: {e}")
    
    def on_profile_change(self, event=None):
        """Gestionnaire de changement de profil audio"""
        try:
            selected_display = self.vars['audio_profile'].get()
            
            # Trouve la clé correspondante
            profile_key = None
            for key, display in self.audio_profiles.items():
                if display == selected_display:
                    profile_key = key
                    break
            
            if profile_key and profile_key != "auto":
                # Met à jour les paramètres selon le profil
                profile_settings = {
                    "ultra_low_latency": {"sample_rate": 44100, "buffer_size": 512},
                    "low_latency": {"sample_rate": 44100, "buffer_size": 1024},
                    "quality": {"sample_rate": 44100, "buffer_size": 2048},
                    "bandwidth_saving": {"sample_rate": 22050, "buffer_size": 4096}
                }
                
                if profile_key in profile_settings:
                    settings = profile_settings[profile_key]
                    self.vars['sample_rate'].set(settings["sample_rate"])
                    self.vars['buffer_size'].set(settings["buffer_size"])
                    
        except Exception as e:
            print(f"Erreur lors du changement de profil: {e}")
    
    def on_vox_toggle(self):
        """Active/désactive les contrôles VOX"""
        enabled = self.vars['vox_enabled'].get()
        
        # Liste des types de widgets qui supportent l'option 'state'
        state_supported_widgets = (ttk.Entry, ttk.Combobox, ttk.Scale, ttk.Checkbutton, 
                                 ttk.Button, ttk.Radiobutton, ttk.Spinbox)
        
        # Active/désactive les widgets dans le frame VOX
        for widget in self.vox_params_frame.winfo_children():
            if isinstance(widget, state_supported_widgets):
                try:
                    widget.configure(state="normal" if enabled else "disabled")
                except tk.TclError:
                    pass  # Ignore les widgets qui ne supportent pas cette option
            
            # Récursif pour les frames imbriquées
            for child in widget.winfo_children():
                if isinstance(child, state_supported_widgets):
                    try:
                        child.configure(state="normal" if enabled else "disabled")
                    except tk.TclError:
                        pass  # Ignore les widgets qui ne supportent pas cette option
    
    def start_vox_test(self):
        """Démarre le test VOX en temps réel"""
        if not hasattr(self, 'vox_test_running') or not self.vox_test_running:
            self.vox_test_running = True
            self.start_audio_monitoring()
        else:
            self.vox_test_running = False
            self.stop_audio_monitoring()
    
    def start_audio_monitoring(self):
        """Démarre le monitoring audio pour le VU-mètre"""
        try:
            import pyaudio
            import numpy as np
            
            self.audio_monitor = pyaudio.PyAudio()
            
            # Configuration audio
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            chunk = 1024
            
            # Ouvrir le stream audio
            self.audio_stream = self.audio_monitor.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            # Changer le texte du bouton
            for widget in self.window.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    for tab in widget.tabs():
                        frame = widget.nametowidget(tab)
                        for child in frame.winfo_children():
                            if isinstance(child, ttk.LabelFrame) and "Niveau Audio" in str(child['text']):
                                for button in child.winfo_children():
                                    if isinstance(button, ttk.Button) and "Test VOX" in str(button['text']):
                                        button.config(text="🔴 Arrêter le monitoring")
            
            # Démarrer la lecture des données audio
            self.update_audio_level()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de démarrer le monitoring audio: {e}")
            self.vox_test_running = False
    
    def stop_audio_monitoring(self):
        """Arrête le monitoring audio"""
        try:
            if hasattr(self, 'audio_stream'):
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            if hasattr(self, 'audio_monitor'):
                self.audio_monitor.terminate()
            
            # Remettre le texte du bouton
            for widget in self.window.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    for tab in widget.tabs():
                        frame = widget.nametowidget(tab)
                        for child in frame.winfo_children():
                            if isinstance(child, ttk.LabelFrame) and "Niveau Audio" in str(child['text']):
                                for button in child.winfo_children():
                                    if isinstance(button, ttk.Button) and "Arrêter" in str(button['text']):
                                        button.config(text="🎤 Test VOX en Temps Réel")
            
            # Remettre les barres à zéro
            self.audio_level_var.set(0)
            self.level_label.config(text="Niveau: 0.000")
            
        except Exception as e:
            print(f"Erreur lors de l'arrêt du monitoring: {e}")
    
    def update_audio_level(self):
        """Met à jour le niveau audio en temps réel"""
        if not self.vox_test_running:
            return
            
        try:
            import numpy as np
            
            # Lire les données audio
            data = self.audio_stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Calculer le niveau RMS en dB
            rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            if rms > 0:
                import math
                level = 20 * math.log10(rms / 32767.0)  # Convertir en dB
                level = max(-60.0, level)  # Limiter à -60dB minimum
            else:
                level = -60.0
            
            # Mettre à jour l'interface (convertir dB vers 0-1 pour l'affichage de la barre)
            display_level = max(0, min(1, (level + 60) / 60))  # -60dB à 0dB -> 0 à 1
            self.audio_level_var.set(display_level)
            self.level_label.config(text=f"Niveau: {level:.1f} dB")
            
            # Vérifier le seuil VOX
            threshold = self.vars['vox_threshold'].get()
            if level > threshold:
                self.level_label.config(foreground="green")
            else:
                self.level_label.config(foreground="red")
            
            # Programmer la prochaine mise à jour
            self.window.after(50, self.update_audio_level)  # 20 FPS
            
        except Exception as e:
            print(f"Erreur monitoring audio: {e}")
            self.vox_test_running = False
    
    def test_network(self):
        """Teste la connectivité réseau"""
        self.network_status_label.config(text="Test en cours...", foreground="orange")
        self.window.update()
        
        def run_test():
            try:
                import socket
                import time
                
                # Test de port
                port = self.vars['server_port'].get()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                try:
                    sock.bind(('localhost', port))
                    sock.close()
                    port_status = f"✅ Port {port} disponible"
                except:
                    port_status = f"❌ Port {port} occupé"
                
                # Test de latence
                start_time = time.time()
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(5)
                try:
                    test_sock.connect(('127.0.0.1', 80))
                    latency = (time.time() - start_time) * 1000
                    latency_status = f"🌐 Latence locale: {latency:.1f}ms"
                except:
                    latency_status = "⚠️ Test de latence échoué"
                test_sock.close()
                
                result = f"{port_status}\n{latency_status}"
                
                def update_ui():
                    self.network_status_label.config(text=result, foreground="black")
                
                self.window.after(0, update_ui)
                
            except Exception as e:
                def update_error():
                    self.network_status_label.config(text=f"❌ Erreur: {e}", foreground="red")
                self.window.after(0, update_error)
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def run_full_diagnostic(self):
        """Lance le diagnostic complet"""
        self.diagnostic_text.delete(1.0, tk.END)
        self.diagnostic_text.insert(tk.END, "🔍 Lancement du diagnostic complet...\n\n")
        self.diagnostic_text.update()
        
        def run_diagnostic():
            try:
                # Exécute le script de diagnostic
                diagnostic_path = Path(__file__).parent.parent / "diagnostic.py"
                if not diagnostic_path.exists():
                    diagnostic_path = Path.cwd() / "diagnostic.py"
                
                if diagnostic_path.exists():
                    result = subprocess.run([sys.executable, str(diagnostic_path)], 
                                          capture_output=True, text=True, 
                                          cwd=str(diagnostic_path.parent))
                    
                    def update_results():
                        self.diagnostic_text.delete(1.0, tk.END)
                        if result.returncode == 0:
                            self.diagnostic_text.insert(tk.END, result.stdout)
                        else:
                            self.diagnostic_text.insert(tk.END, f"❌ Erreur lors du diagnostic:\n{result.stderr}")
                        
                        # Sauvegarde les résultats
                        self.config_manager.set("last_diagnostic_date", datetime.now().isoformat())
                        self.config_manager.set("diagnostic_results", result.stdout[:1000])  # Limite la taille
                    
                    self.window.after(0, update_results)
                else:
                    def show_error():
                        self.diagnostic_text.delete(1.0, tk.END)
                        self.diagnostic_text.insert(tk.END, "❌ Script de diagnostic non trouvé")
                    self.window.after(0, show_error)
                    
            except Exception as e:
                def show_exception():
                    self.diagnostic_text.delete(1.0, tk.END)
                    self.diagnostic_text.insert(tk.END, f"❌ Erreur: {e}")
                self.window.after(0, show_exception)
        
        threading.Thread(target=run_diagnostic, daemon=True).start()
    
    def run_audio_test(self):
        """Lance un test audio rapide"""
        self.diagnostic_text.delete(1.0, tk.END)
        self.diagnostic_text.insert(tk.END, "🎵 Test audio rapide...\n\n")
        
        def test_audio():
            try:
                import pyaudio
                
                result_text = "📊 RÉSULTATS DU TEST AUDIO RAPIDE\n"
                result_text += "=" * 50 + "\n\n"
                
                p = pyaudio.PyAudio()
                device_count = p.get_device_count()
                
                result_text += f"🎵 Périphériques audio détectés: {device_count}\n"
                
                input_devices = []
                output_devices = []
                
                for i in range(device_count):
                    info = p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        input_devices.append(info['name'])
                    if info['maxOutputChannels'] > 0:
                        output_devices.append(info['name'])
                
                result_text += f"🎤 Microphones: {len(input_devices)}\n"
                result_text += f"🔊 Haut-parleurs: {len(output_devices)}\n\n"
                
                # Test des profils
                profiles = [
                    ("Ultra Low", 44100, 512),
                    ("Low Latency", 44100, 1024),
                    ("Quality", 44100, 2048)
                ]
                
                result_text += "⚡ Test des profils de latence:\n"
                for name, rate, buffer in profiles:
                    try:
                        stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate,
                                      input=True, output=True, frames_per_buffer=buffer)
                        latency = (buffer / rate) * 1000
                        stream.close()
                        result_text += f"  ✅ {name}: ~{latency:.1f}ms\n"
                    except Exception as e:
                        result_text += f"  ❌ {name}: Erreur - {str(e)[:50]}...\n"
                
                p.terminate()
                
                result_text += f"\n🕒 Test terminé: {datetime.now().strftime('%H:%M:%S')}\n"
                
                def update_text():
                    self.diagnostic_text.delete(1.0, tk.END)
                    self.diagnostic_text.insert(tk.END, result_text)
                
                self.window.after(0, update_text)
                
            except Exception as e:
                def show_error():
                    self.diagnostic_text.delete(1.0, tk.END)
                    self.diagnostic_text.insert(tk.END, f"❌ Erreur lors du test audio: {e}")
                self.window.after(0, show_error)
        
        threading.Thread(target=test_audio, daemon=True).start()
    
    def save_diagnostic_report(self):
        """Sauvegarde le rapport de diagnostic"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
                title="Sauvegarder le rapport de diagnostic"
            )
            
            if filename:
                content = self.diagnostic_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Succès", f"Rapport sauvegardé: {filename}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def auto_configure(self):
        """Configuration automatique basée sur le diagnostic"""
        if messagebox.askyesno("Configuration Automatique", 
                             "Voulez-vous lancer un diagnostic et appliquer automatiquement "
                             "la configuration optimale pour votre système?"):
            
            self.diagnostic_text.delete(1.0, tk.END)
            self.diagnostic_text.insert(tk.END, "🤖 Configuration automatique en cours...\n\n")
            
            def auto_config():
                try:
                    # Simulation d'analyse du système
                    import psutil
                    import time
                    
                    # Analyse CPU et RAM
                    cpu_percent = psutil.cpu_percent(interval=1)
                    ram_percent = psutil.virtual_memory().percent
                    
                    config_text = f"📊 Analyse système:\n"
                    config_text += f"   CPU: {cpu_percent:.1f}%\n"
                    config_text += f"   RAM: {ram_percent:.1f}%\n\n"
                    
                    # Recommandations
                    if cpu_percent < 30 and ram_percent < 50:
                        # Système performant
                        recommended_profile = "ultra_low_latency"
                        config_text += "🚀 Système performant détecté\n"
                        config_text += "   Profil recommandé: Ultra Low Latency\n"
                        
                        self.vars['audio_profile'].set(self.audio_profiles["ultra_low_latency"])
                        self.vars['sample_rate'].set(44100)
                        self.vars['buffer_size'].set(512)
                        self.vars['compression_enabled'].set(True)
                        self.vars['thread_priority'].set("high")
                        
                    elif cpu_percent < 60 and ram_percent < 70:
                        # Système moyen
                        recommended_profile = "low_latency"
                        config_text += "⚡ Système standard détecté\n"
                        config_text += "   Profil recommandé: Low Latency\n"
                        
                        self.vars['audio_profile'].set(self.audio_profiles["low_latency"])
                        self.vars['sample_rate'].set(44100)
                        self.vars['buffer_size'].set(1024)
                        self.vars['compression_enabled'].set(True)
                        self.vars['thread_priority'].set("high")
                        
                    else:
                        # Système chargé
                        recommended_profile = "quality"
                        config_text += "🐌 Système chargé détecté\n"
                        config_text += "   Profil recommandé: Quality\n"
                        
                        self.vars['audio_profile'].set(self.audio_profiles["quality"])
                        self.vars['sample_rate'].set(44100)
                        self.vars['buffer_size'].set(2048)
                        self.vars['compression_enabled'].set(True)
                        self.vars['thread_priority'].set("normal")
                    
                    config_text += f"\n✅ Configuration automatique appliquée!\n"
                    config_text += f"💡 Vous pouvez ajuster manuellement les paramètres si nécessaire.\n"
                    
                    def update_ui():
                        self.diagnostic_text.delete(1.0, tk.END)
                        self.diagnostic_text.insert(tk.END, config_text)
                        messagebox.showinfo("Configuration Automatique", 
                                          f"Configuration optimisée appliquée!\n"
                                          f"Profil: {recommended_profile.replace('_', ' ').title()}")
                    
                    self.window.after(0, update_ui)
                    
                except Exception as e:
                    def show_error():
                        self.diagnostic_text.delete(1.0, tk.END)
                        self.diagnostic_text.insert(tk.END, f"❌ Erreur configuration automatique: {e}")
                    self.window.after(0, show_error)
            
            threading.Thread(target=auto_config, daemon=True).start()
    
    def export_config(self):
        """Exporte la configuration"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
                title="Exporter la configuration"
            )
            
            if filename:
                success = self.config_manager.export_config(filename)
                if success:
                    messagebox.showinfo("Succès", f"Configuration exportée: {filename}")
                else:
                    messagebox.showerror("Erreur", "Erreur lors de l'export")
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {e}")
    
    def import_config(self):
        """Importe une configuration"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.askopenfilename(
                filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
                title="Importer une configuration"
            )
            
            if filename:
                success = self.config_manager.import_config(filename)
                if success:
                    self.load_current_values()
                    messagebox.showinfo("Succès", f"Configuration importée: {filename}")
                else:
                    messagebox.showerror("Erreur", "Erreur lors de l'import")
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'import: {e}")
    
    def reset_to_defaults(self):
        """Remet les paramètres par défaut"""
        if messagebox.askyesno("Restaurer les Défauts", 
                             "Voulez-vous vraiment restaurer tous les paramètres par défaut?"):
            try:
                self.config_manager.reset_to_defaults()
                self.load_current_values()
                messagebox.showinfo("Succès", "Paramètres restaurés aux valeurs par défaut")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la restauration: {e}")
    
    def save_settings(self):
        """Sauvegarde les paramètres"""
        try:
            self.apply_settings()
            messagebox.showinfo("Succès", "Paramètres sauvegardés avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def apply_settings(self):
        """Applique les paramètres"""
        try:
            # Convertit le profil affiché en clé
            profile_display = self.vars['audio_profile'].get()
            profile_key = "auto"
            for key, display in self.audio_profiles.items():
                if display == profile_display:
                    profile_key = key
                    break
            
            # Prépare les mises à jour
            updates = {
                # Audio
                "audio_profile": profile_key,
                "custom_sample_rate": self.vars['sample_rate'].get(),
                "custom_buffer_size": self.vars['buffer_size'].get(),
                "compression_enabled": self.vars['compression_enabled'].get(),
                "compression_level": self.vars['compression_level'].get(),
                
                # VOX
                "vox_enabled": self.vars['vox_enabled'].get(),
                "vox_threshold": self.vars['vox_threshold'].get(),
                "vox_delay": self.vars['vox_delay'].get(),
                "vox_hangtime": self.vars['vox_hangtime'].get(),
                
                # Réseau
                "server_port": self.vars['server_port'].get(),
                "connection_timeout": self.vars['connection_timeout'].get(),
                "tcp_nodelay": self.vars['tcp_nodelay'].get(),
                "network_optimization": self.vars['network_optimization'].get(),
                
                # Diagnostic
                "auto_diagnostic": self.vars['auto_diagnostic'].get(),
                
                # Avancé
                "thread_priority": self.vars['thread_priority'].get(),
                "cpu_optimization": self.vars['cpu_optimization'].get(),
                "memory_optimization": self.vars['memory_optimization'].get(),
                "experimental_features": self.vars['experimental_features'].get(),
                "log_level": self.vars['log_level'].get(),
                "theme": self.vars['theme'].get(),
                "show_performance_metrics": self.vars['show_performance_metrics'].get()
            }
            
            # Applique les mises à jour
            success = self.config_manager.update_multiple(updates)
            
            if not success:
                messagebox.showerror("Erreur", "Erreur lors de l'application des paramètres")
                return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application: {e}")
            return False
    
    def cancel(self):
        """Annule et ferme la fenêtre"""
        # Arrêter le monitoring audio s'il est actif
        if hasattr(self, 'vox_test_running') and self.vox_test_running:
            self.vox_test_running = False
            self.stop_audio_monitoring()
        
        if self.window:
            self.window.destroy()
    
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

def show_settings(parent, config_manager):
    """Fonction utilitaire pour afficher les paramètres"""
    settings = SettingsWindow(parent, config_manager)
    settings.show()
    return settings