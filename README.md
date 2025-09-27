# LanVoice - Application de Chat Vocal LAN

## Description
LanVoice est une application Python de chat vocal en réseau local (LAN) avec interface graphique. Elle permet de créer un serveur vocal et de s'y connecter pour communiquer en temps réel avec d'autres utilisateurs sur le même réseau.

## Fonctionnalités

### 🎙️ Chat Vocal
- **Mode Serveur** : Héberge une session vocal pour plusieurs clients
- **Mode Client** : Se connecte à un serveur vocal existant
- **Audio en temps réel** : Capture et diffusion audio avec PyAudio

### 📊 Interface Avancée
- **VU-Meter** : Affichage visuel du niveau audio en temps réel
- **VOX (Voice Activated Transmission)** : Transmission automatique basée sur le niveau sonore
- **Seuil ajustable** : Contrôle de la sensibilité de déclenchement vocal
- **Indicateurs de statut** : Statut de connexion et transmission en temps réel

### 📝 Logging Complet
- **Journalisation détaillée** : Logs de toutes les opérations
- **Informations système** : CPU, mémoire, réseau automatiquement loggés
- **Rotation des logs** : Gestion automatique de la taille des fichiers de log
- **Nettoyage automatique** : Logs effacés à chaque démarrage

### 🚨 Gestion d'Erreurs Avancée
- **Messages détaillés** : Erreurs explicites avec causes possibles et solutions
- **Diagnostic automatique** : Identification des problèmes réseau et audio
- **Support multi-langues** : Messages d'erreur en français avec contexte technique
- **Logging verbeux** : Tous les détails techniques sauvegardés pour debug

## Installation

### Prérequis
- Python 3.7+
- Windows (testé sur Windows 11)

### Installation des dépendances
```bash
pip install -r requirements.txt
   ```

2. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: Si vous rencontrez des problèmes avec PyAudio sur Windows, vous pouvez télécharger le fichier .whl approprié depuis [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) et l'installer avec:
   ```bash
   pip install pyaudio‑0.2.11‑cp39‑cp39‑win_amd64.whl
   ```

   **Note**: Numpy est requis pour le VU-mètre. Il s'installe automatiquement avec `pip install -r requirements.txt`

3. **Testez le VU-mètre et threshold (optionnel)**
   ```bash
   python test_vu_meter.py
   ```

4. **Lancez l'application**
   ```bash
   python main.py
   ```

## 📖 Utilisation

### Mode Serveur
1. Sélectionnez "🖥️ Serveur (héberger)"
2. Le port par défaut est 12345 (modifiable)
3. Cliquez sur "Démarrer serveur"
4. Partagez votre adresse IP avec les autres utilisateurs
5. Utilisez le bouton "🎤 Parler" pour activer/désactiver votre microphone

### Mode Client
1. Sélectionnez "👤 Client (rejoindre)"
2. Saisissez l'adresse IP du serveur
3. Vérifiez le port (12345 par défaut)
4. Cliquez sur "Se connecter"
5. Utilisez les boutons "🎤 Parler" et "🔊 Écouter" pour contrôler l'audio

### Nouvelles Fonctionnalités Audio

#### 🎚️ VU-mètre
- **Affichage en temps réel** du niveau audio de votre microphone
- **Indicateur coloré**: Vert (normal), Orange (fort), Rouge (très fort)
- **Pourcentage précis** du niveau sonore

#### 🎤 Mode VOX (Voice Activation)
- **Activation automatique** du microphone quand vous parlez
- **Seuil réglable** de 0% à 50% selon votre environnement
- **Indicateur visuel** de l'état VOX (Actif/Inactif)
- **Économise la bande passante** en ne transmettant que quand nécessaire

#### ⚙️ Réglage du Seuil
- **Curseur intuitif** pour ajuster la sensibilité
- **Valeur en temps réel** affichée à côté du curseur
- **Test visuel** avec le VU-mètre pour trouver le bon niveau

### 📝 Système de Logging

#### Fonctionnalités
- **Nouveau fichier à chaque démarrage** avec timestamp
- **Logging détaillé** : Informations système, périphériques audio, réseau
- **Rotation automatique** : Conservation des 10 derniers logs
- **Format complet** : Timestamp, module, niveau, fichier, ligne, fonction
- **Logs dans `logs/`** : Dossier créé automatiquement

#### Informations loggées
- **Système** : OS, architecture, RAM, processeur (avec psutil)
- **Audio** : Tous les périphériques d'entrée/sortie, périphériques par défaut
- **Réseau** : Nom d'hôte, adresses IP locales
- **Application** : Démarrage, connexions, erreurs, événements
- **Performance** : Threads, timeouts, états des connexions

#### Consultation des logs
- **Fichiers** : `logs/lanvoice_YYYYMMDD_HHMMSS.log`
- **Test** : `python test_logging.py` pour voir le système en action
- **Niveaux** : DEBUG, INFO, WARNING, ERROR, CRITICAL avec stack traces

### Conseils d'utilisation
- **Test local**: Utilisez 127.0.0.1 pour tester sur la même machine
- **Réseau local**: Utilisez le bouton "IP Locale" pour obtenir votre adresse IP
- **Qualité audio**: Utilisez un casque pour éviter l'écho
- **Réglage VOX**: Ajustez le seuil entre 5-15% pour un environnement calme, 15-25% pour un environnement bruyant
- **Dépannage**: Consultez les logs dans le dossier `logs/` pour diagnostiquer les problèmes
- **Performances**: Fermez les applications gourmandes en ressources pour une meilleure qualité audio

## 🛠️ Création d'un exécutable

Pour créer un fichier .exe autonome:

1. **Installez PyInstaller** (déjà inclus dans requirements.txt)
   ```bash
   pip install pyinstaller
   ```

2. **Utilisez le script de build**
   ```bash
   python build_exe.py
   ```

3. **L'exécutable sera créé dans le dossier `dist/`**

## 📁 Structure du projet

```
LanVoice/
├── main.py              # Point d'entrée principal
├── requirements.txt     # Dépendances Python
├── build_exe.py        # Script de création d'exécutable
├── README.md           # Ce fichier
├── src/
│   ├── server.py       # Serveur vocal
│   ├── client.py       # Client vocal
│   └── gui.py          # Interface graphique
└── assets/             # Ressources (icônes, etc.)
```

## ⚙️ Configuration

### Paramètres Audio
- **Format**: 16-bit PCM
- **Fréquence**: 44.1 kHz
- **Canaux**: Mono (1 canal)
- **Buffer**: 1024 échantillons

### Paramètres Réseau
- **Port par défaut**: 12345
- **Protocole**: TCP
- **Timeout de connexion**: 5 secondes

## 🔧 Dépannage

### Problèmes courants

1. **"Impossible d'activer le microphone"**
   - Vérifiez que votre microphone fonctionne
   - Vérifiez les permissions d'accès au microphone
   - Redémarrez l'application

2. **"Erreur de connexion au serveur"**
   - Vérifiez l'adresse IP et le port
   - Assurez-vous que le serveur est démarré
   - Vérifiez le pare-feu Windows

3. **"Erreur lors de l'installation de PyAudio"**
   - Sur Windows: Téléchargez le fichier .whl depuis le site officiel
   - Sur Linux: `sudo apt-get install portaudio19-dev python3-pyaudio`
   - Sur macOS: `brew install portaudio`

4. **Audio de mauvaise qualité ou coupé**
   - Fermez les autres applications audio
   - Utilisez un casque pour éviter l'écho
   - Vérifiez la qualité de votre connexion réseau

### Logs et Debug
- Les messages d'information s'affichent dans le journal de l'application
- Pour plus de détails, vérifiez la console lors du lancement depuis le terminal

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à:
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## 📄 Licence

Ce projet est libre d'utilisation pour un usage personnel et éducatif.

## � Dépannage Avancé

LanVoice intègre maintenant une **gestion d'erreurs intelligente** qui vous guide automatiquement :

### Messages d'Erreur Informatifs
- **Erreurs de serveur** : Diagnostic automatique des problèmes de port, permissions, réseau
- **Erreurs de connexion** : Identification précise des causes (DNS, timeout, refus de connexion)  
- **Solutions proposées** : Actions concrètes suggérées pour chaque type d'erreur

### Test des Erreurs
```bash
python test_verbose_errors.py
```

### Documentation Complète
Consultez [`GESTION_ERREURS.md`](GESTION_ERREURS.md) pour le guide complet de dépannage.

## �📞 Support

Pour toute question ou problème:
1. **Vérifiez les messages d'erreur** : L'application fournit maintenant des diagnostics détaillés
2. **Consultez les logs** : Dossier `logs/` avec informations techniques complètes
3. **Lisez la documentation** : [`GESTION_ERREURS.md`](GESTION_ERREURS.md) pour les cas spécifiques
2. Vérifiez que toutes les dépendances sont installées
3. Testez d'abord en mode local (127.0.0.1)

---

**Amusez-vous bien avec LanVoice ! 🎤🔊**