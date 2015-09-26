# emacs-mode: -*- python-*-
# -*- coding: utf-8 -*-
from consts import *
from _Framework.ButtonElement import ButtonElement # Class representing a button a the controller
from _Framework.ChannelStripComponent import * # Class attaching to the mixer of a given track
from _Framework.EncoderElement import EncoderElement
from _Framework.CompoundComponent import CompoundComponent # Base class for classes encompasing other components to form complex components
from _Framework.InputControlElement import * # Base class for all classes representing control elements on a controller
from _Framework.MixerComponent import MixerComponent # Class encompassing several channel strips to form a mixer
from _Framework.SliderElement import SliderElement # Class representing a slider on the controller
from SpecialChannelStripComponent import SpecialChannelStripComponent


class SpecialMixerComponent(MixerComponent):
    ' Special mixer class that uses return tracks alongside midi and audio tracks and allows to navigate sends and reset them'
    __module__ = __name__

    def __init__(self, num_tracks, num_returns, EQ, Filter):
        MixerComponent.__init__(self, num_tracks, num_returns, EQ, Filter)
        # SENDS
        self.sends_index = 0
        self.send_button_up = None
        self.send_button_down = None
        self.send_controls = []
        self.send_reset = []


    def tracks_to_use(self):
        return (self.song().visible_tracks) #+ self.song().return_tracks)



    def _create_strip(self):
        return SpecialChannelStripComponent()

    """                                 SENDS NAV CONFIG & RESET                                            """

    def set_resetsend_buttons(self, buttons):
        # SET BUTTONS FOR RESETTING SEND VALUES AND ADDING LISTENERS
        assert isinstance(buttons, tuple)
        assert (len(buttons) is 8)
        for button in buttons:
            assert isinstance(button, ButtonElement) or (button == None)
        for button in self.send_reset:
            if (button != None):
                button.remove_value_listener(self.reset_send)
        self.send_reset = []
        for button in buttons:
            if (button != None):
                button.add_value_listener(self.reset_send, identify_sender = True)
            self.send_reset.append(button)

    def reset_send(self, value, sender):
        # SET TO 0 THE SEND KNOB WE CONTROL NOW AT A TRACK
        assert (self.send_reset != None)
        assert isinstance(value, int)
        tracks = self.tracks_to_use()
        #returns = self.returns_to_use()
        if ((value is not 0) or (not sender.is_momentary())):
            if self.channel_strip(self.send_reset.index(sender))._send_controls[self.sends_index].mapped_parameter() != None:
                self.channel_strip(self.send_reset.index(sender))._send_controls[self.sends_index].mapped_parameter().value = 0
                for i in range(20000):
                    self.send_reset[self.send_reset.index(sender)].turn_on()
                self.send_reset[self.send_reset.index(sender)].turn_off()


    def _set_send_nav(self, send_up, send_down):
        # SET BUTTONS TO NAVIGATE THROUGH TRACKSENDS KNOBS
        if (send_up is not self.send_button_up):
            # do_update = True
            if (self.send_button_up != None):
                self.send_button_up.remove_value_listener(self._send_up_value)
            self.send_button_up = send_up
            if (self.send_button_up != None):
                self.send_button_up.add_value_listener(self._send_up_value)
        if (send_down is not self.send_button_down):
            if (self.send_button_down != None):
                self.send_button_down.remove_value_listener(self._send_down_value)
            self.send_button_down = send_down
            if (self.send_button_down != None):
                self.send_button_down.add_value_listener(self._send_down_value)

    # THE FOLLOWING TWO FUNCTIONS ARE CALLED WHEN THE SEND UP/DOWN BUTTONS ARE CALLED, IT UPDATES TO NEW SEND'S INDEX
    def _send_up_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self.send_button_up, ButtonElement)
        if value is 127 or not self.send_button_up.is_momentary():
            if self.sends_index == (len(self.song().return_tracks) - 1):
                self.sends_index = 0
            else:
                new_sends_index = self.sends_index + 1
                self.sends_index = new_sends_index
        self._update_send_index(self.sends_index)


    def _send_down_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self.send_button_down, ButtonElement)
        if value is 127 or not self.send_button_down.is_momentary():
            if self.sends_index == 0:
                self.sends_index = (len(self.song().return_tracks) - 1)
            else:
                new_sends_index = self.sends_index - 1
                self.sends_index = new_sends_index
        self._update_send_index(self.sends_index)

    # UPDATES THE CONTROL SENDS OF A TRACK
    def _update_send_index(self, sends_index):
        for index in range(8):
            self.send_controls = []
            strip = self.channel_strip(index)
            for i in range(12):
                self.send_controls.append(None)
            self.send_controls[sends_index] = EncoderElement(MIDI_CC_TYPE, CHANNEL, mixer_sendknob_cc[index], Live.MidiMap.MapMode.absolute)
            strip.set_send_controls(tuple(self.send_controls))


# local variables:
# tab-width: 4
