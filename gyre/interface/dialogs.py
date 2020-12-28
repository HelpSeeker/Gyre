# Copyright (C) 2020 HelpSeeker <AlmostSerious@protonmail.ch>
#
# This file is part of Gyre.
#
# Gyre is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gyre is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gyre.  If not, see <https://www.gnu.org/licenses/>.

from gi.repository import Gtk, Handy

from gyre.utils import get_error_log
from gyre.core.settings import Settings

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ProfileImporter(Gtk.FileChooserNative):

    def __init__(self, parent):
        super().__init__(
            title="Load Profile",
            action=Gtk.FileChooserAction.OPEN,
            modal=True,
            transient_for=parent,
        )


class ProfileExporter(Gtk.FileChooserNative):

    def __init__(self, parent):
        super().__init__(
            title="Save Profile",
            action=Gtk.FileChooserAction.SAVE,
            modal=True,
            transient_for=parent,
        )


class ErrorLogViewer(Gtk.MessageDialog):

    def __init__(self, parent):
        super().__init__(
            buttons=Gtk.ButtonsType.CLOSE,
            message_type=Gtk.MessageType.INFO,
            text="Unable to open error log",
            secondary_text="Using internal viewer instead",
            modal=True,
            transient_for=parent,
        )
        viewer = Gtk.ScrolledWindow(
            propagate_natural_height=True,
            propagate_natural_width=True,
            child=Gtk.TextView(
                buffer=Gtk.TextBuffer(text=get_error_log().read_text()),
                editable=False,
                cursor_visible=False,
            ),
        )
        self.get_message_area().add(viewer)
        self.show_all()


class MissingPathWarning(Gtk.MessageDialog):

    def __init__(self, parent):
        super().__init__(
            buttons=Gtk.ButtonsType.CLOSE,
            message_type=Gtk.MessageType.WARNING,
            text="No existing output location found",
            secondary_text="Please specify one before proceeding",
            modal=True,
            transient_for=parent,
        )
        chooser = Gtk.FileChooserButton(
            title="Choose Output Directory",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        chooser.connect("file-set", self._on_output_path_changed)
        self.get_message_area().add(chooser)
        self.show_all()

    @staticmethod
    def _on_output_path_changed(chooser):
        Settings.get_default().output_path = chooser.get_filename()


class CloseConfirmation(Gtk.MessageDialog):

    def __init__(self, parent):
        super().__init__(
            buttons=Gtk.ButtonsType.YES_NO,
            message_type=Gtk.MessageType.QUESTION,
            text="Do you really want to quit while a download is running?",
            modal=True,
            transient_for=parent,
        )


class ImportDisabledInfo(Gtk.MessageDialog):

    def __init__(self, parent):
        super().__init__(
            buttons=Gtk.ButtonsType.CLOSE,
            message_type=Gtk.MessageType.INFO,
            text="Import disabled",
            secondary_text="Please stop the running download before importing",
            modal=True,
            transient_for=parent,
        )


class NoConnectionError(Gtk.MessageDialog):

    def __init__(self, parent):
        super().__init__(
            buttons=Gtk.ButtonsType.CLOSE,
            message_type=Gtk.MessageType.ERROR,
            text="Unable to connect",
            secondary_text="Please check your connection and try again",
            modal=True,
            transient_for=parent,
        )


class InvalidSettingsError(Gtk.MessageDialog):

    def __init__(self, parent):
        super().__init__(
            buttons=Gtk.ButtonsType.CLOSE,
            message_type=Gtk.MessageType.ERROR,
            text="Invalid settings detected",
            secondary_text="Please open Preferences and resolve any warnings before continuing",
            modal=True,
            transient_for=parent,
        )


@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/welcome.ui")
class WelcomeScreen(Handy.Window):
    __gtype_name__ = "WelcomeScreen"

    chooser = Gtk.Template.Child("chooser")
    continue_button = Gtk.Template.Child("continue_button")

    def __init__(self):
        super().__init__()

        self.continue_button.set_sensitive(False)

        self.chooser.connect("file-set", self._file_set)
        self.continue_button.connect("clicked", self._button_clicked)

    def _file_set(self, chooser):
        Settings.get_default().output_path = chooser.get_filename()
        self.continue_button.set_sensitive(True)

    def _button_clicked(self, button):
        self.destroy()


@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/about.ui")
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = "AboutDialog"
