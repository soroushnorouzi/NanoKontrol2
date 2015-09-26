from __future__ import with_statement
import Live
import time # We will be using time functions for time-stamping our log file outputs

""" We are only using using some of the Framework classes them in this script (the rest are not listed here) """

from consts import *
from _Framework.ButtonElement import ButtonElement # Class representing a button a the controller
from _Framework.ButtonMatrixElement import ButtonMatrixElement # Class representing a button a the controller
from _Framework.ChannelStripComponent import * # Class attaching to the mixer of a given track
from _Framework.EncoderElement import EncoderElement
from _Framework.ClipSlotComponent import ClipSlotComponent # Class representing a ClipSlot within Live
from _Framework.CompoundComponent import CompoundComponent # Base class for classes encompasing other components to form complex components
from _Framework.ControlElement import ControlElement # Base class for all classes representing control elements on a controller
from _Framework.ControlSurface import ControlSurface # Central base class for scripts based on the new Framework
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent # Base class for all classes encapsulating functions in Live
from _Framework.InputControlElement import * # Base class for all classes representing control elements on a controller
from _Framework.MixerComponent import MixerComponent # Class encompassing several channel strips to form a mixer
from _Framework.SceneComponent import SceneComponent # Class representing a scene in Live
from _Framework.SessionComponent import SessionComponent # Class encompassing several scene to cover a defined section of Live's session
from _Framework.SliderElement import SliderElement # Class representing a slider on the controller
from _Framework.TransportComponent import TransportComponent # Class encapsulating all functions in Live's transport section
from _Framework.DeviceComponent import DeviceComponent

# SpecialMixerComponent and SpecialChannelStripComponent to get acess to the unfold function
from SpecialMixerComponent import SpecialMixerComponent
from SpecialChannelStripComponent import *
# Get access to view clip/device controls
from ViewTogglerComponent import ViewTogglerComponent
# Get access to tempo up/down buttons
from SpecialTransportComponent import SpecialTransportComponent


class NanoKontrolShift(ControlSurface):
    __module__ = __name__
    __doc__ = " NanoKontrolShift controller script "

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._suppress_session_highlight = True
        self._suppress_send_midi = True  # Turn off rebuild MIDI map until after we're done setting up
        self.log_message(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + "--------------= NanoKontrolShift log opened =--------------") # Writes message into Live's main log file. This is a ControlSurface method.
        with self.component_guard():
            # OBJECTS
            self.session = None #session object
            self.mixer = None #mixer object
            self.view = None #clip/device view object
            self.device = None #device object
            self.transport = None #transport object
            # MODES
            self._shift_button = None
            self._shift_button_pressed = False
            self._alt_button = None
            self._alt_button_pressed = False
            self._ctrl_button = None
            self._ctrl_button_pressed = False
            # INITIALIZE MIXER, SESSIONS
            self._setup_session_control()  # Setup the session object
            self._setup_mixer_control() # Setup the mixer object
            self._setup_view_control() # Setup the clip/view toggler
            self.session.set_mixer(self.mixer) # Bind mixer to session
            self._setup_device_control() # Setup the device object
            self._setup_transport_control() # Setup transport object
            self.set_device_component(self.device) # Bind device to control surface
            # SET INITIAL SESSION/MIXER AND MODIFIERS BUTTONS
            self._set_modifiers_buttons()
            self.__update_matrix()
            self.set_highlighting_session_component(self.session)

            for component in self.components:
                component.set_enabled(True)

        self._suppress_session_highlight = True
        self._suppress_send_midi = True # Turn rebuild back on, once we're done setting up

    def _setup_session_control(self):
        self.show_message("#################### SESSION: ON ##############################")
        is_momentary = True
        # CREATE SESSION, SET OFFSETS, BUTTONS NAVIGATION AND BUTTON MATRIX
        self.session = SessionComponent(num_tracks, num_scenes) #(num_tracks, num_scenes)
        self.session.set_offsets(0, 0)
        self.session.set_scene_bank_buttons(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_down), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_up))
        self.session.set_track_bank_buttons(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_right), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_left)) # (right_button, left_button) This moves the "red box" selection set left & right. We'll use the mixer track selection instead...

    def _setup_mixer_control(self):
        is_momentary = True
        #CREATE MIXER, SET OFFSET (SPECIALMIXERCOMPONENT USES SPECIALCHANNELSTRIP THAT ALLOWS US TO UNFOLD TRACKS WITH TRACK SELECT BUTTON)
        self.mixer = SpecialMixerComponent(num_tracks, 0, False, False) # 4 tracks, 2 returns, no EQ, no filters
        self.mixer.name = 'Mixer'
        self.mixer.set_track_offset(0) #Sets start point for mixer strip (offset from left)

    def _setup_view_control(self):
        # CREATES OBJECT SO WE CAN TOGGLE DEVICE/CLIP, LOCK DEVICE
        self.view = ViewTogglerComponent(num_tracks, self)

    def _setup_device_control(self):
        # CREATE DEVICE TO ASSIGN PARAMETERS BANK
        self.device = DeviceComponent()
        self.device.name = 'Device_Component'

    def _setup_transport_control(self):
        # CREATE TRANSPORT DEVICE
        self.transport = SpecialTransportComponent(self)


    def _on_selected_scene_changed(self):
        # ALLOWS TO GRAB THE FIRST DEVICE OF A SELECTED TRACK IF THERE'S ANY
        ControlSurface._on_selected_track_changed(self)
        track = self.song().view.selected_track
        if (track.devices is not None):
            self._ignore_track_selection = True
            device_to_select = track.devices[0]
            self.song().view.select_device(device_to_select)
            self._device_component.set_device(device_to_select)
        self._ignore_track_selection = False

    """                                 LED ON, OFF, FLASH WITH SESSION CLIPS                                             """

    # UPDATING BUTTONS FROM CLIP MATRIX IN NK AS SESSION MOVES
    def __update_matrix(self):
        for scene_index in range(num_scenes):
            scene = self.session.scene(scene_index)
            for track_index in range(num_tracks):
                clip_slot = scene.clip_slot(track_index)
                button = clip_slot._launch_button_value.subject
                value_to_send = -1
                if clip_slot._clip_slot != None:
                    if clip_slot.has_clip():
                        value_to_send = 127
                        if clip_slot._clip_slot.clip.is_triggered:
                            if clip_slot._clip_slot.clip.will_record_on_start:
                                value_to_send = clip_slot._triggered_to_record_value
                            else:
                                value_to_send = clip_slot._triggered_to_play_value
                        elif clip_slot._clip_slot.clip.is_playing:
                            if clip_slot._clip_slot.clip.is_recording:
                                value_to_send = 127
                                #########      CLIPS PLAYING WILL FLASH
                                for i in range(2000):
                                    if i % 50 == 0:
                                        button.send_value(127)
                                    else:
                                        button.send_value(0)
                            else:
                                for i in range(2000):
                                    if i % 50 == 0:
                                        button.send_value(127)
                                    else:
                                        button.send_value(0)
                    elif clip_slot._clip_slot.is_triggered:
                        if clip_slot._clip_slot.will_record_on_start:
                            value_to_send = clip_slot._triggered_to_record_value
                        else:
                            value_to_send = clip_slot._triggered_to_play_value
                    elif clip_slot._clip_slot.is_playing:
                        if clip_slot._clip_slot.is_recording:
                            value_to_send = clip_slot._recording_value
                        else:
                            value_to_send = clip_slot._started_value
                    elif clip_slot._clip_slot.controls_other_clips:
                        value_to_send = 0
                if value_to_send in range(128):
                    button.send_value(value_to_send)
                else:
                    button.turn_off()



    """                                 MODIFIERS, MODES, KEYS CONFIG                                             """

    #MODES ARE HERE: INITIALIZATIONS, DISCONNECTS BUTTONS, SLIDERS, ENCODERS
    def _clear_controls(self):
        # TURNING OFF ALL LEDS IN MATRIX
        self._turn_off_matrix()
        # SESSION
        resetsend_controls = []
        self.mixer.send_controls = []
        for scene_index in range(num_scenes):
            scene = self.session.scene(scene_index)
            scene.set_launch_button(None)
            for track_index in range(num_tracks):
                clip_slot = scene.clip_slot(track_index)
                clip_slot.set_launch_button(None)
        self.session.set_stop_track_clip_buttons(None)
        self.session.set_stop_all_clips_button(None)
            # REMOVE LISTENER TO SESSION MOVES
        if self.session.offset_has_listener(self.__update_matrix):
            self.session.remove_offset_listener(self.__update_matrix)
        self.session.set_stop_all_clips_button(None)
        # MIXER
        self.mixer._set_send_nav(None, None)
        for track_index in range(num_tracks):
            strip = self.mixer.channel_strip(track_index)
            strip.set_solo_button(None)
            strip.set_mute_button(None)
            strip.set_arm_button(None)
            resetsend_controls.append(None)
            strip.set_select_button(None)
            for i in range(12):
                self.mixer.send_controls.append(None)
            strip.set_send_controls(tuple(self.mixer.send_controls))
        self.mixer.set_resetsend_buttons(tuple(resetsend_controls))
        # VIEW
        self.view.set_device_nav_buttons(None, None)
        detailclip_view_controls = []
        for track_index in range(num_tracks):
            detailclip_view_controls.append(None)
        self.view.set_buttons(tuple(detailclip_view_controls))
        # DEVICE PARAMETERS
        device_param_controls = []
        self.device.set_parameter_controls(tuple(device_param_controls))
        self.device.set_on_off_button(None)
        self.device.set_lock_button(None)
        # TRANSPORT
        self.transport.set_stop_button(None)
        self.transport.set_play_button(None)
        self.transport.set_record_button(None)
        self.transport._set_quant_toggle_button(None)
        self.transport.set_metronome_button(None)
        self.transport._set_tempo_buttons(None, None)

        self.log_message("Controls Cleared")



    def _set_initial_mode(self):
        is_momentary = True
        ### MIXER
        self.mixer._set_send_nav(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, send_up), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, send_down))
        for index in range(num_tracks):
            strip = self.mixer.channel_strip(index)
            strip.name = 'Mixer_ChannelStrip_' + str(index)
            self.mixer._update_send_index(self.mixer.sends_index)
            strip.set_volume_control(SliderElement(MIDI_CC_TYPE, CHANNEL, mixer_volumefader_cc[index]))
            self.mixer.send_controls[self.mixer.sends_index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, mixer_sendknob_cc[index], Live.MidiMap.MapMode.absolute)
            strip.set_send_controls(tuple(self.mixer.send_controls))
            strip._invert_mute_feedback = True
        ### SESSION - CLIP LAUNCH BUTTONS
        launch_ctrl = 0
        for scene_index in range(num_scenes):
            scene = self.session.scene(scene_index)
            scene.name = 'Scene_' + str(scene_index)
            button_row = []
            scene.set_triggered_value(2)
            for track_index in range(num_tracks):
                button = ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_cliplaunch_cc[launch_ctrl])
                button_row.append(button)
                launch_ctrl = launch_ctrl + 1
                button.name = str(track_index) + '_Clip_' + str(scene_index) + '_Button'
                button_row.append(button)
                clip_slot = scene.clip_slot(track_index)
                clip_slot.name = str(track_index) + '_Clip_Slot_' + str(scene_index)
                clip_slot.set_launch_button(button)
        self.session.selected_scene().name = 'Selected_Scene'
        if not self.session.offset_has_listener(self.__update_matrix):
            self.session.add_offset_listener(self.__update_matrix)
        self.__update_matrix()
        self.mixer._update_send_index(self.mixer.sends_index)


    def _set_shift_mode(self):
        is_momentary = True
        self.mixer._set_send_nav(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, send_up), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, send_down))
        ### SET ARM, SOLO, MUTE
        for index in range(num_tracks):
            strip = self.mixer.channel_strip(index)
            strip.set_send_controls(tuple(self.mixer.send_controls))
            strip.set_solo_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, track_solo_cc[index]))
            strip.set_mute_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, track_mute_cc[index]))
            strip.set_arm_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, track_arm_cc[index]))
            for i in range(12):
                self.mixer.send_controls.append(None)
            self.mixer.send_controls[self.mixer.sends_index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, mixer_sendknob_cc[index], Live.MidiMap.MapMode.absolute)
            strip.set_send_controls(tuple(self.mixer.send_controls))
            strip._invert_mute_feedback = True
        self.mixer._update_send_index(self.mixer.sends_index)


    def _set_alt_mode(self):
        is_momentary = True
        self.mixer._set_send_nav(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, send_up), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, send_down))
        stop_track_controls = []
        resetsend_controls = []
        button = None
        buttons = None
        # SET SESSION TRACKSTOP, TRACK SELECT, RESET SEND KNOB
        for index in range(num_tracks):
            strip = self.mixer.channel_strip(index)
            strip.set_select_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, track_select_cc[index]))
            button = ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, stop_track_cc[index])
            stop_track_controls.append(button)
            buttons = ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, track_resetsend_cc[index])
            resetsend_controls.append(buttons)
        self.session.set_stop_track_clip_buttons(tuple(stop_track_controls))
        self.mixer.set_resetsend_buttons(tuple(resetsend_controls))
        self.mixer._update_send_index(self.mixer.sends_index)


    def _set_ctrl_mode(self):
        # CLIP/DEVICE VIEW TOGGLE
        is_momentary = True
        self.view.set_device_nav_buttons(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, device_left_cc), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, device_right_cc))
        button = None
        detailclip_view_controls = []
        for index in range(num_tracks):
            button = ButtonElement(not is_momentary, MIDI_CC_TYPE, CHANNEL, detailclip_view_cc[index])
            detailclip_view_controls.append(button)
        self.view.set_buttons(tuple(detailclip_view_controls))
        # DEVICE ON/OFF, LOCK AND PARAMETERS
        device_param_controls = []
        onoff_control = ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, onoff_device_cc)
        setlock_control = ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, lock_device_cc)
        for index in range(num_tracks):
            knob = None
            knob = EncoderElement(MIDI_CC_TYPE, CHANNEL, device_param_cc[index], Live.MidiMap.MapMode.absolute)
            device_param_controls.append(knob)
        if None not in device_param_controls:
            self.device.set_parameter_controls(tuple(device_param_controls))
        self.device.set_on_off_button(onoff_control)
        self.device.set_lock_button(setlock_control)
        # TRANSPORT
        self.transport.set_stop_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, transport_stop_cc))
        self.transport.set_play_button(ButtonElement(not is_momentary, MIDI_CC_TYPE, CHANNEL, transport_play_cc))
        self.transport.set_record_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, transport_record_cc))
        self.transport._set_quant_toggle_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, transport_quantization_cc))
        self.transport.set_metronome_button(ButtonElement(not is_momentary, MIDI_CC_TYPE, CHANNEL, transport_metronome_cc))
        self.transport._set_tempo_buttons(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, transport_tempodown_cc), ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, transport_tempoup_cc))
        # SESSION STOP ALL CLIPS AND SCENE LAUNCH
        self.session.set_stop_all_clips_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_stopall_cc))
        for index in range(num_scenes):
            self.session.scene(index).set_launch_button(ButtonElement(is_momentary, MIDI_CC_TYPE, CHANNEL, session_scenelaunch_cc[index]))

    def _set_modifiers_buttons(self):
        is_momentary = True
        self._shift_button = ButtonElement(not is_momentary, MIDI_CC_TYPE, CHANNEL, shift_mod)
        self._alt_button = ButtonElement(not is_momentary, MIDI_CC_TYPE, CHANNEL, alt_mod)
        self._ctrl_button = ButtonElement(not is_momentary, MIDI_CC_TYPE, CHANNEL, ctrl_mod)

        if (self._shift_button != None):
            self._shift_button.add_value_listener(self._shift_value)

        if (self._alt_button != None):
            self._alt_button.add_value_listener(self._alt_value)

        if (self._ctrl_button != None):
            self._ctrl_button.add_value_listener(self._ctrl_value)
        #INIT NORMAL MODE
        self._manage_modes(0)

    # MODIFIERS LISTENERS FUNCS ARE HERE
    def _shift_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self._shift_button, ButtonElement)
        if value == 127:
            if self._shift_button_pressed is False:
                self._unpress_modes()
                self._shift_button_pressed = True
                self._manage_modes(1)
            elif self._shift_button_pressed is True:
                self._manage_modes(0)
                self._unpress_modes()

    def _alt_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self._alt_button, ButtonElement)
        if value == 127:
            if self._alt_button_pressed is False:
                self._unpress_modes()
                self._alt_button_pressed = True
                self._manage_modes(2)
            elif self._alt_button_pressed is True:
                self._manage_modes(0)
                self._unpress_modes()

    def _ctrl_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self._ctrl_button, ButtonElement)
        if value == 127:
            if self._ctrl_button_pressed is False:
                self._unpress_modes()
                self._ctrl_button_pressed = True
                self._manage_modes(3)
            elif self._ctrl_button_pressed is True:
                self._manage_modes(0)
                self._unpress_modes()

    def _manage_modes(self, mode_index):
        if mode_index == 0:
            self._clear_controls()
            self._set_initial_mode()
            self._shift_button.turn_on()
            self._alt_button.turn_on()
            self._ctrl_button.turn_on()
            self.log_message("NORMAL ON")
        elif mode_index == 1:
            self._clear_controls()
            self._set_shift_mode()
            self._shift_button.turn_on()
            self._alt_button.turn_off()
            self._ctrl_button.turn_off()
            self.log_message("SHIFT ON")
        elif mode_index == 2:
            self._clear_controls()
            self._set_alt_mode()
            self._alt_button.turn_on()
            self._shift_button.turn_off()
            self._ctrl_button.turn_off()
            self.log_message("ALT ON")
        elif mode_index == 3:
            self._clear_controls()
            self._set_ctrl_mode()
            self._ctrl_button.turn_on()
            self._shift_button.turn_off()
            self._alt_button.turn_off()
            self.log_message("CTRL ON")

    def _unpress_modes(self):
        self._shift_button_pressed = False
        self._alt_button_pressed = False
        self._ctrl_button_pressed = False

    def _turn_off_matrix(self):
        for index in range(24):
            self._send_midi(tuple([176,index+16,0]))

    def disconnect(self):
        """clean things up on disconnect"""
        self.log_message(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + "--------------= NanoKontrolShift log closed =--------------") #Create entry in log file
        self._clear_controls()
        self.session = None
        self.mixer = None
        self.view = None
        self.device = None
        self.transport = None
        # MODES
        self._shift_button = None
        self._alt_button = None
        self._ctrl_button = None
        # SENDS
        self.send_button_up = None
        self.send_button_down = None
        self.send_controls = []
        self.send_reset = []

        self.set_device_component(None)
        ControlSurface.disconnect(self)
        return None
