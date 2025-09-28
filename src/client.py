"""
Client vocal LAN - Se connecte au serveur, capture le micro et joue l'audio reçu
PHASE 1: Optimisations callback mode pour latence sub-milliseconde
"""

import socket
import threading
import time
import struct
import pyaudio
import numpy as np
import math
import zlib
from collections import deque
from typing import Optional, Callable

# Utiliser le système de logging centralisé
try:
    from src.logger import get_logger
    logger = get_logger('Client')
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Import du gestionnaire de configuration
try:
    from src.config_manager import get_config_manager
except ImportError:
    get_config_manager = None

# Import des optimisations PHASE 1
try:
    from src.audio_config import AudioOptimizer, UltraMinimalCallback, LockFreeRingBuffer, AudioConfig
except ImportError:
    AudioOptimizer = None
    UltraMinimalCallback = None
    LockFreeRingBuffer = None
    AudioConfig = None

class VoiceClient:
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 12345,
                 status_callback: Optional[Callable] = None):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.recording = False
        self.playing = False
        self.status_callback = status_callback
        
        # Gestionnaire de configuration
        self.config_manager = get_config_manager() if get_config_manager else None
        
        # Configuration audio depuis les paramètres utilisateur
        self._load_audio_config()
        
        # Configuration VOX depuis les paramètres
        self._load_vox_config()
        
        # Extraction des paramètres
        self.CHUNK = self.audio_config['CHUNK']
        self.FORMAT = self.audio_config['FORMAT']
        self.CHANNELS = self.audio_config['CHANNELS']
        self.RATE = self.audio_config['RATE']
        self.BUFFER_SIZE = self.audio_config.get('BUFFER_SIZE', 512)
        
        # Optimisations supplémentaires
        self.use_compression = True  # Compression audio
        self.adaptive_buffer = deque(maxlen=10)  # Buffer adaptatif
        
        # PyAudio
        self.audio = None
        self.input_stream = None
        self.output_stream = None
        
        # Threads
        self.receive_thread = None
        self.send_thread = None
        
        # État
        self.lock = threading.Lock()
        
        # VU-mètre et threshold
        self.audio_level = 0.0  # Niveau audio actuel (0-100)
        self.threshold = 10.0   # Seuil en pourcentage (0-100)
        self.vox_enabled = False  # Voice activation
        self.vox_active = False   # État actuel du VOX
        self.level_callback: Optional[Callable] = None  # Callback pour mettre à jour le VU-mètre
        self.vox_callback: Optional[Callable] = None     # Callback pour l'état VOX
        
        # Intégration gestionnaire de configuration
        self.config_manager = get_config_manager() if get_config_manager else None
        self._apply_user_config()
        
        # PHASE 1: Optimisations ultra-minimales
        self.ultra_minimal_mode = False
        self.callback_system = None  # Système de callbacks optimisé
        self.ring_buffers = {
            'input': None,
            'output': None,
            'network_send': None,
            'network_receive': None
        }
        
        # Détection du profil ULTRA_MINIMAL
        if hasattr(AudioConfig, 'ULTRA_MINIMAL_LATENCY') and \
           self.audio_config.get('DESCRIPTION', '').startswith('Latence sub-milliseconde'):
            self.ultra_minimal_mode = True
            logger.info("🚀 PHASE 1: Mode ultra-minimal activé")
            
            # Initialiser les buffers circulaires
            buffer_size = self.CHUNK * 64  # 64 chunks de buffer
            self.ring_buffers['input'] = LockFreeRingBuffer(buffer_size * 2) if LockFreeRingBuffer else None
            self.ring_buffers['output'] = LockFreeRingBuffer(buffer_size * 2) if LockFreeRingBuffer else None
            self.ring_buffers['network_send'] = LockFreeRingBuffer(buffer_size * 4) if LockFreeRingBuffer else None
            self.ring_buffers['network_receive'] = LockFreeRingBuffer(buffer_size * 4) if LockFreeRingBuffer else None
            
            # Système de callbacks
            if UltraMinimalCallback:
                self.callback_system = UltraMinimalCallback(self.CHUNK, self.RATE)
        
        logger.info(f"Client initialisé - Host: {host}, Port: {port}")
        logger.info(f"🎵 Configuration audio optimisée:")
        logger.info(f"   • Profil: {self.audio_config.get('DESCRIPTION', 'Personnalisé')}")
        if self.ultra_minimal_mode:
            logger.info(f"   🚀 Mode ULTRA-MINIMAL: Latence cible ~{(self.CHUNK/self.RATE)*1000:.1f}ms")
        logger.info(f"   • Latence théorique: ~{self._calculate_latency_ms():.1f}ms")
        logger.info(f"   • Chunk: {self.CHUNK} samples")
        logger.info(f"   • Sample Rate: {self.RATE} Hz")
        logger.info(f"   • Compression: {'Activée' if self.use_compression else 'Désactivée'}")
        logger.debug(f"Configuration détaillée - Format: {self.FORMAT}, Channels: {self.CHANNELS}, Buffer: {self.BUFFER_SIZE}")
        
    def _apply_user_config(self):
        """Applique la configuration utilisateur personnalisée"""
        try:
            if self.config_manager:
                # Configuration audio personnalisée
                audio_profile = self.config_manager.get('audio_profile', 'auto')
                
                if audio_profile != 'auto':
                    # Applique un profil spécifique
                    custom_rate = self.config_manager.get('custom_sample_rate')
                    custom_buffer = self.config_manager.get('custom_buffer_size')
                    
                    if custom_rate:
                        self.RATE = custom_rate
                        self.audio_config['RATE'] = custom_rate
                        
                    if custom_buffer:
                        self.CHUNK = custom_buffer
                        self.BUFFER_SIZE = custom_buffer
                        self.audio_config['CHUNK'] = custom_buffer
                        self.audio_config['BUFFER_SIZE'] = custom_buffer
                
                # Configuration de compression
                self.use_compression = self.config_manager.get('compression_enabled', True)
                
                # Configuration VOX
                self.vox_enabled = self.config_manager.get('vox_enabled', False)
                vox_threshold = self.config_manager.get('vox_threshold', -30.0)
                self.threshold = vox_threshold  # Seuil en dB
                
                logger.info(f"Configuration utilisateur appliquée: Profil={audio_profile}, VOX={self.vox_enabled}")
                
        except Exception as e:
            logger.warning(f"Erreur application config utilisateur: {e}")
    
    def _load_audio_config(self):
        """Charge la configuration audio par défaut"""
        self.audio_config = {
            'CHUNK': 1024,
            'FORMAT': pyaudio.paInt16,
            'CHANNELS': 1,
            'RATE': 44100,
            'BUFFER_SIZE': 1024,
            'DESCRIPTION': 'Configuration par défaut'
        }
    
    def _load_vox_config(self):
        """Charge la configuration VOX par défaut"""
        self.vox_enabled = False
        self.threshold = -30.0  # Seuil en décibels (dB)
        self.vox_active = False
    
    def reload_user_config(self):
        """Recharge la configuration utilisateur"""
        try:
            if self.config_manager:
                self.config_manager.load_config()
                self._apply_user_config()
                
                if self.status_callback:
                    self.status_callback("🔄 Configuration rechargée")
                    
                logger.info("Configuration utilisateur rechargée")
                
        except Exception as e:
            logger.error(f"Erreur rechargement config: {e}")
            if self.status_callback:
                self.status_callback(f"⚠️ Erreur config: {e}")
    
    def _calculate_latency_ms(self):
        """Calcule la latence théorique en millisecondes"""
        return (self.CHUNK / self.RATE) * 1000
    
    def _optimize_audio_thread(self):
        """Optimise le thread audio pour une latence minimale"""
        try:
            from src.audio_config import AudioOptimizer
            success = AudioOptimizer.optimize_thread_priority()
            if success:
                logger.debug("🚀 Priorité thread audio optimisée")
            return success
        except Exception as e:
            logger.debug(f"⚠️ Optimisation thread échouée: {e}")
            return False
    
    def _compress_audio(self, audio_data):
        """Compresse les données audio pour réduire la bande passante"""
        if not self.use_compression:
            return audio_data
        
        try:
            compressed = zlib.compress(audio_data, level=1)  # Compression rapide
            compression_ratio = len(compressed) / len(audio_data)
            logger.debug(f"🗜️ Compression audio: {compression_ratio:.2f} ratio")
            return compressed
        except Exception as e:
            logger.debug(f"⚠️ Erreur compression: {e}")
            return audio_data
    
    def _decompress_audio(self, compressed_data):
        """Décompresse les données audio"""
        if not self.use_compression:
            return compressed_data
        
        try:
            return zlib.decompress(compressed_data)
        except Exception as e:
            logger.debug(f"⚠️ Erreur décompression: {e}")
            return compressed_data
    
    def connect(self) -> bool:
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Timeout de 10 secondes pour la connexion
            
            # Optimisations socket pour faible latence
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER_SIZE)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.BUFFER_SIZE)
            
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(1)  # Timeout plus court pour les opérations normales
            self.connected = True
            
            # Initialiser PyAudio
            self.audio = pyaudio.PyAudio()
            
            logger.info(f"Connecté au serveur {self.host}:{self.port}")
            logger.debug(f"Socket connecté avec timeout: {self.socket.gettimeout()}s")
            self._update_status("Connecté au serveur")
            
            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self._receive_audio, daemon=True)
            self.receive_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur de connexion: {e}")
            self._update_status(f"Erreur de connexion: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Se déconnecte du serveur"""
        self.connected = False
        self.stop_recording()
        self.stop_playing()
        
        # Fermer le socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Attendre la fin des threads (éviter de joindre le thread actuel)
        current_thread = threading.current_thread()
        if self.receive_thread and self.receive_thread.is_alive() and self.receive_thread != current_thread:
            self.receive_thread.join(timeout=2)
        
        if self.send_thread and self.send_thread.is_alive() and self.send_thread != current_thread:
            self.send_thread.join(timeout=2)
        
        # Nettoyer PyAudio
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
            self.input_stream = None
        
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
            self.output_stream = None
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            self.audio = None
        
        logger.info("Déconnecté du serveur")
        self._update_status("Déconnecté")
    
    def start_recording(self) -> bool:
        """Démarre l'enregistrement du microphone avec optimisations PHASE 1"""
        if not self.connected or self.recording:
            return False
        
        try:
            # PHASE 1: Optimisations temps-réel avant création stream
            if self.ultra_minimal_mode and AudioOptimizer:
                logger.info("🚀 PHASE 1: Application optimisations temps-réel...")
                AudioOptimizer.apply_ultra_minimal_optimizations()
            
            # Optimisation du thread avant création stream
            self._optimize_audio_thread()
            
            # PHASE 1: Mode callback pour latence minimale
            if self.ultra_minimal_mode and self.callback_system:
                logger.info("🎯 PHASE 1: Activation mode callback ultra-rapide")
                
                # Stream d'entrée en mode callback
                self.input_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK,
                    input_device_index=None,
                    stream_callback=self.callback_system.input_callback,
                    start=False
                )
                
                # Thread de traitement des données depuis ring buffer
                self.send_thread = threading.Thread(target=self._send_audio_callback_mode, daemon=True)
                
            else:
                # Mode polling standard (compatibilité)
                self.input_stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK,
                    input_device_index=None,
                    start=False
                )
                
                # Thread de traitement standard
                self.send_thread = threading.Thread(target=self._send_audio, daemon=True)
            
            latency_ms = self._calculate_latency_ms()
            logger.debug(f"🎤 Stream d'entrée créé - Latence théorique: ~{latency_ms:.1f}ms")
            
            # Démarrage synchronisé
            self.input_stream.start_stream()
            self.recording = True
            self.send_thread.start()
            
            mode_info = "Mode CALLBACK ultra-rapide" if self.ultra_minimal_mode else "Mode polling standard"
            logger.info(f"Enregistrement démarré - {mode_info}")
            self._update_status(f"Enregistrement actif ({mode_info})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur démarrage enregistrement: {e}")
            self._update_status(f"Erreur micro: {e}")
            return False
    
    def stop_recording(self):
        """Arrête l'enregistrement du microphone"""
        self.recording = False
        
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
            self.input_stream = None
        
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=2)
        
        logger.info("Enregistrement arrêté")
        self._update_status("Connecté (micro inactif)")
    
    def start_playing(self) -> bool:
        """Démarre la lecture audio"""
        if not self.connected or self.playing:
            return False
        
        try:
            # Optimisation thread pour la lecture
            self._optimize_audio_thread()
            
            # Créer le stream de sortie
            self.output_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK,
                output_device_index=None,  # Device par défaut
                start=False  # Démarrage manuel
            )
            
            logger.debug(f"🔊 Stream de sortie optimisé créé - Latence: ~{self._calculate_latency_ms():.1f}ms")
            self.output_stream.start_stream()  # Démarrage synchronisé
            
            self.playing = True
            logger.info("Lecture démarrée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur démarrage lecture: {e}")
            self._update_status(f"Erreur haut-parleur: {e}")
            return False
    
    def stop_playing(self):
        """Arrête la lecture audio"""
        self.playing = False
        
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
            self.output_stream = None
        
        logger.info("Lecture arrêtée")
    
    def _send_audio(self):
        """Thread qui envoie l'audio capturé au serveur"""
        try:
            while self.recording and self.connected:
                if self.input_stream:
                    try:
                        # Lire les données audio
                        audio_data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                        
                        # Calculer le niveau audio pour le VU-mètre
                        self.audio_level = self.calculate_rms_level(audio_data)
                        
                        # Mettre à jour le VU-mètre via callback
                        if self.level_callback:
                            try:
                                self.level_callback(self.audio_level)
                            except Exception as e:
                                logger.error(f"Erreur callback niveau: {e}")
                        
                        # Vérifier si on doit transmettre (threshold/VOX)
                        should_send = self.should_transmit_audio()
                        
                        # Mettre à jour l'état VOX si nécessaire
                        if self.vox_enabled:
                            new_vox_state = self.audio_level > self.threshold
                            if new_vox_state != self.vox_active:
                                self.vox_active = new_vox_state
                                if self.vox_callback:
                                    try:
                                        self.vox_callback(new_vox_state)
                                    except Exception as e:
                                        logger.error(f"Erreur callback VOX: {e}")
                        
                        # Envoyer au serveur seulement si le seuil est dépassé
                        if should_send and self.socket:
                            # Compression des données audio pour réduire la bande passante
                            compressed_data = self._compress_audio(audio_data)
                            
                            # Envoyer avec en-tête de compression
                            compression_flag = b'\x01' if self.use_compression else b'\x00'
                            size_data = struct.pack('!I', len(compressed_data))
                            self.socket.sendall(compression_flag + size_data + compressed_data)
                            
                            # Log statistiques occasionnelles
                            if hasattr(self, '_send_count'):
                                self._send_count += 1
                            else:
                                self._send_count = 1
                            
                            if self._send_count % 100 == 0:  # Log toutes les 100 transmissions
                                original_size = len(audio_data)
                                compressed_size = len(compressed_data)
                                ratio = compressed_size / original_size if original_size > 0 else 1.0
                                logger.debug(f"📊 Compression audio: {ratio:.2f} ratio, {original_size}→{compressed_size} bytes")
                            
                    except Exception as e:
                        if self.recording:
                            logger.error(f"Erreur envoi audio: {e}")
                        break
                else:
                    time.sleep(0.01)
                    
        except Exception as e:
            logger.error(f"Erreur thread envoi: {e}")
        finally:
            logger.info("Thread d'envoi terminé")
    
    def _send_audio_callback_mode(self):
        """PHASE 1: Thread optimisé pour mode callback ultra-rapide"""
        try:
            logger.info("🚀 PHASE 1: Thread callback ultra-rapide démarré")
            
            while self.recording and self.connected:
                if self.callback_system and self.ring_buffers['input']:
                    # Lire les données du ring buffer (non-bloquant)
                    audio_data = self.ring_buffers['input'].read(self.CHUNK * 2)  # 2 bytes per sample
                    
                    if len(audio_data) >= self.CHUNK * 2:
                        # Calculer le niveau audio
                        self.audio_level = self.calculate_rms_level(bytes(audio_data))
                        
                        # Callbacks niveau et VOX (optimisés)
                        self._update_audio_callbacks()
                        
                        # Vérifier transmission
                        if self.should_transmit_audio() and self.socket:
                            # Compression ultra-rapide (mode callback = priorité latence)
                            if self.use_compression:
                                try:
                                    import lz4.frame
                                    # LZ4 est 10x plus rapide que zlib
                                    compressed_data = lz4.frame.compress(bytes(audio_data), compression_level=1)
                                    compression_flag = b'\x02'  # Flag LZ4
                                except ImportError:
                                    # Fallback zlib niveau 1 (rapide)
                                    compressed_data = zlib.compress(bytes(audio_data), level=1)
                                    compression_flag = b'\x01'  # Flag zlib
                            else:
                                compressed_data = bytes(audio_data)
                                compression_flag = b'\x00'  # Pas de compression
                            
                            # Envoi ultra-rapide avec buffer réseau
                            if self.ring_buffers['network_send']:
                                # Préparer paquet complet
                                size_data = struct.pack('!I', len(compressed_data))
                                packet = compression_flag + size_data + compressed_data
                                
                                # Ajouter au ring buffer réseau (non-bloquant)
                                if not self.ring_buffers['network_send'].write(packet):
                                    logger.debug("⚠️ Ring buffer réseau plein, paquet ignoré")
                            else:
                                # Envoi direct (fallback)
                                size_data = struct.pack('!I', len(compressed_data))
                                self.socket.sendall(compression_flag + size_data + compressed_data)
                    
                    # Statistiques temps-réel
                    if hasattr(self, '_callback_stats_count'):
                        self._callback_stats_count += 1
                    else:
                        self._callback_stats_count = 1
                    
                    if self._callback_stats_count % 1000 == 0:  # Stats toutes les 1000 itérations
                        if self.callback_system:
                            stats = self.callback_system.get_performance_stats()
                            logger.debug(f"🎯 PHASE 1 Stats: {stats['callbacks']} callbacks, "
                                       f"{stats['underruns']} underruns, {stats['overruns']} overruns")
                else:
                    # Attente ultra-courte pour éviter busy-wait
                    time.sleep(0.0001)  # 0.1ms
                    
        except Exception as e:
            logger.error(f"🚀 PHASE 1: Erreur thread callback: {e}")
        finally:
            logger.info("🚀 PHASE 1: Thread callback ultra-rapide terminé")
    
    def _update_audio_callbacks(self):
        """Optimise les callbacks niveau et VOX pour mode ultra-rapide"""
        try:
            # Callback niveau (optimisé)
            if self.level_callback:
                self.level_callback(self.audio_level)
            
            # Callback VOX (optimisé)
            if self.vox_enabled:
                new_vox_state = self.audio_level > self.threshold
                if new_vox_state != self.vox_active:
                    self.vox_active = new_vox_state
                    if self.vox_callback:
                        self.vox_callback(new_vox_state)
        except Exception as e:
            # Log minimal pour éviter impact performance
            pass
    
    def _receive_audio(self):
        """Thread qui reçoit l'audio du serveur"""
        try:
            while self.connected:
                try:
                    # Recevoir le flag de compression
                    compression_flag = self.socket.recv(1)
                    if not compression_flag:
                        break
                    
                    is_compressed = compression_flag == b'\x01'
                    
                    # Recevoir la taille du paquet
                    size_data = self.socket.recv(4)
                    if not size_data:
                        break
                    
                    audio_size = struct.unpack('!I', size_data)[0]
                    
                    # Recevoir les données audio
                    audio_data = b''
                    bytes_received = 0
                    while bytes_received < audio_size and self.connected:
                        chunk = self.socket.recv(min(audio_size - bytes_received, 4096))
                        if not chunk:
                            break
                        audio_data += chunk
                        bytes_received += len(chunk)
                    
                    # Décompresser les données si nécessaire
                    if len(audio_data) == audio_size:
                        if is_compressed:
                            audio_data = self._decompress_audio(audio_data)
                        
                        # Jouer l'audio si la lecture est active
                        if self.playing and self.output_stream:
                            try:
                                # Buffer adaptatif pour réduire les discontinuités
                                self.adaptive_buffer.append(audio_data)
                                
                                # Jouer immédiatement si buffer pas trop plein
                                if len(self.adaptive_buffer) <= 3:  # Max 3 chunks en buffer
                                    while self.adaptive_buffer and self.playing:
                                        chunk_to_play = self.adaptive_buffer.popleft()
                                        self.output_stream.write(chunk_to_play)
                                else:
                                    # Vider le buffer si trop plein (réduction latence)
                                    logger.debug("🚮 Vidage buffer adaptatif (réduction latence)")
                                    self.adaptive_buffer.clear()
                                    self.output_stream.write(audio_data)
                                    
                            except Exception as e:
                                if self.playing:
                                    logger.error(f"Erreur lecture audio: {e}")
                    
                except ConnectionResetError:
                    break
                except socket.timeout:
                    # Timeout normal, continuer si toujours connecté
                    if not self.connected:
                        break
                    continue
                except Exception as e:
                    if self.connected:
                        logger.error(f"Erreur réception audio: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Erreur thread réception: {e}")
        finally:
            logger.info("Thread de réception terminé")
            # Marquer comme déconnecté sans appeler disconnect() pour éviter la récursion
            if self.connected:
                self.connected = False
                self._update_status("Connexion perdue")
    
    def _update_status(self, status: str):
        """Met à jour le statut et appelle le callback si défini"""
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception as e:
                logger.error(f"Erreur callback status: {e}")
    
    def get_status(self):
        """Retourne le statut du client"""
        return {
            'connected': self.connected,
            'recording': self.recording,
            'playing': self.playing,
            'host': self.host,
            'port': self.port
        }
    
    def calculate_rms_level(self, audio_data: bytes) -> float:
        """Calcule le niveau RMS de l'audio en décibels (dB)"""
        try:
            # Convertir les bytes en array numpy
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculer le RMS
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Convertir en dB
            if rms > 0:
                db = 20 * math.log10(rms / 32767.0)  # 32767 = max valeur int16
                # Limiter la plage à -60dB minimum
                level = max(-60.0, db)
            else:
                level = -60.0  # Silence = -60dB
            
            return level
            
        except Exception as e:
            logger.error(f"Erreur calcul niveau RMS: {e}")
            return 0
    
    def should_transmit_audio(self) -> bool:
        """Détermine si l'audio doit être transmis basé sur le threshold"""
        if not self.vox_enabled:
            return self.recording  # Mode manuel
        
        # Mode VOX: vérifier le seuil
        return self.audio_level > self.threshold
    
    def set_threshold(self, threshold: float):
        """Définit le seuil de déclenchement (0-100)"""
        self.threshold = max(0, min(100, threshold))
    
    def set_vox_enabled(self, enabled: bool):
        """Active/désactive le mode VOX"""
        self.vox_enabled = enabled
        if not enabled:
            self.vox_active = False
            if self.vox_callback:
                self.vox_callback(False)
    
    def get_audio_devices(self):
        """Retourne la liste des périphériques audio disponibles"""
        devices = {'input': [], 'output': []}
        
        if not self.audio:
            temp_audio = pyaudio.PyAudio()
        else:
            temp_audio = self.audio
        
        try:
            for i in range(temp_audio.get_device_count()):
                device_info = temp_audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices['input'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels']
                    })
                if device_info['maxOutputChannels'] > 0:
                    devices['output'].append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxOutputChannels']
                    })
        except Exception as e:
            logger.error(f"Erreur énumération périphériques: {e}")
        finally:
            if not self.audio:
                temp_audio.terminate()
        
        return devices

if __name__ == "__main__":
    # Test du client
    client = VoiceClient()
    
    def status_update(status):
        print(f"Status: {status}")
    
    client.status_callback = status_update
    
    try:
        if client.connect():
            client.start_playing()
            print("Client connecté. Appuyez sur Entrée pour commencer/arrêter l'enregistrement, 'q' pour quitter")
            
            recording = False
            while True:
                user_input = input().strip().lower()
                if user_input == 'q':
                    break
                elif user_input == '':
                    if recording:
                        client.stop_recording()
                        recording = False
                        print("Enregistrement arrêté")
                    else:
                        if client.start_recording():
                            recording = True
                            print("Enregistrement démarré")
        else:
            print("Impossible de se connecter au serveur")
            
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")
    finally:
        client.disconnect()