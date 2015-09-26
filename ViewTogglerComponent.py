
import Live
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ButtonElement import ButtonElement

class ViewTogglerComponent(ControlSurfaceComponent):
    """ Component that can toggle the device chain- and clip view of a number of tracks """

    def __init__(self, num_tracks, parent):
        assert (num_tracks > 0) or AssertionError
        ControlSurfaceComponent.__init__(self)
        self.__main_script__ = parent
        self._num_tracks = num_tracks
        self._toggle_buttons = []
        self._device_left_button = None
        self._device_right_button = None
        self._ignore_track_selection = False
        self.application().view.add_is_view_visible_listener('Detail', self._on_detail_view_changed)
        self.application().view.add_is_view_visible_listener('Detail/Clip', self._on_views_changed)

    def disconnect(self):
        self.application().view.remove_is_view_visible_listener('Detail', self._on_detail_view_changed)
        self.application().view.remove_is_view_visible_listener('Detail/Clip', self._on_views_changed)
        if self._toggle_buttons != None:
            for button in self._toggle_buttons:
                if button !=None:
                    button.remove_value_listener(self._toggle_value)

            self._toggle_buttons = None

    def set_buttons(self, toggle_buttons):
        assert isinstance(toggle_buttons, tuple) and len(toggle_buttons) == self._num_tracks or AssertionError
        if (self._toggle_buttons != None):
            for button in self._toggle_buttons:
                if (button != None):
                    button.remove_value_listener(self._toggle_value)

        self._toggle_buttons = toggle_buttons
        if (self._toggle_buttons != None):
            for button in self._toggle_buttons:
                assert isinstance(button, ButtonElement) or AssertionError
                if (button != None):
                    button.add_value_listener(self._toggle_value, identify_sender=True)
        self.on_selected_track_changed()

    def on_selected_track_changed(self):
        self._update_buttons()

    def on_enabled_changed(self):
        self.update()

    def update(self):
        if self.is_enabled():
            self._update_buttons()
        else:
            if self._toggle_buttons != None:
                for button in self._toggle_buttons:
                    button.turn_off()

    def _on_detail_view_changed(self):
        self._update_buttons()

    def _on_views_changed(self):
        self._update_buttons()

    def _update_buttons(self):
        if self._toggle_buttons != None:
            tracks = self.song().visible_tracks
            trackoffset = self.__main_script__.session.track_offset()
            for index in range(self._num_tracks):
                if len(tracks) > index and tracks[index + trackoffset] == self.song().view.selected_track and self.application().view.is_view_visible('Detail'):
                    if self.application().view.is_view_visible('Detail/DeviceChain'):
                        if self._toggle_buttons[index] != None:
                            self._toggle_buttons[index].turn_on()
                    if self.application().view.is_view_visible('Detail/Clip'):
                        if self._toggle_buttons[index] != None:
                            self._toggle_buttons[index].turn_off()


    def _toggle_value(self, value, sender):
        assert (sender in self._toggle_buttons) or AssertionError
        assert isinstance(value, int)
        tracks = self.song().visible_tracks
        trackoffset = self.__main_script__.session.track_offset()
        index = list(self._toggle_buttons).index(sender)
        for i in range(self._num_tracks):
            self._toggle_buttons[i].turn_off()
        if value == 127 and len(tracks) > index:
            self._ignore_track_selection = True
            self.song().view.selected_track = tracks[index + trackoffset]
            self.application().view.show_view('Detail')
            self.application().view.show_view('Detail/Clip')
            track = self.song().view.selected_track
            if (track.devices is not None) and (len(tracks) > index):
                device_to_select = track.devices[0]
                self.song().view.select_device(device_to_select)
                self.__main_script__._device_component.set_device(device_to_select)
            self._ignore_track_selection = False
        elif value == 0 and len(tracks) > index:
            self._ignore_track_selection = True
            self.song().view.selected_track = tracks[index + trackoffset]
            self.application().view.show_view('Detail')
            self.application().view.show_view('Detail/DeviceChain')
            self._ignore_track_selection = False
        self._toggle_buttons[index].send_value(value)


    def set_device_nav_buttons(self, left_button, right_button):
        identify_sender = True
        if self._device_left_button != None:
            self._device_left_button.remove_value_listener(self._nav_value)
        self._device_left_button = left_button
        if self._device_left_button != None:
            self._device_left_button.add_value_listener(self._nav_value, identify_sender)
        if self._device_right_button != None:
            self._device_right_button.remove_value_listener(self._nav_value)
        self._device_right_button = right_button
        if self._device_right_button != None:
            self._device_right_button.add_value_listener(self._nav_value, identify_sender)



    def _nav_value(self, value, sender):
        assert ((sender != None) and (sender in (self._device_left_button, self._device_right_button)))
        if value == 127:
            if (sender == self._device_right_button):
                direction = Live.Application.Application.View.NavDirection.right
                self.application().view.scroll_view(direction, 'Detail/DeviceChain', True)
            elif (sender == self._device_left_button):
                direction = Live.Application.Application.View.NavDirection.left
                self.application().view.scroll_view(direction, 'Detail/DeviceChain', True)


