#!/usr/bin/env python3
"""
LanVoice - Outil de Diagnostic Audio v2.0
Diagnostique les problèmes audio et propose des solutions
"""

import pyaudio
import socket
import platform
import psutil
import time
import numpy as np
from datetime import datetime

class LanVoiceDiagnostic:
    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
        
    def log_result(self, test_name, status, details="", solution=""):
        """Enregistre le résultat d'un test"""
        self.results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'solution': solution,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    def test_audio_devices(self):
        """Teste la disponibilité des périphériques audio"""
        print("🎵 Test des périphériques audio...")
        
        try:
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            
            if device_count == 0:
                self.log_result("Périphériques Audio", "❌ ERREUR", 
                              "Aucun périphérique audio détecté", 
                              "Vérifiez que vos pilotes audio sont installés")
                return False
                
            input_devices = []
            output_devices = []
            
            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    input_devices.append(info['name'])
                if info['maxOutputChannels'] > 0:
                    output_devices.append(info['name'])
            
            self.log_result("Périphériques Audio", "✅ OK", 
                          f"Entrée: {len(input_devices)}, Sortie: {len(output_devices)}")
            
            if len(input_devices) == 0:
                self.log_result("Microphone", "⚠️ ATTENTION", 
                              "Aucun microphone détecté", 
                              "Connectez un microphone ou vérifiez les permissions")
                
            if len(output_devices) == 0:
                self.log_result("Haut-parleurs", "⚠️ ATTENTION", 
                              "Aucun haut-parleur détecté", 
                              "Connectez des haut-parleurs ou un casque")
            
            p.terminate()
            return True
            
        except Exception as e:
            self.log_result("Périphériques Audio", "❌ ERREUR", 
                          f"Erreur PyAudio: {str(e)}", 
                          "Réinstallez PyAudio ou vérifiez les pilotes audio")
            return False
    
    def test_audio_latency(self):
        """Teste la latence audio avec différents buffers"""
        print("⏱️ Test de latence audio...")
        
        buffer_sizes = [256, 512, 1024, 2048, 4096]
        sample_rate = 44100
        
        try:
            p = pyaudio.PyAudio()
            
            for buffer_size in buffer_sizes:
                try:
                    # Test d'ouverture du stream
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        output=True,
                        frames_per_buffer=buffer_size
                    )
                    
                    # Calcul de la latence théorique
                    latency_ms = (buffer_size / sample_rate) * 1000
                    
                    stream.close()
                    
                    if latency_ms < 5:
                        status = "🟢 EXCELLENT"
                    elif latency_ms < 15:
                        status = "🟡 BON"
                    else:
                        status = "🔴 ÉLEVÉ"
                        
                    self.log_result(f"Latence Buffer {buffer_size}", status, 
                                  f"~{latency_ms:.1f}ms")
                    
                except Exception as e:
                    self.log_result(f"Latence Buffer {buffer_size}", "❌ ERREUR", 
                                  f"Impossible de tester: {str(e)}")
            
            p.terminate()
            
        except Exception as e:
            self.log_result("Test Latence", "❌ ERREUR", 
                          f"Erreur générale: {str(e)}", 
                          "Vérifiez l'installation de PyAudio")
    
    def test_network_connectivity(self):
        """Teste la connectivité réseau"""
        print("🌐 Test de connectivité réseau...")
        
        # Test de port disponible
        port = 12345
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            self.log_result("Port Réseau", "✅ OK", f"Port {port} disponible")
        except Exception as e:
            self.log_result("Port Réseau", "❌ ERREUR", 
                          f"Port {port} occupé: {str(e)}", 
                          "Fermez les applications utilisant ce port ou changez le port")
        
        # Test de latence réseau local
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', 80))
            end_time = time.time()
            sock.close()
            
            latency = (end_time - start_time) * 1000
            if latency < 1:
                status = "🟢 EXCELLENT"
            elif latency < 5:
                status = "🟡 BON"
            else:
                status = "🔴 ÉLEVÉ"
                
            self.log_result("Latence Réseau Local", status, f"~{latency:.1f}ms")
            
        except Exception as e:
            self.log_result("Latence Réseau", "⚠️ ATTENTION", 
                          "Impossible de tester la latence réseau")
    
    def test_system_performance(self):
        """Teste les performances système"""
        print("🖥️ Test des performances système...")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent < 50:
            cpu_status = "🟢 BON"
        elif cpu_percent < 80:
            cpu_status = "🟡 MODÉRÉ"
        else:
            cpu_status = "🔴 ÉLEVÉ"
            
        self.log_result("Utilisation CPU", cpu_status, f"{cpu_percent:.1f}%")
        
        # RAM
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        if ram_percent < 70:
            ram_status = "🟢 BON"
        elif ram_percent < 90:
            ram_status = "🟡 MODÉRÉ"
        else:
            ram_status = "🔴 ÉLEVÉ"
            
        self.log_result("Utilisation RAM", ram_status, 
                      f"{ram_percent:.1f}% ({memory.used // (1024**3)}GB/{memory.total // (1024**3)}GB)")
        
        # Système
        system_info = f"{platform.system()} {platform.release()}"
        self.log_result("Système", "ℹ️ INFO", system_info)
    
    def test_audio_quality(self):
        """Teste la qualité audio avec un signal de test"""
        print("🎼 Test de qualité audio...")
        
        try:
            p = pyaudio.PyAudio()
            
            # Génération d'un signal de test (440Hz - La)
            sample_rate = 44100
            duration = 1.0
            frequency = 440.0
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            test_signal = np.sin(2 * np.pi * frequency * t)
            test_signal = (test_signal * 32767).astype(np.int16)
            
            # Test de lecture
            try:
                stream_out = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True,
                    frames_per_buffer=1024
                )
                
                # Joue le signal de test (silencieusement pour le diagnostic)
                stream_out.write(test_signal.tobytes())
                stream_out.close()
                
                self.log_result("Test Audio Sortie", "✅ OK", 
                              "Signal de test généré avec succès")
                
            except Exception as e:
                self.log_result("Test Audio Sortie", "❌ ERREUR", 
                              f"Erreur de lecture: {str(e)}", 
                              "Vérifiez vos haut-parleurs ou casque")
            
            # Test d'enregistrement
            try:
                stream_in = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=1024
                )
                
                # Enregistre un court échantillon
                data = stream_in.read(1024)
                stream_in.close()
                
                # Analyse du signal
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data**2))
                
                if rms > 1000:
                    self.log_result("Test Audio Entrée", "✅ OK", 
                                  f"Signal détecté (RMS: {rms:.0f})")
                elif rms > 100:
                    self.log_result("Test Audio Entrée", "🟡 FAIBLE", 
                                  f"Signal faible (RMS: {rms:.0f})", 
                                  "Augmentez le volume du microphone")
                else:
                    self.log_result("Test Audio Entrée", "⚠️ AUCUN", 
                                  f"Pas de signal (RMS: {rms:.0f})", 
                                  "Vérifiez votre microphone et parlez plus fort")
                
            except Exception as e:
                self.log_result("Test Audio Entrée", "❌ ERREUR", 
                              f"Erreur d'enregistrement: {str(e)}", 
                              "Vérifiez votre microphone et les permissions")
            
            p.terminate()
            
        except Exception as e:
            self.log_result("Test Qualité Audio", "❌ ERREUR", 
                          f"Erreur générale: {str(e)}")
    
    def generate_report(self):
        """Génère un rapport de diagnostic complet"""
        print("\n" + "="*60)
        print("📋 RAPPORT DE DIAGNOSTIC LANVOICE")
        print("="*60)
        
        # Résumé des statuts
        total_tests = len(self.results)
        ok_count = sum(1 for r in self.results if "✅" in r['status'])
        error_count = sum(1 for r in self.results if "❌" in r['status'])
        warning_count = sum(1 for r in self.results if "⚠️" in r['status'])
        
        print(f"\n📊 RÉSUMÉ: {total_tests} tests effectués")
        print(f"   ✅ Réussis: {ok_count}")
        print(f"   ❌ Erreurs: {error_count}")
        print(f"   ⚠️ Avertissements: {warning_count}")
        
        # Détails des tests
        print(f"\n📝 DÉTAILS DES TESTS:")
        print("-" * 60)
        
        for result in self.results:
            print(f"[{result['timestamp']}] {result['test']}: {result['status']}")
            if result['details']:
                print(f"   📄 {result['details']}")
            if result['solution']:
                print(f"   💡 Solution: {result['solution']}")
            print()
        
        # Recommandations
        print("🔧 RECOMMANDATIONS:")
        print("-" * 60)
        
        if error_count == 0 and warning_count == 0:
            print("✅ Votre système est optimisé pour LanVoice!")
            print("   Tous les tests sont réussis, vous devriez avoir d'excellentes performances.")
        elif error_count > 0:
            print("❌ Des problèmes critiques ont été détectés:")
            print("   Corrigez les erreurs ci-dessus avant d'utiliser LanVoice.")
        else:
            print("🟡 Votre système fonctionne mais peut être optimisé:")
            print("   Consultez les solutions proposées pour améliorer les performances.")
        
        # Profil recommandé
        if error_count == 0:
            if ok_count >= total_tests * 0.9:
                print("\n🎯 PROFIL RECOMMANDÉ: Ultra Low Latency")
                print("   Votre système peut gérer la latence minimale (<3ms)")
            elif warning_count <= 2:
                print("\n🎯 PROFIL RECOMMANDÉ: Low Latency")
                print("   Bon compromis performance/stabilité (~6ms)")
            else:
                print("\n🎯 PROFIL RECOMMANDÉ: Quality")
                print("   Privilégie la stabilité et la qualité (~12ms)")
        else:
            print("\n🎯 PROFIL RECOMMANDÉ: Bandwidth Saving")
            print("   Mode conservateur jusqu'à résolution des problèmes")
        
        print("\n" + "="*60)
        print(f"Diagnostic terminé - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

def main():
    """Fonction principale du diagnostic"""
    print("🔍 LanVoice - Diagnostic Audio v2.0")
    print("Analyse de votre système pour optimiser les performances audio...\n")
    
    diagnostic = LanVoiceDiagnostic()
    
    try:
        # Exécution des tests
        diagnostic.test_system_performance()
        diagnostic.test_audio_devices()
        diagnostic.test_audio_latency()
        diagnostic.test_audio_quality()
        diagnostic.test_network_connectivity()
        
        # Génération du rapport
        diagnostic.generate_report()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Diagnostic interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue: {str(e)}")
        print("Veuillez signaler ce problème avec les détails ci-dessus.")

if __name__ == "__main__":
    main()