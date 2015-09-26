# --== Decompile ==--



# 0: Song.Quantization.q_no_q,
# 1: Song.Quantization.q_8_bars,
# 2: Song.Quantization.q_4_bars,
# 3: Song.Quantization.q_2_bars,
# 4: Song.Quantization.q_bar,
# 5: Song.Quantization.q_half,
# 6: Song.Quantization.q_half_triplet,
# 7: Song.Quantization.q_quarter,
# 8: Song.Quantization.q_quarter_triplet,
# 9: Song.Quantization.q_eight,
# 10: Song.Quantization.q_eight_triplet,
# 11: Song.Quantization.q_sixtenth,
# 12: Song.Quantization.q_sixtenth_triplet,
# 13: Song.Quantization.q_thirtytwoth


import Live
from _Framework.ButtonElement import ButtonElement
from _Framework.TransportComponent import TransportComponent

class SpecialTransportComponent(TransportComponent):

    def __init__(self, parent):
        TransportComponent.__init__(self)
        self.__mainscript__ = parent
        self.tempo_up_button = None
        self.tempo_down_button = None
        self._quant_toggle_button = None

        for index in range(13):
            if self.__mainscript__.song().clip_trigger_quantization is Live.Song.Quantization.values[index]:
                self.quant_index = index


    def disconnect(self):
        TransportComponent.disconnect(self)
        return None


    def _set_tempo_buttons(self, tempo_down, tempo_up):
        if (tempo_down is not self.tempo_down_button):
            if (self.tempo_down_button != None):
                self.tempo_down_button.remove_value_listener(self._tempo_down_value)
            self.tempo_down_button = tempo_down
            if (self.tempo_down_button != None):
                self.tempo_down_button.add_value_listener(self._tempo_down_value)
        if (tempo_up is not self.tempo_up_button):
            if (self.tempo_up_button != None):
                self.tempo_up_button.remove_value_listener(self._tempo_up_value)
            self.tempo_up_button = tempo_up
            if (self.tempo_up_button != None):
                self.tempo_up_button.add_value_listener(self._tempo_up_value)


    def _tempo_down_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self.tempo_down_button, ButtonElement)
        if value is 127 or not self.tempo_down_button.is_momentary():
            self.song().tempo -= 1
            for i in range(1000):
                self.tempo_down_button.turn_on()
            self.tempo_down_button.turn_off()

    def _tempo_up_value(self, value):
        assert isinstance(value, int)
        assert isinstance(self.tempo_up_button, ButtonElement)
        if value is 127 or not self.tempo_up_button.is_momentary():
            self.song().tempo += 1
            for i in range(1000):
                self.tempo_up_button.turn_on()
            self.tempo_up_button.turn_off()



    def _set_quant_toggle_button(self, quant_button):
        if (self._quant_toggle_button is not quant_button):
            if self._quant_toggle_button != None:
                self._quant_toggle_button.remove_value_listener(self._quant_toggle_value)
            self._quant_toggle_button = quant_button
            if self._quant_toggle_button != None:
                self._quant_toggle_button.add_value_listener(self._quant_toggle_value)


    def _quant_toggle_value(self, value):
        if self._quant_toggle_button != None:
            assert(value in range(128)) or AssertionError
            if (value is 127):
                self._quant_toggle_button.turn_on()
                self.quant_index += 1
                if self.quant_index < 13:
                    if (Live.Song.Quantization.values[self.quant_index] == 6) or (Live.Song.Quantization.values[self.quant_index] == 8) or (Live.Song.Quantization.values[self.quant_index]== 10) or (Live.Song.Quantization.values[self.quant_index] == 12):
                        self.quant_index += 1
                else:
                    self.quant_index = 0
            self.__mainscript__.song().clip_trigger_quantization = Live.Song.Quantization.values[self.quant_index]
            self._quant_toggle_button.turn_off()






