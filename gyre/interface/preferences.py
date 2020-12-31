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

import pathlib

from gi.repository import Gtk, Gio, Handy

from gyre.settings import Settings
from gyre.interface.widgets import FileChooserButton

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@Gtk.Template(resource_path="/io/github/helpseeker/Gyre/ui/preferences.ui")
class PreferenceWindow(Handy.PreferencesWindow):
    __gtype_name__ = "PreferenceWindow"

    ### Output

    # Location
    output_action_row = Gtk.Template.Child("output_action_row")
    container_row = Gtk.Template.Child("container_row")
    name_entry = Gtk.Template.Child("name_entry")
    overwrite_switch = Gtk.Template.Child("overwrite_switch")

    # Length
    loop_spin_button = Gtk.Template.Child("loop_spin_button")
    duration_entry = Gtk.Template.Child("duration_entry")

    # Streams
    keep_switch = Gtk.Template.Child("keep_switch")

    ### Quality

    # Video
    video_row = Gtk.Template.Child("video_row")
    video_switch = Gtk.Template.Child("video_switch")
    resolution_row = Gtk.Template.Child("resolution_row")
    max_res_row = Gtk.Template.Child("max_res_row")
    min_res_row = Gtk.Template.Child("min_res_row")

    # Audio
    audio_row = Gtk.Template.Child("audio_row")
    audio_switch = Gtk.Template.Child("audio_switch")
    audio_quality_row = Gtk.Template.Child("audio_quality_row")

    # Special
    share_switch = Gtk.Template.Child("share_switch")

    ### Download

    # Network
    connections_spin_button = Gtk.Template.Child("connections_spin_button")
    retries_spin_button = Gtk.Template.Child("retries_spin_button")

    # Limits and Filters
    quantity_spin_button = Gtk.Template.Child("quantity_spin_button")
    recoubs_row = Gtk.Template.Child("recoubs_row")

    ### Misc

    archive_row = Gtk.Template.Child("archive_row")
    archive_action_row = Gtk.Template.Child("archive_action_row")
    output_list_row = Gtk.Template.Child("output_list_row")
    output_list_action_row = Gtk.Template.Child("output_list_action_row")
    json_row = Gtk.Template.Child("json_row")
    json_action_row = Gtk.Template.Child("json_action_row")

    def __init__(self):
        super().__init__()

        self.settings = Settings.get_default()
        self._prepare_widgets()

    def _prepare_widgets(self):

        self._prepare_output_widgets()
        self._prepare_quality_widgets()
        self._prepare_download_widgets()
        self._prepare_misc_widgets()

    def _prepare_output_widgets(self):
        # Output Path
        output_button = FileChooserButton(
            label=self.settings.output_path,
            title="Choose Output Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        output_button.connect("clicked", self._on_output_button_clicked)
        self.output_action_row.add(output_button)

        # Container
        liststore = Gio.ListStore.new(Handy.ValueObject)
        for ext in ["mkv", "mp4", "asf", "avi", "flv", "f4v", "mov"]:
            liststore.append(Handy.ValueObject.new(ext))

        self.container_row.bind_name_model(liststore, Handy.ValueObject.dup_string)
        self.container_row.set_selected_index(self.settings.file_extension)
        self.container_row.connect("notify::selected-index", self._on_container_changed)

        # Name Template
        self.name_entry.set_text(self.settings.name_template)
        self.name_entry.connect("notify::text", self._on_name_template_changed)

        # Overwrite
        self.overwrite_switch.set_active(self.settings.overwrite)
        self.overwrite_switch.connect("notify::active", self._on_overwrite_changed)

        # Loop Limit
        self.loop_spin_button.set_adjustment(
            Gtk.Adjustment(
                value=self.settings.loop_limit,
                lower=1,
                upper=99999,
                step_increment=1,
                page_increment=10,
            )
        )
        self.loop_spin_button.connect("notify::value", self._on_loop_limit_changed)

        # Duration Limit
        # TODO: Create a better widget for duration (maybe 4 vertical spin buttons?)
        self.duration_entry.set_text(self.settings.duration_limit)
        self.duration_entry.connect("notify::text", self._on_duration_limit_changed)

        # Keep Streams
        self.keep_switch.set_active(self.settings.keep_streams)
        self.keep_switch.connect("notify::active", self._on_keep_streams_changed)

    def _prepare_quality_widgets(self):
        # Download Video
        self.video_switch.set_active(self.settings.download_video)
        self.video_switch.connect("notify::active", self._on_video_switch_changed)

        # Video Resolution
        liststore = Gio.ListStore.new(Handy.ValueObject)
        liststore.append(Handy.ValueObject.new("Lowest"))
        liststore.append(Handy.ValueObject.new("Highest"))

        self.resolution_row.bind_name_model(liststore, Handy.ValueObject.dup_string)
        # Worst -> 0, Best -> -1
        self.resolution_row.set_selected_index(self.settings.video_resolution*-1)
        self.resolution_row.connect("notify::selected-index", self._on_video_resolution_changed)

        # Max Video Resolution
        liststore = Gio.ListStore.new(Handy.ValueObject)
        for res in ["640x480", "1280x960", "1600x1200"]:
            liststore.append(Handy.ValueObject.new(res))

        self.max_res_row.bind_name_model(liststore, Handy.ValueObject.dup_string)
        self.max_res_row.set_selected_index(self.settings.max_video_resolution)
        self.max_res_row.connect("notify::selected-index", self._on_max_video_resolution_changed)

        # Min Video Resolution
        self.min_res_row.bind_name_model(liststore, Handy.ValueObject.dup_string)
        self.min_res_row.set_selected_index(self.settings.min_video_resolution)
        self.min_res_row.connect("notify::selected-index", self._on_min_video_resolution_changed)

        # Download Audio
        self.audio_switch.set_active(self.settings.download_audio)
        self.audio_switch.connect("notify::active", self._on_audio_switch_changed)

        # Audio Quality
        liststore = Gio.ListStore.new(Handy.ValueObject)
        liststore.append(Handy.ValueObject.new("Worst"))
        liststore.append(Handy.ValueObject.new("Best"))

        self.audio_quality_row.bind_name_model(liststore, Handy.ValueObject.dup_string)
        # Worst -> 0, Best -> -1
        self.audio_quality_row.set_selected_index(self.settings.audio_quality*-1)
        self.audio_quality_row.connect("notify::selected-index", self._on_audio_quality_changed)

        # Download 'share' version
        self.share_switch.set_active(self.settings.download_share_version)
        self.share_switch.connect("notify::active", self._on_share_switch_changed)

        self._update_quality_widgets()

    def _prepare_download_widgets(self):
        # Connections
        self.connections_spin_button.set_adjustment(
            Gtk.Adjustment(
                value=self.settings.connections,
                lower=1,
                upper=1000,
                step_increment=1,
                page_increment=10,
            )
        )
        self.connections_spin_button.connect("notify::value", self._on_connections_changed)

        # Retries
        self.retries_spin_button.set_adjustment(
            Gtk.Adjustment(
                value=self.settings.retry_attempts,
                lower=-1,
                upper=99999,
                step_increment=1,
                page_increment=10,
            )
        )
        self.retries_spin_button.connect("notify::value", self._on_retries_changed)

        # Quantity
        self.quantity_spin_button.set_adjustment(
            Gtk.Adjustment(
                value=self.settings.quantity_limit,
                lower=0,
                upper=99999,
                step_increment=1,
                page_increment=10,
            )
        )
        self.quantity_spin_button.connect("notify::value", self._on_quantity_changed)

        # Recoubs
        liststore = Gio.ListStore.new(Handy.ValueObject)
        for mode in ["No Recoubs", "With Recoubs", "Only Recoubs"]:
            liststore.append(Handy.ValueObject.new(mode))

        self.recoubs_row.bind_name_model(liststore, Handy.ValueObject.dup_string)
        self.recoubs_row.set_selected_index(self.settings.download_recoubs)
        self.recoubs_row.connect('notify::selected-index', self._on_recoubs_download_changed)

    def _prepare_misc_widgets(self):
        # Archive
        self.archive_row.set_expanded(self.settings.archive)
        self.archive_row.set_enable_expansion(self.settings.archive)
        self.archive_row.connect("notify::enable-expansion", self._on_archive_changed)

        archive_button = FileChooserButton(
            label=self.settings.archive_path,
            title="Save Archive File",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        archive_button.connect("clicked", self._on_archive_path_button_clicked)
        self.archive_action_row.add(archive_button)

        # Output List
        self.output_list_row.set_expanded(self.settings.output_list)
        self.output_list_row.set_enable_expansion(self.settings.output_list)
        self.output_list_row.connect("notify::enable-expansion", self._on_output_list_changed)

        output_list_button = FileChooserButton(
            label=self.settings.output_list_path,
            title="Save Link List",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        output_list_button.connect("clicked", self._on_output_list_path_button_clicked)
        self.output_list_action_row.add(output_list_button)

        # Info JSON
        self.json_row.set_expanded(self.settings.info_json)
        self.json_row.set_enable_expansion(self.settings.info_json)
        self.json_row.connect("notify::enable-expansion", self._on_info_json_changed)

        json_button = FileChooserButton(
            label=self.settings.info_json_path,
            title="Save Info JSON",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        json_button.connect("clicked", self._on_json_path_button_clicked)
        self.json_action_row.add(json_button)

    def _update_quality_widgets(self):
        # Video download
        video = self.settings.download_video and not self.settings.download_share_version
        self.resolution_row.set_sensitive(video)
        self.max_res_row.set_sensitive(video)
        self.min_res_row.set_sensitive(video)

        if self.settings.max_video_resolution < self.settings.min_video_resolution:
            # Unfortunately these icons are massive (32x32)
            # Fortunately libhandy devs aren't happy with it either and want to redesign it
            # Unfortunately we have to wait until that happens
            self.max_res_row.set_icon_name("dialog-warning-symbolic")
            self.min_res_row.set_icon_name("dialog-warning-symbolic")
            self.max_res_row.set_subtitle("Max. resolution larger than min. resolution")
            self.min_res_row.set_subtitle("Max. resolution larger than min. resolution")
        else:
            self.max_res_row.set_icon_name("")
            self.min_res_row.set_icon_name("")
            self.max_res_row.set_subtitle("Limit max. resolution considered for download")
            self.min_res_row.set_subtitle("Limit min. resolution considered for download")

        # Audio download
        audio = self.settings.download_audio and not self.settings.download_share_version
        self.audio_quality_row.set_sensitive(audio)

        # Share download
        self.video_row.set_sensitive(not self.settings.download_share_version)
        self.audio_row.set_sensitive(not self.settings.download_share_version)

    def _on_archive_path_button_clicked(self, dialog_button):
        if dialog_button.run() == Gtk.ResponseType.ACCEPT:
            self.settings.archive_path = dialog_button.filename

    def _on_output_list_path_button_clicked(self, dialog_button):
        if dialog_button.run() == Gtk.ResponseType.ACCEPT:
            self.settings.output_list_path = dialog_button.filename

    def _on_json_path_button_clicked(self, dialog_button):
        if dialog_button.run() == Gtk.ResponseType.ACCEPT:
            self.settings.info_json_path = dialog_button.filename

    def _on_output_button_clicked(self, dialog_button):
        if dialog_button.run() == Gtk.ResponseType.ACCEPT:
            self.settings.output_path = dialog_button.filename

    def _on_container_changed(self, combo_row, prop_name):
        self.settings.file_extension = combo_row.get_selected_index()

    def _on_name_template_changed(self, entry, prop_name):
        self.settings.name_template = entry.get_text()

    def _on_overwrite_changed(self, toggle_button, prop_name):
        self.settings.overwrite = toggle_button.get_active()

    def _on_loop_limit_changed(self, spin_button, prop_name):
        self.settings.loop_limit = spin_button.get_value_as_int()

    def _on_duration_limit_changed(self, entry, prop_name):
        self.settings.duration_limit = entry.get_text()

    def _on_keep_streams_changed(self, toggle_button, prop_name):
        self.settings.keep_streams = toggle_button.get_active()

    def _on_video_switch_changed(self, toggle_button, prop_name):
        self.settings.download_video = toggle_button.get_active()
        # Force-toggle audio if also video and share are deactivated
        if not (self.settings.download_video or self.settings.download_audio or self.settings.download_share_version):
            self.audio_switch.set_active(True)
        self._update_quality_widgets()

    def _on_video_resolution_changed(self, combo_row, prop_name):
        # Worst -> 0, Best -> -1
        self.settings.video_resolution = combo_row.get_selected_index() * -1

    def _on_max_video_resolution_changed(self, combo_row, prop_name):
        self.settings.max_video_resolution = combo_row.get_selected_index()
        self._update_quality_widgets()

    def _on_min_video_resolution_changed(self, combo_row, prop_name):
        self.settings.min_video_resolution = combo_row.get_selected_index()
        self._update_quality_widgets()

    def _on_audio_switch_changed(self, toggle_button, prop_name):
        self.settings.download_audio = toggle_button.get_active()
        # Force-toggle video if also audio and share are deactivated
        if not (self.settings.download_video or self.settings.download_audio or self.settings.download_share_version):
            self.video_switch.set_active(True)
        self._update_quality_widgets()

    def _on_audio_quality_changed(self, combo_row, prop_name):
        # Worst -> 0, Best -> -1
        self.settings.audio_quality = combo_row.get_selected_index() * -1

    def _on_share_switch_changed(self, toggle_button, prop_name):
        self.settings.download_share_version = toggle_button.get_active()
        self._update_quality_widgets()

    def _on_connections_changed(self, spin_button, prop_name):
        self.settings.connections = spin_button.get_value_as_int()

    def _on_retries_changed(self, spin_button, prop_name):
        self.settings.retry_attempts = spin_button.get_value_as_int()

    def _on_quantity_changed(self, spin_button, prop_name):
        self.settings.quantity_limit = spin_button.get_value_as_int()

    def _on_recoubs_download_changed(self, combo_row, prop_name):
        self.settings.download_recoubs = combo_row.get_selected_index()

    def _on_archive_changed(self, row, prop_name):
        self.settings.archive = row.get_enable_expansion()

    def _on_output_list_changed(self, row, prop_name):
        self.settings.output_list = row.get_enable_expansion()

    def _on_info_json_changed(self, row, prop_name):
        self.settings.info_json = row.get_enable_expansion()
