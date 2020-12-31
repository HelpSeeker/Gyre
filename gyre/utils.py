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

import json
import pathlib
import threading
import time

from gi.repository import GLib

from gyre.settings import Settings

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CancelledError(Exception):
    pass


class WorkThread(threading.Thread):

    def __init__(self, *args, parent=None, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)

    def run(self):
        self.parent.idle = False
        super().run()
        self.parent.idle = True

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_cache_dir():
    cache_dir = pathlib.Path(GLib.get_user_cache_dir())

    # Check if we're inside a Flatpak
    if is_flatpak():
        return cache_dir

    cache_dir = cache_dir / "gyre"
    if not cache_dir.exists():
        cache_dir.mkdir()

    return cache_dir


def is_flatpak():
    return pathlib.Path(GLib.get_user_runtime_dir(), "flatpak-info").exists()


def get_error_log():
    error_log = get_cache_dir() / "error.log"

    if not error_log.exists():
        error_log.touch(exist_ok=True)

    return error_log


def write_error_log(error):
    with get_error_log().open("a") as f:
        print(f"[{time.asctime()}] {error}", file=f)


def import_profile(path, liststore):
    from gyre.container import create_container

    with path.open("r") as f:
        content = json.load(f)

    for opt in content["Settings"]:
        setattr(Settings.get_default(), opt, content["Settings"][opt])

    liststore.remove_all()
    liststore.splice(0, 0, [create_container(**item) for item in content["Input"]])


def export_profile(path, liststore):
    options = [
        "output_path",
        "file_extension",
        "name_template",
        "overwrite",
        "loop_limit",
        "duration_limit",
        "keep_streams",
        "download_video",
        "video_resolution",
        "max_video_resolution",
        "min_video_resolution",
        "download_audio",
        "audio_quality",
        "download_share_version",
        "connections",
        "retry_attempts",
        "quantity_limit",
        "download_recoubs",
        "archive",
        "archive_path",
        "output_list",
        "output_list_path",
        "info_json",
        "info_json_path",
        "tag_separator",
        "tag_separator",
        "download_chunk_size",
        "allow_unicode",
    ]

    content = {
        "Settings": {
            opt: getattr(Settings.get_default(), opt) for opt in options
        },
        "Input": [
            {
                "type": item.type,
                "id": item.id,
                "sort": item.sort,
                "quantity": item.quantity
            } for item in liststore
        ]
    }

    with path.open("w") as f:
        json.dump(content, f)


def translate_community_name(community, direction="to_ui"):
    name_map = {
        "animals-pets": "Animals & Pets",
        "anime": "Anime",
        "art": "Art & Design",
        "cars": "Auto & Technique",
        "cartoons": "Cartoons",
        "celebrity": "Celebrity",
        "dance": "Dance",
        "fashion": "Fashion & Beauty",
        "gaming": "Gaming",
        "mashup": "Mashup",
        "movies": "Movies & TV",
        "music": "Music",
        "nature-travel": "Nature & Travel",
        "news": "News & Politics",
        "nsfw": "NSFW",
        "science-technology": "Science & Technology",
        "sports": "Sports",
    }

    if direction == "to_ui":
        return name_map[community]
    if direction == "to_api":
        reverse_map = dict(zip(name_map.values(), name_map.keys()))
        return reverse_map[community]

    raise ValueError("Invalid direction")
