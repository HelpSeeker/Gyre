# Copyright (C) 2020-2024 HelpSeeker <AlmostSerious@protonmail.ch>
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

from gi.repository import Gtk, Gio, Handy

from gyre.container import BaseContainer
from gyre.interface.row import InputRow

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/window.ui")
class GyreWindow(Handy.ApplicationWindow):
    __gtype_name__ = "GyreWindow"

    add_button = Gtk.Template.Child("add_button")
    clean_button = Gtk.Template.Child("clean_button")
    menu_button = Gtk.Template.Child("menu_button")
    start_button = Gtk.Template.Child("start_button")
    stop_button = Gtk.Template.Child("stop_button")
    listbox = Gtk.Template.Child("listbox")

    listbox_window = Gtk.Template.Child("listbox_window")
    no_item_box = Gtk.Template.Child("no_item_box")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.builder = Gtk.Builder()
        self.builder.add_from_resource("/io/github/helpseeker/Gyre/menu/add.xml")
        self.builder.add_from_resource("/io/github/helpseeker/Gyre/menu/menu.xml")
        self.add_button.set_menu_model(self.builder.get_object("add-popover"))
        self.menu_button.set_menu_model(self.builder.get_object("menu-popover"))

        self.list = Gio.ListStore.new(BaseContainer)
        self.listbox.bind_model(self.list, InputRow, self.list, self)

        self.list.connect("items_changed", self.update_widgets)
        self.update_widgets()

    def update_widgets(self, *args):
        has_input = bool(self.listbox.get_children())

        # gray out download controls for empty list
        self.start_button.set_sensitive(has_input)
        self.stop_button.set_sensitive(has_input)

        # Hide either no_item_box or listbox
        self.no_item_box.set_no_show_all(has_input)
        self.no_item_box.set_visible(not has_input)
        self.listbox_window.set_no_show_all(not has_input)
        self.listbox_window.set_visible(has_input)

        # Highlight add button for empty list
        if not has_input:
            self.add_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        else:
            self.add_button.get_style_context().remove_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

        self.show_all()
