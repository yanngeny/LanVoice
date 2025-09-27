"""
Test du VU-mètre et du système de threshold
"""

import sys
import os
import time
import threading

# Ajouter le dossier src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    import numpy as np
    from client import VoiceClient
    
    def test_vu_meter():
        """Test du VU-mètre avec des données audio simulées"""
        print("🧪 Test du VU-mètre...")
        
        client = VoiceClient()
        
        # Callback pour afficher le niveau
        def level_callback(level):
            bars = "█" * int(level / 5)  # Barre visuelle
            print(f"\rNiveau: {level:5.1f}% |{bars:<20}|", end="", flush=True)
        
        # Callback pour afficher l'état VOX
        def vox_callback(active):
            status = "🔊 ACTIF" if active else "🔇 INACTIF"
            print(f" VOX: {status}")
        
        client.level_callback = level_callback
        client.vox_callback = vox_callback
        
        # Tester avec différents niveaux de threshold
        thresholds = [5, 15, 25]
        
        for threshold in thresholds:
            print(f"\n--- Test avec seuil {threshold}% ---")
            client.set_threshold(threshold)
            client.set_vox_enabled(True)
            
            # Simuler différents niveaux audio
            test_levels = [0, 10, 20, 30, 40, 20, 5, 0]
            
            for level in test_levels:
                # Simuler des données audio correspondant au niveau
                if level > 0:
                    # Créer un signal audio simulé
                    amplitude = int(32767 * (level / 100))
                    audio_data = np.random.randint(-amplitude, amplitude, 1024, dtype=np.int16).tobytes()
                else:
                    # Silence
                    audio_data = np.zeros(1024, dtype=np.int16).tobytes()
                
                # Calculer et afficher le niveau
                calculated_level = client.calculate_rms_level(audio_data)
                client.audio_level = calculated_level
                
                # Simuler la logique VOX
                should_transmit = client.should_transmit_audio()
                vox_active = calculated_level > threshold
                
                if level_callback:
                    level_callback(calculated_level)
                if vox_callback and vox_active != getattr(client, '_last_vox_state', False):
                    vox_callback(vox_active)
                    client._last_vox_state = vox_active
                
                time.sleep(0.5)
            
            print("\n" + "="*50)
        
        print("\n✅ Test du VU-mètre terminé")
        return True

    def test_threshold_logic():
        """Test de la logique de threshold"""
        print("\n🧪 Test de la logique de threshold...")
        
        client = VoiceClient()
        
        # Test mode manuel
        client.set_vox_enabled(False)
        client.recording = True
        assert client.should_transmit_audio() == True, "Mode manuel devrait transmettre quand recording=True"
        
        client.recording = False
        assert client.should_transmit_audio() == False, "Mode manuel ne devrait pas transmettre quand recording=False"
        
        # Test mode VOX
        client.set_vox_enabled(True)
        client.set_threshold(15)
        
        client.audio_level = 10
        assert client.should_transmit_audio() == False, "VOX ne devrait pas transmettre sous le seuil"
        
        client.audio_level = 20
        assert client.should_transmit_audio() == True, "VOX devrait transmettre au-dessus du seuil"
        
        print("✅ Logique de threshold OK")
        return True

    def main():
        """Lance les tests du VU-mètre et threshold"""
        print("=" * 50)
        print("🎚️ Test VU-mètre et Threshold")
        print("=" * 50)
        
        try:
            # Test de la logique
            if not test_threshold_logic():
                return False
            
            # Test visuel du VU-mètre
            print("\nAppuyez sur Entrée pour lancer le test visuel du VU-mètre...")
            input()
            
            if not test_vu_meter():
                return False
            
            print("\n🎉 Tous les tests sont passés!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erreur lors des tests: {e}")
            import traceback
            traceback.print_exc()
            return False

    if __name__ == "__main__":
        success = main()
        input("\nAppuyez sur Entrée pour continuer...")
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Dépendance manquante: {e}")
    print("Installez numpy avec: pip install numpy")
    input("Appuyez sur Entrée pour continuer...")
    sys.exit(1)