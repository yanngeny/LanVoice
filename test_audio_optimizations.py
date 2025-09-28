"""
Script de test et benchmark des optimisations audio LanVoice
Mesure les améliorations de latence et qualité
"""

import time
import threading
import sys
import os
import statistics

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.audio_config import AudioConfig, AudioOptimizer, benchmark_audio_configs
    from src.server import VoiceServer
    from src.client import VoiceClient
    from src.logger import init_logging, get_logger
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

def test_audio_configurations():
    """Teste les différentes configurations audio"""
    print("=" * 80)
    print("🎵 TEST DES CONFIGURATIONS AUDIO OPTIMISÉES")
    print("=" * 80)
    
    # Afficher les profils disponibles
    benchmark_audio_configs()
    
    # Test pratique avec PyAudio
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        
        print(f"\n🔊 TESTS PYAUDIO PRATIQUES")
        print("=" * 50)
        
        configs_to_test = [
            ("ULTRA_LOW_LATENCY", AudioConfig.ULTRA_LOW_LATENCY),
            ("LOW_LATENCY", AudioConfig.LOW_LATENCY),
            ("QUALITY", AudioConfig.QUALITY),
            ("BANDWIDTH_SAVING", AudioConfig.BANDWIDTH_SAVING)
        ]
        
        for name, config in configs_to_test:
            print(f"\n📊 Test: {name}")
            try:
                # Tester la création d'un stream d'entrée
                stream = audio.open(
                    format=config['FORMAT'],
                    channels=config['CHANNELS'],
                    rate=config['RATE'],
                    input=True,
                    frames_per_buffer=config['CHUNK']
                )
                
                # Mesurer le temps de lecture d'un chunk
                start_time = time.perf_counter()
                data = stream.read(config['CHUNK'], exception_on_overflow=False)
                read_time = time.perf_counter() - start_time
                
                stream.stop_stream()
                stream.close()
                
                theoretical_latency = AudioConfig.get_latency_ms(config)
                actual_latency = read_time * 1000
                
                print(f"   ✅ Succès - Latence théorique: {theoretical_latency:.1f}ms")
                print(f"               Latence mesurée: {actual_latency:.1f}ms")
                print(f"               Taille chunk: {len(data)} bytes")
                
            except Exception as e:
                print(f"   ❌ Échec: {e}")
        
        audio.terminate()
        
    except ImportError:
        print("⚠️ PyAudio non disponible pour les tests pratiques")

def benchmark_compression():
    """Benchmark de la compression audio"""
    print(f"\n🗜️ BENCHMARK COMPRESSION AUDIO")
    print("=" * 50)
    
    import zlib
    import random
    
    # Simuler des données audio de différentes tailles
    test_sizes = [128, 256, 512, 1024, 2048]  # Chunks audio typiques
    compression_levels = [1, 3, 6, 9]  # Niveaux de compression zlib
    
    for chunk_size in test_sizes:
        print(f"\n📦 Chunk size: {chunk_size} samples ({chunk_size * 2} bytes)")
        
        # Générer des données audio simulées (variation sinusoïdale + bruit)
        audio_data = bytearray()
        for i in range(chunk_size):
            # Simuler audio vocal avec harmoniques
            sample = int(32767 * 0.3 * (
                0.7 * (i / chunk_size) +  # Tendance
                0.2 * ((i * 3) % 100 / 100) +  # Harmonique
                0.1 * random.random()  # Bruit
            ))
            audio_data.extend(sample.to_bytes(2, 'little', signed=True))
        
        original_size = len(audio_data)
        
        for level in compression_levels:
            start_time = time.perf_counter()
            compressed = zlib.compress(audio_data, level=level)
            compress_time = time.perf_counter() - start_time
            
            start_time = time.perf_counter()
            decompressed = zlib.decompress(compressed)
            decompress_time = time.perf_counter() - start_time
            
            compression_ratio = len(compressed) / original_size
            total_time = compress_time + decompress_time
            
            print(f"   Niveau {level}: {compression_ratio:.3f} ratio, "
                  f"{total_time*1000:.2f}ms total, "
                  f"({compress_time*1000:.2f}ms + {decompress_time*1000:.2f}ms)")
            
            # Vérifier l'intégrité
            if decompressed != audio_data:
                print(f"   ❌ ERREUR: Corruption des données!")
    
    print(f"\n🎯 RECOMMANDATION: Niveau 1 pour temps réel (< 1ms)")

def test_network_optimizations():
    """Teste les optimisations réseau"""
    print(f"\n🌐 TEST OPTIMISATIONS RÉSEAU")
    print("=" * 50)
    
    # Test de création de serveur optimisé
    try:
        server = VoiceServer(host="127.0.0.1", port=12347)
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        
        time.sleep(0.5)  # Laisser le serveur démarrer
        
        if server.running:
            print("✅ Serveur optimisé créé avec succès")
            
            # Test de connexion client optimisé
            client = VoiceClient(host="127.0.0.1", port=12347)
            if client.connect():
                print("✅ Client optimisé connecté avec succès")
                print(f"   📊 Configuration: {client.audio_config.get('DESCRIPTION', 'N/A')}")
                print(f"   ⚡ Latence théorique: ~{client._calculate_latency_ms():.1f}ms")
                print(f"   🗜️ Compression: {'Activée' if client.use_compression else 'Désactivée'}")
                
                client.disconnect()
                print("✅ Client déconnecté proprement")
            else:
                print("❌ Échec connexion client")
            
            server.stop()
            print("✅ Serveur arrêté proprement")
        else:
            print("❌ Échec démarrage serveur")
            
    except Exception as e:
        print(f"❌ Erreur test réseau: {e}")

def performance_summary():
    """Résumé des performances attendues"""
    print(f"\n" + "=" * 80)
    print("📈 RÉSUMÉ DES AMÉLIORATIONS DE PERFORMANCE")
    print("=" * 80)
    
    print(f"\n🎯 RÉDUCTIONS DE LATENCE:")
    print(f"   • Configuration audio: 1024→256 chunks = ~75% latence en moins")
    print(f"   • Buffers réseau optimisés: TCP_NODELAY + buffers réduits")
    print(f"   • Threads haute priorité: Moins d'interruptions système")
    print(f"   • Buffer adaptatif: Évite l'accumulation de latence")
    
    print(f"\n💾 OPTIMISATIONS BANDE PASSANTE:")
    print(f"   • Compression zlib niveau 1: ~60-80% réduction")
    print(f"   • Transmission sélective VOX: Économie sur silences")
    print(f"   • Pré-compression serveur: Une compression pour tous")
    
    print(f"\n⏱️ LATENCES THÉORIQUES (sans réseau):")
    print(f"   • Ultra Low: ~3ms (128 samples @ 44.1kHz)")
    print(f"   • Low Latency: ~6ms (256 samples @ 44.1kHz)")
    print(f"   • Quality: ~12ms (512 samples @ 44.1kHz)")
    print(f"   • Bandwidth Saving: ~12ms (256 samples @ 22kHz)")
    
    print(f"\n🔧 OPTIMISATIONS ADDITIONNELLES POSSIBLES:")
    print(f"   • Passage UDP: -90% latence réseau (TCP→UDP)")
    print(f"   • Suppression d'écho (AEC): Amélioration qualité")
    print(f"   • Filtrage adaptatif: Réduction bruit de fond")
    print(f"   • Prédiction audio: Compensation paquets perdus")

def main():
    """Fonction principale de test"""
    print("🚀 LANVOICE - TESTS DE PERFORMANCE AUDIO")
    print("Version optimisée avec compression et latence réduite")
    
    # Initialiser le logging
    init_logging()
    
    # Exécuter tous les tests
    test_audio_configurations()
    benchmark_compression()
    test_network_optimizations()
    performance_summary()
    
    print(f"\n✨ Tests terminés! Consultez les logs pour plus de détails.")

if __name__ == "__main__":
    main()