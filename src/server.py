"""
Serveur vocal LAN - Gère les connexions multiples et redistribue l'audio
"""

import socket
import threading
import time
import struct
from typing import Dict, Set

# Utiliser le système de logging centralisé
try:
    from src.logger import get_logger
    logger = get_logger('Server')
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class VoiceServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 12345):
        self.host = host
        self.port = port
        self.socket = None
        self.clients: Dict[socket.socket, str] = {}  # socket -> nom_client
        self.running = False
        self.lock = threading.Lock()
        
        logger.info(f"Serveur initialisé - Host: {host}, Port: {port}")
        
    def start(self):
        """Démarre le serveur"""
        try:
            logger.info(f"Tentative de démarrage du serveur sur {self.host}:{self.port}")
            
            # Créer le socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.debug("Socket créé avec succès")
            
            # Configuration du socket
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.debug("Option SO_REUSEADDR activée")
            
            # Liaison à l'adresse et au port
            self.socket.bind((self.host, self.port))
            logger.debug(f"Socket lié à {self.host}:{self.port}")
            
            # Écoute des connexions
            self.socket.listen(10)
            logger.debug("Socket en mode écoute (backlog: 10)")
            
            self.running = True
            
            logger.info(f"✅ Serveur vocal démarré avec succès sur {self.host}:{self.port}")
            logger.info("En attente de connexions...")
            logger.debug(f"Socket configuré avec SO_REUSEADDR, listen(10)")
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    client_socket.settimeout(1)  # Timeout pour les opérations client
                    logger.info(f"Nouvelle connexion de {address}")
                    
                    # Créer un thread pour gérer ce client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except OSError as e:
                    if self.running:
                        logger.error(f"Erreur lors de l'acceptation de connexion: {type(e).__name__}: {e}")
                        logger.debug(f"Errno: {getattr(e, 'errno', 'N/A')}, Winerror: {getattr(e, 'winerror', 'N/A')}")
                    break
                    
        except socket.error as e:
            logger.error(f"❌ Erreur socket lors du démarrage du serveur: {type(e).__name__}: {e}")
            logger.error(f"Errno: {getattr(e, 'errno', 'N/A')}, Winerror: {getattr(e, 'winerror', 'N/A')}")
            if e.errno == 10048:  # Windows: Address already in use
                logger.error(f"Le port {self.port} est déjà utilisé par une autre application")
            elif e.errno == 10013:  # Windows: Permission denied
                logger.error(f"Permissions insuffisantes pour utiliser le port {self.port}")
            raise  # Re-lever l'exception pour que GUI puisse la capturer
        except PermissionError as e:
            logger.error(f"❌ Permissions insuffisantes: {e}")
            logger.error(f"Impossible de se lier au port {self.port} - Essayez un port > 1024")
            raise
        except OSError as e:
            logger.error(f"❌ Erreur système lors du démarrage: {type(e).__name__}: {e}")
            logger.error(f"Host: {self.host}, Port: {self.port}")
            logger.error(f"Errno: {getattr(e, 'errno', 'N/A')}, Winerror: {getattr(e, 'winerror', 'N/A')}")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur inattendue du serveur: {type(e).__name__}: {e}")
            logger.error(f"Host: {self.host}, Port: {self.port}, Running: {self.running}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, address):
        """Gère un client connecté"""
        client_name = f"Client_{address[0]}_{address[1]}"
        
        try:
            # Ajouter le client à la liste
            with self.lock:
                self.clients[client_socket] = client_name
            
            logger.info(f"{client_name} connecté (thread: {threading.current_thread().name})")
            logger.debug(f"Client {client_name} ajouté à la liste - Total clients: {len(self.clients)}")
            self.broadcast_message(f"{client_name} a rejoint le salon", exclude=client_socket)
            
            while self.running:
                try:
                    # Recevoir la taille du paquet audio
                    size_data = client_socket.recv(4)
                    if not size_data:
                        break
                    
                    audio_size = struct.unpack('!I', size_data)[0]
                    
                    # Recevoir les données audio
                    audio_data = b''
                    bytes_received = 0
                    while bytes_received < audio_size:
                        chunk = client_socket.recv(min(audio_size - bytes_received, 4096))
                        if not chunk:
                            break
                        audio_data += chunk
                        bytes_received += len(chunk)
                    
                    if len(audio_data) == audio_size:
                        # Diffuser l'audio à tous les autres clients
                        self.broadcast_audio(audio_data, exclude=client_socket)
                    
                except ConnectionResetError:
                    logger.info(f"{client_name} a fermé la connexion")
                    break
                except socket.timeout:
                    # Timeout normal, continuer si le serveur tourne toujours
                    if not self.running:
                        break
                    continue
                except Exception as e:
                    logger.error(f"Erreur avec {client_name}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Erreur lors de la gestion de {client_name}: {e}")
        finally:
            # Nettoyer la connexion
            with self.lock:
                if client_socket in self.clients:
                    del self.clients[client_socket]
            
            try:
                client_socket.close()
            except:
                pass
            
            logger.info(f"{client_name} déconnecté")
            self.broadcast_message(f"{client_name} a quitté le salon", exclude=client_socket)
    
    def broadcast_audio(self, audio_data: bytes, exclude: socket.socket = None):
        """Diffuse l'audio à tous les clients connectés sauf celui exclu"""
        with self.lock:
            clients_to_remove = []
            for client_socket in self.clients:
                if client_socket == exclude:
                    continue
                
                try:
                    # Envoyer la taille puis les données avec gestion d'erreur
                    size_data = struct.pack('!I', len(audio_data))
                    client_socket.sendall(size_data + audio_data)
                except (ConnectionResetError, BrokenPipeError):
                    # Connexion fermée par le client
                    clients_to_remove.append(client_socket)
                except Exception as e:
                    logger.error(f"Erreur envoi audio à {self.clients[client_socket]}: {e}")
                    clients_to_remove.append(client_socket)
            
            # Nettoyer les clients déconnectés
            for client_socket in clients_to_remove:
                if client_socket in self.clients:
                    del self.clients[client_socket]
                try:
                    client_socket.close()
                except:
                    pass
    
    def broadcast_message(self, message: str, exclude: socket.socket = None):
        """Diffuse un message texte à tous les clients"""
        logger.info(f"Message diffusé: {message}")
        # Pour l'instant, on log juste les messages
        # On pourrait implémenter un canal texte séparé si nécessaire
    
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        
        # Fermer toutes les connexions clients
        with self.lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        # Fermer le socket serveur
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        logger.info("Serveur arrêté")
    
    def get_status(self):
        """Retourne le statut du serveur"""
        with self.lock:
            return {
                'running': self.running,
                'host': self.host,
                'port': self.port,
                'clients_count': len(self.clients),
                'clients': list(self.clients.values())
            }

if __name__ == "__main__":
    # Test du serveur
    server = VoiceServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    finally:
        server.stop()