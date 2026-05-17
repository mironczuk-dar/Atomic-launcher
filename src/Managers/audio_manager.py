#IMPROTING FILES
from settings import *
from settings import AUDIO_DATA_PATH
from Tools.data_loading_tools import save_data
from pygame import mixer
from Tools.timer import Timer
from Manifests.music_manifest import STATE_MUSIC_TRACKS

#AUDIO MANAGER CLASS
class AudioManager:

    # CONSTRUCTOR
    def __init__(s, game):
        s.game = game

        # ----- MUSIC -----
        s.state_music = STATE_MUSIC_TRACKS

        # ----- MUSIC EFFECTS -----
        s.current_track = None
        s.last_track = None  # Caches the track to seamlessly restore it
        s.music_on = s.game.audio_data.get('music_on', True)
        s.music_volume = s.game.audio_data.get('music_volume', 1.0)

        # ----- SOUND EFFECTS -----
        s.test_sound = pygame.mixer.Sound(join(BASE_DIR, 'audio', 'Sounds', 'select_sound.wav'))
        s.sound_on = s.game.audio_data.get('sound_on', True)
        s.sound_volume = s.game.audio_data.get('sound_volume', 1.0)

    
    def update(s, delta_time):
        # The preview cooldown timer is now safely handled natively inside AudioOptionsTab
        pass


    # ----- MUSIC METHODS -----
    def pause_music(s):
        mixer.music.pause()

    def unpause_music(s):
        if s.music_on: 
            mixer.music.unpause()

    # ----- MUSIC METHODS -----
    def play_for_state(s, state_name):
        track_name = s.state_music.get(state_name)
        if track_name:
            s.play_music(track_name)

    def play_music(s, track_name):
        if not s.music_on:
            mixer.music.stop()
            s.current_track = None
            return

        if track_name != s.current_track:
            track_path = s.game.music_tracks.get(track_name)
            if track_path:
                mixer.music.load(track_path)
                mixer.music.set_volume(s.music_volume)
                mixer.music.play(-1)
                s.current_track = track_name
            else:
                mixer.music.stop()
                s.current_track = None

    def stop_music(s):
        mixer.music.stop()
        s.current_track = None

    def set_music_volume(s, volume):
        s.music_volume = volume
        mixer.music.set_volume(volume)
        s.game.audio_data['music_volume'] = volume
        save_data(s.game.audio_data, AUDIO_DATA_PATH)

    def toggle_music(s):
        s.music_on = not s.music_on
        s.game.audio_data['music_on'] = s.music_on
        save_data(s.game.audio_data, AUDIO_DATA_PATH)
        if not s.music_on:
            s.last_track = s.current_track # Save track before clearing it
            s.stop_music()
        else:
            # Safely resume the last cached track
            if hasattr(s, 'last_track') and s.last_track:
                s.play_music(s.last_track)
            elif hasattr(s.game, 'state_manager') and hasattr(s.game.state_manager, 'active_state'):
                s.play_for_state(s.game.state_manager.active_state)

    # ----- SOUND EFFECT METHODS -----
    def play_sound(s, sound):
        if not s.sound_on:
            return None
        
        snd = sound
        if snd:
            snd.set_volume(s.sound_volume)
            return snd.play() 
        else:
            print(f'[SOUND ERROR]: {snd}')
            return None

    def set_sound_volume(s, volume):
        s.sound_volume = volume
        s.game.audio_data['sound_volume'] = volume
        save_data(s.game.audio_data, AUDIO_DATA_PATH)

    def play_sound_preview(s):
        # This gets fired dynamically by AudioOptionsTab depending on UI cooldown logic
        s.play_sound(s.test_sound)

    def toggle_sound(s):
        s.sound_on = not s.sound_on
        s.game.audio_data['sound_on'] = s.sound_on
        save_data(s.game.audio_data, AUDIO_DATA_PATH)

        s.play_sound(s.game.select_sound)