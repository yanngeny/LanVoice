"""
Client vocal LAN - Se connecte au serveur, capture le micro et joue l'audio reçu
"""

import socket
import threading
import time
import struct
import pyaudio
import numpy as np
import math
from typing import Optional, Callable

# Utiliser le système de logging centralisé
try:
    from src.logger import get_logger
    logger = get_logger('Client')
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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
        
        # Configuration audio
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
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
        
        logger.info(f"Client initialisé - Host: {host}, Port: {port}")
        logger.debug(f"Configuration audio - Format: {self.FORMAT}, Channels: {self.CHANNELS}, Rate: {self.RATE}, Chunk: {self.CHUNK}")
        
    def connect(self) -> bool:
        """Se connecte au serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Timeout de 10 secondes pour la connexion
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
        """Démarre l'enregistrement du microphone"""
        if not self.connected or self.recording:
            return False
        
        try:
            # Créer le stream d'entrée
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.recording = True
            
            # Démarrer le thread d'envoi
            self.send_thread = threading.Thread(target=self._send_audio, daemon=True)
            self.send_thread.start()
            
            logger.info("Enregistrement démarré")
            logger.debug(f"Stream d'entrée créé - Format: {self.FORMAT}, Channels: {self.CHANNELS}, Rate: {self.RATE}")
            self._update_status("Enregistrement actif")
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
            # Créer le stream de sortie
            self.output_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK
            )
            
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
                            size_data = struct.pack('!I', len(audio_data))
                            self.socket.sendall(size_data + audio_data)
                            
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
    
    def _receive_audio(self):
        """Thread qui reçoit l'audio du serveur"""
        try:
            while self.connected:
                try:
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
                    
                    # Jouer l'audio si la lecture est active
                    if len(audio_data) == audio_size and self.playing and self.output_stream:
                        try:
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
        """Calcule le niveau RMS de l'audio en pourcentage (0-100)"""
        try:
            # Convertir les bytes en array numpy
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculer le RMS
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Convertir en dB puis en pourcentage (0-100)
            if rms > 0:
                db = 20 * math.log10(rms / 32767.0)  # 32767 = max valeur int16
                # Normaliser de -60dB/0dB vers 0-100%
                level = max(0, min(100, (db + 60) * 100 / 60))
            else:
                level = 0
            
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