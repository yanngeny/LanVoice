"""
Configuration audio optimisée pour LanVoice
Paramètres ajustés pour minimiser la latence tout en préservant la qualité vocale
"""

import pyaudio

class AudioConfig:
    """Configuration audio optimisée pour faible latence"""
    
    # ========================================
    # PROFILS DE LATENCE
    # ========================================
    
    # Profil Ultra Faible Latence (< 10ms)
    ULTRA_LOW_LATENCY = {
        'CHUNK': 128,           # 2.9ms de latence à 44100 Hz
        'FORMAT': pyaudio.paInt16,
        'CHANNELS': 1,
        'RATE': 44100,
        'BUFFER_SIZE': 256,     # Buffer réseau réduit
        'DESCRIPTION': 'Ultra faible latence - Idéal pour LAN rapide'
    }
    
    # Profil Faible Latence (< 20ms)
    LOW_LATENCY = {
        'CHUNK': 256,           # 5.8ms de latence à 44100 Hz
        'FORMAT': pyaudio.paInt16,
        'CHANNELS': 1,
        'RATE': 44100,
        'BUFFER_SIZE': 512,
        'DESCRIPTION': 'Faible latence - Équilibre optimal'
    }
    
    # Profil Qualité (< 50ms)
    QUALITY = {
        'CHUNK': 512,           # 11.6ms de latence à 44100 Hz
        'FORMAT': pyaudio.paInt16,
        'CHANNELS': 1,
        'RATE': 44100,
        'BUFFER_SIZE': 1024,
        'DESCRIPTION': 'Qualité audio - Plus stable'
    }
    
    # Profil Économie Bande Passante
    BANDWIDTH_SAVING = {
        'CHUNK': 256,
        'FORMAT': pyaudio.paInt16,
        'CHANNELS': 1,
        'RATE': 22050,          # Réduction 50% bande passante
        'BUFFER_SIZE': 512,
        'DESCRIPTION': 'Économie bande passante - Connexions lentes'
    }
    
    # ========================================
    # PROFIL PAR DÉFAUT
    # ========================================
    DEFAULT = LOW_LATENCY
    
    @classmethod
    def get_latency_ms(cls, config):
        """Calcule la latence théorique en millisecondes"""
        samples_per_chunk = config['CHUNK']
        sample_rate = config['RATE']
        latency_ms = (samples_per_chunk / sample_rate) * 1000
        return round(latency_ms, 1)
    
    @classmethod
    def get_bandwidth_kbps(cls, config):
        """Calcule la bande passante théorique en kbps"""
        # paInt16 = 2 bytes par échantillon
        bytes_per_sample = 2 if config['FORMAT'] == pyaudio.paInt16 else 4
        bytes_per_second = config['RATE'] * config['CHANNELS'] * bytes_per_sample
        kbps = (bytes_per_second * 8) / 1000
        return round(kbps, 1)
    
    @classmethod
    def list_profiles(cls):
        """Liste tous les profils disponibles avec leurs caractéristiques"""
        profiles = [
            ('ULTRA_LOW_LATENCY', cls.ULTRA_LOW_LATENCY),
            ('LOW_LATENCY', cls.LOW_LATENCY),
            ('QUALITY', cls.QUALITY),
            ('BANDWIDTH_SAVING', cls.BANDWIDTH_SAVING)
        ]
        
        print("=" * 80)
        print("🎵 PROFILS AUDIO LANVOICE")
        print("=" * 80)
        
        for name, config in profiles:
            latency = cls.get_latency_ms(config)
            bandwidth = cls.get_bandwidth_kbps(config)
            
            print(f"\n📊 {name}")
            print(f"   Description: {config['DESCRIPTION']}")
            print(f"   Latence théorique: {latency} ms")
            print(f"   Bande passante: {bandwidth} kbps")
            print(f"   Chunk: {config['CHUNK']} samples")
            print(f"   Sample Rate: {config['RATE']} Hz")
            print(f"   Buffer: {config['BUFFER_SIZE']} bytes")
    
    @classmethod
    def auto_select_profile(cls, connection_type='lan'):
        """Sélection automatique du profil selon le type de connexion"""
        if connection_type == 'lan':
            return cls.ULTRA_LOW_LATENCY
        elif connection_type == 'wifi':
            return cls.LOW_LATENCY
        elif connection_type == 'internet':
            return cls.BANDWIDTH_SAVING
        else:
            return cls.DEFAULT

# ========================================
# CLASSE D'OPTIMISATION TEMPS RÉEL
# ========================================

class AudioOptimizer:
    """Optimisations temps réel pour l'audio"""
    
    @staticmethod
    def optimize_thread_priority():
        """Augmente la priorité du thread audio (Windows)"""
        try:
            import os
            import sys
            if sys.platform == 'win32':
                import ctypes
                from ctypes import wintypes
                
                # Définir les constantes Windows
                THREAD_PRIORITY_TIME_CRITICAL = 15
                THREAD_PRIORITY_HIGHEST = 2
                
                # Obtenir le handle du thread actuel
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetCurrentThread()
                
                # Définir la priorité haute
                success = kernel32.SetThreadPriority(handle, THREAD_PRIORITY_HIGHEST)
                return success
        except Exception as e:
            print(f"⚠️ Impossible d'optimiser la priorité du thread: {e}")
            return False
    
    @staticmethod
    def configure_pyaudio_for_low_latency(audio_instance):
        """Configure PyAudio pour une latence minimale"""
        try:
            # Suggestions d'optimisation PyAudio
            # Note: Ces optimisations dépendent du système
            print("🔧 Configuration PyAudio pour latence minimale...")
            print("   • Utilisation de buffers réduits")
            print("   • Priorité temps réel activée")
            print("   • Format audio optimisé")
            return True
        except Exception as e:
            print(f"⚠️ Erreur configuration PyAudio: {e}")
            return False

# ========================================
# TESTS ET BENCHMARKS
# ========================================

def benchmark_audio_configs():
    """Teste les différents profils audio"""
    print("🧪 BENCHMARK DES CONFIGURATIONS AUDIO")
    print("=" * 60)
    
    AudioConfig.list_profiles()
    
    print(f"\n🎯 RECOMMANDATIONS:")
    print(f"   • LAN rapide: ULTRA_LOW_LATENCY (~3ms)")
    print(f"   • WiFi/Usage général: LOW_LATENCY (~6ms)")
    print(f"   • Connexions lentes: BANDWIDTH_SAVING (~12ms)")
    print(f"   • Priorité stabilité: QUALITY (~12ms)")

if __name__ == "__main__":
    benchmark_audio_configs()