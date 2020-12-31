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

import os

from gi.repository import Gtk, Handy

from gyre.utils import translate_community_name
from gyre.container import create_container
from gyre.interface.widgets import FileChooserButton

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/add_url.ui")
class AddURLWindow(Handy.Window):
    __gtype_name__ = "AddURLWindow"

    back_button = Gtk.Template.Child("back_button")
    add_button = Gtk.Template.Child("add_button")
    url_entry = Gtk.Template.Child("url_entry")
    limit_spin_button = Gtk.Template.Child("limit_spin_button")

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.url = ""
        self.limit = 0

        self.limit_spin_button.set_adjustment(
            Gtk.Adjustment(
                value=0,
                lower=0,
                upper=99999,
                step_increment=1,
                page_increment=10,
            )
        )

        self.back_button.connect("clicked", lambda x: self.destroy())
        self.add_button.connect("clicked", self._on_add_clicked)
        self.url_entry.connect("notify::text", self._on_entry_changed)
        # TODO: Figure out whether to use notify::value or value-changed
        self.limit_spin_button.connect("value-changed", self._on_spin_button_changed)

    def _on_entry_changed(self, *args):
        self.url = self.url_entry.get_text()
        self.add_button.set_sensitive(self.url)

    def _on_spin_button_changed(self, *args):
        self.limit = self.limit_spin_button.get_value_as_int()

    def _on_add_clicked(self, *args):
        self.model.append(map_input(self.url, self.limit))
        self.destroy()


@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/add_item.ui")
class AddWindow(Handy.Window):
    __gtype_name__ = "AddWindow"

    back_button = Gtk.Template.Child("back_button")
    add_button = Gtk.Template.Child("add_button")
    box = Gtk.Template.Child("box")
    type_dropdown = Gtk.Template.Child("type_dropdown")
    entry_label = Gtk.Template.Child("entry_label")
    id_entry = Gtk.Template.Child("id_entry")
    community_dropdown = Gtk.Template.Child("community_dropdown")
    list_button = Gtk.Template.Child("placeholder")
    sort_dropdown = Gtk.Template.Child("sort_dropdown")
    limit_spin_button = Gtk.Template.Child("limit_spin_button")

    SUPPORTED_FORMATS = {
        "Coub": {
            "id": 0,
            "entry_label": "ID",
            "placeholder": "e.g. 1wtwnp",
            "need_id": True,
            "sort_list": [],
            "default_sort": -1,
        },
        "List": {
            "id": 1,
            "entry_label": "List Location",
            "placeholder": None,
            "need_id": True,
            "sort_list": [],
            "default_sort": -1,
        },
        "Channel": {
            "id": 2,
            "entry_label": "Channel",
            "placeholder": "e.g. spontaneous-coub",
            "need_id": True,
            "sort_list": [
                "Most Recent",
                "Most Liked",
                "Most Viewed",
                "Oldest",
                "Random",
            ],
            "default_sort": 0,
        },
        "Search": {
            "id": 3,
            "entry_label": "Term",
            "placeholder": "e.g. Kimetsu no Yaiba",
            "need_id": True,
            "sort_list": [
                "Relevance",
                "Top",
                "Views Count",
                "Most Recent",
            ],
            "default_sort": 0,
        },
        "Tag": {
            "id": 4,
            "entry_label": "Tag",
            "placeholder": "e.g. grandson",
            "need_id": True,
            "sort_list": [
                "Popular",
                "Top",
                "Views Count",
                "Fresh",
            ],
            "default_sort": 0,
        },
        "Community": {
            "id": 5,
            "entry_label": "Community",
            "placeholder": "e.g. science-technology",
            "need_id": True,
            "sort_list": [
                "Hot (Daily)",
                "Hot (Weekly)",
                "Hot (Monthly)",
                "Hot (Quarterly)",
                "Hot (Six Months)",
                "Rising",
                "Fresh",
                "Top",
                "Views Count",
                "Random",
            ],
            "default_sort": 2,
            "values": {
                "animals-pets": 0,
                "anime": 1,
                "art": 2,
                "cars": 3,
                "cartoons": 4,
                "celebrity": 5,
                "dance": 6,
                "fashion": 7,
                "gaming": 8,
                "mashup": 9,
                "movies": 10,
                "music": 11,
                "nature-travel": 12,
                "news": 13,
                "nsfw": 14,
                "science-technology": 15,
                "sports": 16,
            },
        },
        "Featured": {
            "id": 6,
            "entry_label": "No additional info required",
            "placeholder": None,
            "need_id": False,
            "sort_list": [
                "Recent",
                "Top of the Month",
                "Undervalued",
            ],
            "default_sort": 0,
        },
        "Coub of the Day": {
            "id": 7,
            "entry_label": "No additional info required",
            "placeholder": None,
            "need_id": False,
            "sort_list": [
                "Recent",
                "Top",
                "Views Count",
            ],
            "default_sort": 0,
        },
        "Story": {
            "id": 8,
            "entry_label": "ID",
            "placeholder": "e.g. 903045",
            "need_id": True,
            "sort_list": [],
            "default_sort": -1,
        },
        "Hot Section": {
            "id": 9,
            "entry_label": "No additional info required",
            "placeholder": None,
            "need_id": False,
            "sort_list": [
                "Hot (Daily)",
                "Hot (Weekly)",
                "Hot (Monthly)",
                "Hot (Quarterly)",
                "Hot (Six Months)",
                "Rising",
                "Fresh",
            ],
            "default_sort": 2,
        },
        "Random": {
            "id": 10,
            "entry_label": "No additional info required",
            "placeholder": None,
            "need_id": False,
            "sort_list": [
                "Popular",
                "Top",
            ],
            "default_sort": 0,
        },
    }

    def __init__(self, model, item=None):
        super().__init__()
        self.model = model
        self.item = item

        self.type = self.item.type if self.item else "Coub"
        self.id = self.item.id if self.item else ""
        self.sort = self.item.sort if self.item else ""
        self.limit = self.item.quantity if self.item else 0

        if self.item:
            self.add_button.set_label("Update")

        self.box.remove(self.list_button)
        self.list_button = FileChooserButton(
            label=None,
            title="Open Input List",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        self.list_button.set_no_show_all(True)
        self.box.add(self.list_button)
        self.box.reorder_child(self.list_button, 5)

        self.limit_spin_button.set_adjustment(
            Gtk.Adjustment(
                value=self.limit,
                lower=0,
                upper=99999,
                step_increment=1,
                page_increment=10,
            )
        )

        self.back_button.connect("clicked", lambda x: self.destroy())
        self.add_button.connect("clicked", self._on_add_clicked)
        self.type_dropdown.connect("notify::active", self._on_type_changed)
        self.id_entry.connect("notify::text", self._on_entry_changed)
        self.community_dropdown.connect("changed", self._on_community_changed)
        self.list_button.connect("clicked", self._on_list_button_clicked)
        self.sort_dropdown.connect("notify::active", self._on_sort_changed)
        self.limit_spin_button.connect("value-changed", self._on_spin_button_changed)

        # Disable add button until input was provided
        self.add_button.set_sensitive(False)

        # Populate dropdown lists
        for community in self.SUPPORTED_FORMATS["Community"]["values"]:
            self.community_dropdown.append_text(translate_community_name(community))
        for type in self.SUPPORTED_FORMATS:
            self.type_dropdown.append_text(type)

        self.type_dropdown.set_active(self.SUPPORTED_FORMATS[self.type]["id"])

    def _update_add_button(self):
        valid = bool(self.id) or not self.SUPPORTED_FORMATS[self.type]["need_id"]
        self.add_button.set_sensitive(valid)

    def _on_type_changed(self, *args):
        self.type = self.type_dropdown.get_active_text()

        self.entry_label.set_label(self.SUPPORTED_FORMATS[self.type]["entry_label"])

        if self.type == "List":
            self.id_entry.hide()
            self.community_dropdown.hide()
            self.list_button.show()

            # Don't set default file, unless ID is an existing path
            if self.id and os.path.isfile(self.id):
                self.list_button.label = self.id
        elif self.type == "Community":
            self.id_entry.hide()
            self.list_button.hide()
            self.community_dropdown.show()

            if self.id and self.id in self.SUPPORTED_FORMATS[self.type]["values"]:
                self.community_dropdown.set_active(self.SUPPORTED_FORMATS[self.type]["values"][self.id])
        else:
            self.list_button.hide()
            self.community_dropdown.hide()
            self.id_entry.show()
            self.id_entry.set_sensitive(self.SUPPORTED_FORMATS[self.type]["need_id"])
            self.id_entry.set_placeholder_text(self.SUPPORTED_FORMATS[self.type]["placeholder"])

            # Don't set entry text, if ID is a list path
            if self.id and not os.path.isfile(self.id):
                self.id_entry.set_text(self.id)

        self.sort_dropdown.remove_all()
        for sort in self.SUPPORTED_FORMATS[self.type]["sort_list"]:
            self.sort_dropdown.append_text(sort)
        if self.sort in self.SUPPORTED_FORMATS[self.type]["sort_list"]:
            self.sort_dropdown.set_active(self.SUPPORTED_FORMATS[self.type]["sort_list"].index(self.sort))
        else:
            self.sort_dropdown.set_active(self.SUPPORTED_FORMATS[self.type]["default_sort"])

        self.limit_spin_button.set_sensitive(self.type != "Coub")

        self._update_add_button()

    def _on_entry_changed(self, *args):
        self.id = self.id_entry.get_text()
        self._update_add_button()

    def _on_community_changed(self, dropdown):
        self.id = translate_community_name(dropdown.get_active_text(), direction="to_api")
        self._update_add_button()

    def _on_list_button_clicked(self, dialog_button):
        if dialog_button.run() == Gtk.ResponseType.ACCEPT:
            self.id = dialog_button.filename
            self._update_add_button()

    def _on_sort_changed(self, *args):
        self.sort = self.sort_dropdown.get_active_text()

    def _on_spin_button_changed(self, *args):
        self.limit = self.limit_spin_button.get_value_as_int()

    def _on_add_clicked(self, *args):
        # Switching types may preserve unnecessary ID or sort
        if not self.SUPPORTED_FORMATS[self.type]["need_id"]:
            self.id = ""
        if not self.SUPPORTED_FORMATS[self.type]["sort_list"]:
            self.sort = ""

        new = create_container(self.type, self.id, self.sort, self.limit)
        if self.item:
            pos = self.model.find(self.item)[1]
            self.model.splice(pos, 1, [new])
        else:
            self.model.append(new)

        self.destroy()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# TODO: Prevent wrong input at this stage (to show error in URL Window)

def map_input(url, quantity):
    sort_map = {
        "Channel": {
            "/coubs": None,
            "/reposts": None,
            "/stories": None,
        },
        "Search": {
            "/likes": "Top",
            "/views": "Views Count",
            "/fresh": "Most Recent",
            "/channels": None,
        },
        "Tag": {
            "/likes": "Top",
            "/views": "Views Count",
            "/fresh": "Fresh"
        },
        "Community": {
            "/rising": "Rising",
            "/fresh": "Fresh",
            "/top": "Top",
            "/views": "Views Count",
            "/random": "Random",
        },
        "Featured": {
            "/coubs/top_of_the_month": "Top of the Month",
            "/coubs/undervalued": "Undervalued",
            "/stories": None,
            "/channels": None,
        },
        "Hot Section": {
            "/rising": "Rising",
            "/fresh": "Fresh",
            "/hot": "Hot (Monthly)",
        },
        "Random": {
            "/top": "Top",
        },
    }

    # Shorten URL for easier parsing
    url = url.strip(" /").lstrip("htps:/")

    # Type detection
    if url.startswith("coub.com/view"):
        type = "Coub"
    elif url.startswith("coub.com/search"):
        type = "Search"
    elif url.startswith("coub.com/tags"):
        type = "Tag"
    elif url.startswith(("coub.com/community/featured", "coub.com/featured")):
        type = "Featured"
    elif url.startswith("coub.com/community/coub-of-the-day"):
        type = "Coub of the Day"
    elif url.startswith("coub.com/community"):
        type = "Community"
    elif url.startswith("coub.com/stories"):
        type = "Story"
    elif url.startswith("coub.com/random"):
        type = "Random"
    elif url in ["coub.com", "coub.com/rising", "coub.com/fresh", "coub.com/hot"]:
        type = "Hot Section"
    else:
        type = "Channel"

    # Sort detection
    sort = None
    if type in sort_map:
        for suffix in sort_map[type]:
            # Despite its name, this string isn't necessarily at the very end (e.g. searches)
            if suffix in url:
                sort = sort_map[type][suffix]
                url = url.replace(suffix, "")

    # ID detection
    if type in ["Featured", "Coub of the Day", "Hot Section", "Random"]:
        id = None
    elif type == "Coub":
        id = url.partition("coub.com/view/")[2]
    elif type == "Channel":
        id = url.partition("coub.com/")[2]
    elif type == "Search":
        id = url.partition("coub.com/search?q=")[2]
    elif type == "Tag":
        id = url.partition("coub.com/tags/")[2]
    elif type == "Community":
        id = url.partition("coub.com/community/")[2]
    elif type == "Story":
        id = url.partition("coub.com/stories/")[2]

    args = [type, id, sort, quantity]
    return create_container(*args)
