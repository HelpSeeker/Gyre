# Copyright (C) 2020-2021 HelpSeeker <AlmostSerious@protonmail.ch>
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

from gi.repository import Gtk, GLib

from gyre.utils import translate_community_name
from gyre.settings import Settings
from gyre.interface.add import AddWindow

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/row.ui")
class InputRow(Gtk.ListBoxRow):
    __gtype_name__ = "InputRow"

    main_label = Gtk.Template.Child("main_label")
    subtitle = Gtk.Template.Child("subtitle")
    edit_button = Gtk.Template.Child("edit_button")
    delete_button = Gtk.Template.Child("delete_button")
    progress_bar = Gtk.Template.Child("progress_bar")

    def __init__(self, item, model, window):
        super().__init__()

        self.item = item
        self.model = model
        self.window = window

        if self.item.id and self.item.type == "Community":
            item_id = translate_community_name(self.item.id)
        else:
            item_id = self.item.id

        self.main_label.set_label("".join([
            self.item.type,
            f": {item_id}" if item_id else "",
            f" (limit: {self.item.quantity})" if self.item.quantity else "",
        ]))
        self.subtitle.set_label(f"sorted by '{self.item.sort}'" if self.item.sort else "")

        self.edit_button.connect("clicked", self._on_edit)
        self.delete_button.connect("clicked", self._on_delete)
        self.item.connect("notify::status", lambda *args: GLib.idle_add(self._on_item_status_changed))
        self.item.connect("notify::page-progress", lambda *args: GLib.idle_add(self._on_progress_update))
        self.item.connect("notify::done", lambda *args: GLib.idle_add(self._on_progress_update))

    def set_editable(self, boolean):
        self.edit_button.set_sensitive(boolean)
        self.delete_button.set_sensitive(boolean)

    def _on_edit(self, *args):
        update_window = AddWindow(self.model, self.item)
        update_window.set_transient_for(self.window)
        update_window.show_all()

    def _on_delete(self, *args):
        self.model.remove(self.model.find(self.item)[1])

    def _on_progress_update(self, *args):
        if self.item.status == "Parsing" and self.item.pages:
            self.progress_bar.set_fraction(self.item.page_progress/self.item.pages)
        elif self.item.status == "Downloading" and self.item.count:
            self.progress_bar.set_fraction(self.item.done/self.item.count)
            self.progress_bar.set_text(" ".join([
                "Downloading coubs...",
                f"({self.item.done}/{self.item.count})",
                f"({self.item.exist} exist)" if self.item.exist else "",
                f"({self.item.invalid} errors)" if self.item.invalid else "",
            ]))
            if self.item.done == self.item.count:
                self.item.status = "Finished"

    def _on_item_status_changed(self, *args):
        self.progress_bar.set_sensitive(True)
        self.progress_bar.set_visible(self.item.status)
        if self.item.status == "Started":
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("Waiting to start...")
        elif self.item.status == "Parsing":
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("Fetching links...")
        elif self.item.status == "Waiting":
            if Settings.get_default().output_list:
                self.progress_bar.set_fraction(1)
                self.progress_bar.set_text("Done parsing!")
            else:
                self.progress_bar.set_fraction(0)
                self.progress_bar.set_text("Waiting to download...")
        elif self.item.status == "Downloading":
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("Downloading coubs...")
        elif self.item.status == "No new coubs":
            self.progress_bar.set_fraction(1)
            self.progress_bar.set_text("Finished! (no new coubs or limit exceeded)")
        elif self.item.status == "Finished":
            self.progress_bar.set_fraction(1)
            self.progress_bar.set_text(" ".join([
                "Finished!",
                f"({self.item.exist} exist)" if self.item.exist else "",
                f"({self.item.invalid} errors)" if self.item.invalid else "",
            ]))
        else:
            self.progress_bar.set_text(self.item.status)
            self.progress_bar.set_sensitive(False)
