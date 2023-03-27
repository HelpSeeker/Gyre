# Copyright (C) 2020-2023 HelpSeeker <AlmostSerious@protonmail.ch>
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

import os

from gi.repository import Gtk, Pango


class FileChooserButton(Gtk.Button):

    def __init__(self, label=None, title=None, parent=None,
                 action=Gtk.FileChooserAction.OPEN):
        super().__init__()
        self.set_valign(Gtk.Align.CENTER)

        if action == Gtk.FileChooserAction.SELECT_FOLDER:
            image = Gtk.Image.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        else:
            image = Gtk.Image.new_from_icon_name("folder-documents-symbolic", Gtk.IconSize.BUTTON)

        self.set_image(image)
        self.label = label
        self.dialog = Gtk.FileChooserNative.new(
            title=title,
            parent=parent,
            action=action,
            accept_label=None,
            cancel_label=None,
        )
        self.dialog.connect("response", self._on_dialog_response)

    def run(self):
        return self.dialog.run()

    def _on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            self.label = self.filename

    @property
    def label(self):
        return self.get_label()

    @label.setter
    def label(self, value):
        if value:
            self.set_always_show_image(True)
            # extra whitespace since icons have barely any padding
            self.set_label(f" {os.path.basename(value)}")
        else:
            self.set_always_show_image(False)
            self.set_label("Browse...")

        # Dirty, but ellipsize mode and alignment don't stick
        # Hierarchy cheatsheet: Button -> Alignment -> Box -> [Image, Label]
        button_label = self.get_child().get_child().get_children()[1]
        button_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.get_child().set_halign(Gtk.Align.START)

    @property
    def title(self):
        return self.dialog.get_title()

    @title.setter
    def title(self, value):
        self.dialog.set_title(value)

    @property
    def parent(self):
        return self.dialog.get_transient_for()

    @parent.setter
    def parent(self, value):
        self.dialog.set_transient_for(value)

    @property
    def action(self):
        return self.dialog.get_action()

    @action.setter
    def action(self, value):
        self.dialog.set_action(value)

    @property
    def filename(self):
        return self.dialog.get_filename()

    @filename.setter
    def filename(self, value):
        self.dialog.set_filename(value)
