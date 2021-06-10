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

import asyncio
import pathlib
import time
import traceback
import urllib

import aiohttp
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Handy", "1")

from gi.repository import Gtk, Gio, Handy, GLib, GObject

from gyre import utils
from gyre.container import cancel_containers, uncancel_containers
from gyre.coub import Coub, cancel_coubs, uncancel_coubs
from gyre.settings import Settings
from gyre.interface.add import AddURLWindow, AddWindow
from gyre.interface.window import GyreWindow
from gyre.interface.preferences import PreferenceWindow
from gyre.interface import dialogs

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Global variables
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# A hard limit on how many Coubs to process at once
# Prevents excessive RAM usage for very large downloads
COUB_LIMIT = 1000

# To signal cancellation to the work thread
CANCELLED = False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Application(Gtk.Application):

    idle = GObject.Property(type=bool, default=True)

    def __init__(self):
        super().__init__(application_id='io.github.helpseeker.Gyre',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.window = None
        self.connect("notify::idle", self._on_idle_changed)

    def add_actions(self):
        add_url_clicked = Gio.SimpleAction.new("add_url", None)
        add_url_clicked.connect("activate", self.do_add_url)
        self.add_action(add_url_clicked)

        add_item_clicked = Gio.SimpleAction.new("add_item", None)
        add_item_clicked.connect("activate", self.do_add_item)
        self.add_action(add_item_clicked)

        clean_clicked = Gio.SimpleAction.new("clean", None)
        clean_clicked.connect("activate", self.do_clean_list)
        self.add_action(clean_clicked)

        import_clicked = Gio.SimpleAction.new("import", None)
        import_clicked.connect("activate", self.do_import_profile)
        self.add_action(import_clicked)

        export_clicked = Gio.SimpleAction.new("export", None)
        export_clicked.connect("activate", self.do_export_profile)
        self.add_action(export_clicked)

        error_log_clicked = Gio.SimpleAction.new("log", None)
        error_log_clicked.connect("activate", self.do_open_error_log)
        self.add_action(error_log_clicked)

        about_clicked = Gio.SimpleAction.new("about", None)
        about_clicked.connect("activate", self.do_open_about)
        self.add_action(about_clicked)

        prefs_clicked = Gio.SimpleAction.new("prefs", None)
        prefs_clicked.connect("activate", self.do_open_prefs)
        self.add_action(prefs_clicked)

        start_clicked = Gio.SimpleAction.new("start", None)
        start_clicked.connect("activate", self.do_start_download)
        self.add_action(start_clicked)

        stop_clicked = Gio.SimpleAction.new("stop", None)
        stop_clicked.connect("activate", self.do_stop_download)
        self.add_action(stop_clicked)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        Handy.init()

    def do_activate(self):
        if not self.window:
            self.window = GyreWindow(
                application=self,
                title="Gyre",
                icon_name="io.github.helpseeker.Gyre"
            )
            self.add_actions()

            self.window.clean_button.set_action_name("app.clean")
            self.window.start_button.set_action_name("app.start")
            self.window.stop_button.set_action_name("app.stop")
            # for some reason binding the action makes the start button sensitive again
            self.window.update_widgets()

            self.window.connect("delete-event", self._on_delete_event)
            self.window.show_all()

            if Settings.get_default().first_start:
                dialog = dialogs.WelcomeScreen()
                dialog.set_transient_for(self.window)
                dialog.show_all()
                Settings.get_default().first_start = False

        self.window.present()

    def _on_delete_event(self, *args):
        if self.idle:
            return False

        dialog = dialogs.CloseConfirmation(self.window)
        if dialog.run() == Gtk.ResponseType.YES:
            self.quit()
        dialog.destroy()

        return True

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)
        self._clean_up()

    def do_add_url(self, *args):
        add_window = AddURLWindow(self.window.list)
        add_window.set_transient_for(self.window)
        add_window.show_all()

    def do_add_item(self, *args):
        add_window = AddWindow(self.window.list)
        add_window.set_transient_for(self.window)
        add_window.show_all()

    def do_clean_list(self, *args):
        # Temp list necessary as removing directly would mess up the order
        to_remove = []
        for item in self.window.list:
            if item.status in ["Finished", "No new coubs"]:
                to_remove.append(item)
        for item in to_remove:
            self.window.list.remove(self.window.list.find(item)[1])

    def do_import_profile(self, *args):
        if not self.idle:
            dialog = dialogs.ImportDisabledInfo(self.window)
            dialog.run()
            dialog.destroy()
            return

        dialog = dialogs.ProfileImporter(self.window)
        # FileChooserNative doesn't have any signals to connect
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            profile = pathlib.Path(dialog.get_filename())
            utils.import_profile(profile, self.window.list)
        dialog.destroy()

    def do_export_profile(self, *args):
        dialog = dialogs.ProfileExporter(self.window)
        # FileChooserNative doesn't have any signals to connect
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            profile = pathlib.Path(dialog.get_filename())
            utils.export_profile(profile, self.window.list)
        dialog.destroy()

    def do_open_error_log(self, *args):
        error_log = Gio.File.new_for_path(str(utils.get_error_log()))

        try:
            app = error_log.query_default_handler()
            if not app.launch([error_log]):
                raise GLib.Error
        except GLib.Error:
            # Provide an internal viewer, in case we're unable to launch a handler
            # This is the norm for Flatpak
            dialog = dialogs.ErrorLogViewer(self.window)
            dialog.run()
            dialog.destroy()

    def do_open_about(self, *args):
        about_dialog = dialogs.AboutDialog()
        about_dialog.set_transient_for(self.window)
        if about_dialog.run() == Gtk.ResponseType.DELETE_EVENT:
            about_dialog.destroy()

    def do_open_prefs(self, *args):
        prefs_window = PreferenceWindow()
        prefs_window.set_transient_for(self.window)
        prefs_window.show_all()

    def do_start_download(self, *args):
        if not self.idle:
            return

        uncancel_containers()
        uncancel_coubs()

        # Prompt user, if no existing output folder is selected
        # This can happen if no folder was chosen yet or if the chosen one was deleted
        while not pathlib.Path(Settings.get_default().output_path).exists():
            dialog = dialogs.MissingPathWarning(self.window)
            dialog.run()
            dialog.destroy()

        try:
            urllib.request.urlopen("https://coub.com")
        except urllib.error.URLError:
            dialog = dialogs.NoConnectionError(self.window)
            dialog.run()
            dialog.destroy()
            return

        if not Settings.get_default().valid():
            dialog = dialogs.InvalidSettingsError(self.window)
            dialog.run()
            dialog.destroy()
            return

        # Thread changes self.idle internally
        thread = utils.WorkThread(
            target=asyncio.run,
            args=(process(self.window.list),),
            daemon=True,
            parent=self,
        )
        thread.start()

    def do_stop_download(self, *args):
        global CANCELLED

        cancel_containers()
        cancel_coubs()
        CANCELLED = True
        # Stall until the work thread finished
        while not self.idle:
            time.sleep(0.1)
        self._clean_up()
        CANCELLED = False

    def _on_idle_changed(self, *args):
        self.window.add_button.set_sensitive(self.idle)
        for row in self.window.listbox:
            row.set_editable(self.idle)

    @staticmethod
    def _clean_up():
        for p in pathlib.Path(Settings.get_default().output_path).glob("*.gyre"):
            p.unlink()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

async def process(model):
    while True:
        ids = set()
        coubs = []

        quantity = None
        if Settings.get_default().quantity_limit:
            quantity = Settings.get_default().quantity_limit

        archive_content = set()
        if Settings.get_default().archive:
            archive = pathlib.Path(Settings.get_default().archive_path)
            if archive.exists():
                archive_content = set(archive.read_text().splitlines())

        tout = aiohttp.ClientTimeout(total=None)
        conn = aiohttp.TCPConnector(limit=Settings.get_default().connections)
        async with aiohttp.ClientSession(timeout=tout, connector=conn) as session:
            for item in model:
                item.status = "Started"
                item.reset()

            try:
                for item in model:
                    item.status = "Parsing"
                    temp = await item.get_ids(session, quantity)
                    # Weed out duplicates and already downloaded IDs
                    temp = [i for i in temp if not (i in ids or i in archive_content)]
                    # Adjust container count based on filtered ID list
                    item.count = len(temp)
                    if temp:
                        coubs.extend([Coub(i, item, session) for i in temp])
                        # Ugly, but we want to keep it a set for faster lookup
                        ids = list(ids)
                        ids.extend(temp)
                        ids = set(ids)
                    if quantity is not None:
                        quantity -= len(temp)
                    item.status = "Waiting"

                # Marking containers as finished while parsing is problematic
                # Users could clean them up (i.e. remove them) and mess up the list order
                for item in model:
                    if Settings.get_default().output_list:
                        item.status = "Finished"
                    elif not item.count:
                        item.status = "No new coubs"
                    else:
                        item.status = "Downloading"

                if Settings.get_default().output_list:
                    links = [f"https://coub.com/view/{coub.id}" for coub in coubs]
                    pathlib.Path(Settings.get_default().output_list_path).write_text("\n".join(links))
                    return

                while coubs:
                    tasks = [c.process() for c in coubs[:COUB_LIMIT]]
                    await asyncio.gather(*tasks)
                    coubs = coubs[COUB_LIMIT:]
            except utils.CancelledError:
                for item in model:
                    item.status = "Cancelled"
                break
            except:
                for item in model:
                    item.status = "Error: Unknown error"
                error = traceback.format_exc()
                utils.write_error_log(error)
                break

        if Settings.get_default().repeat_download:
            for timer in range(Settings.get_default().repeat_interval, 0, -1):
                for item in model:
                    item.status = f"Waiting to start next download ({timer} min. remaining)"
                for _ in range(120):
                    if CANCELLED:
                        break
                    time.sleep(0.5)
        else:
            break
