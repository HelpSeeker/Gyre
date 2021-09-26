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
import json
import pathlib
import re
import subprocess
import unicodedata

from aiohttp import ClientError

from gyre.settings import Settings
from gyre.utils import cancellable, write_error_log

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CoubUnavailableError(Exception):
    pass


class CoubExistsError(Exception):

    def __init__(self, path):
        self.path = path


class CoubCorruptedError(Exception):

    def __init__(self, path):
        self.path = path


class Coub:

    id = ""
    title = ""
    creation = ""
    channel = ""
    community = ""
    tags = []

    container = None
    session = None

    video = False
    audio = False

    video_link = ""
    audio_link = ""

    video_file = None
    audio_file = None
    merged_file = None

    def __init__(self, id, container, session):
        super().__init__()
        self.id = id
        self.container = container
        self.session = session
        # We want to be able to re-download coubs with different settings
        self.video = Settings.get_default().download_video
        self.audio = Settings.get_default().download_audio
        # share version is basically like a video-only download
        if Settings.get_default().download_share_version:
            self.video = True
            self.audio = False

    def _log_infos(self):
        infos = {
            "id": self.id,
            "title": self.title,
            "creation": self.creation,
            "channel": self.channel,
            "community": self.community,
            "tags": self.tags,
        }
        with pathlib.Path(Settings.get_default().info_json_path).open("a") as f:
            print(json.dumps(infos), file=f)

    def _log_archive_entry(self):
        with pathlib.Path(Settings.get_default().archive_path).open("a") as f:
            print(self.id, file=f)

    def _clean_up(self):
        if Settings.get_default().keep_streams:
            return
        if not (self.audio_file or self.video_file):
            return

        if self.video and self.audio:
            self.audio_file.unlink(missing_ok=True)
            if not self.video_file == self.merged_file:
                self.video_file.unlink(missing_ok=True)

    def _finish(self):
        self.container.done += 1
        self._clean_up()

    @cancellable
    def _update_properties(self, api_json):
        self.title = api_json["title"]
        self.creation = api_json["created_at"]
        self.channel = api_json["channel"]["title"]
        self.tags = [t["title"] for t in api_json["tags"]]

        if api_json["communities"]:
            self.community = api_json["communities"][0]["permalink"]
        else:
            self.community = "undefined"

    @cancellable
    def _assemble_name(self):
        if not Settings.get_default().name_template:
            return self.id

        name = Settings.get_default().name_template
        name = name.replace("%id%", self.id)
        name = name.replace("%title%", self.title)
        name = name.replace("%creation%", self.creation.replace(":", "-"))
        name = name.replace("%channel%", self.channel)
        name = name.replace("%community%", self.community)
        name = name.replace("%tags%", Settings.get_default().tag_separator.join(self.tags))
        name = get_valid_filename(name, Settings.get_default().allow_unicode)

        if not name:
            return self.id

        return name

    @cancellable
    async def _fetch_infos(self):
        async with self.session.get(f"https://coub.com/api/v2/coubs/{self.id}") as response:
            api_json = await response.read()
            api_json = json.loads(api_json)

        video_streams, audio_streams = get_stream_lists(api_json)
        self.video = bool(video_streams) if self.video else self.video
        self.audio = bool(audio_streams) if self.audio else self.audio

        if not (self.video or self.audio):
            raise CoubUnavailableError

        if self.video:
            self.video_link = video_streams[Settings.get_default().video_resolution]
        if self.audio:
            self.audio_link = audio_streams[Settings.get_default().audio_quality]

        self._update_properties(api_json)
        name = self._assemble_name()
        path = pathlib.Path(Settings.get_default().output_path)

        self.video_file = path / f"{name}.mp4"
        self.audio_file = path / f"{name}.mp3"
        self.merged_file = path / f"{name}.{Settings.get_default().file_extension_nick}"
        if Settings.get_default().download_share_version:
            self.merged_file = self.video_file

    @cancellable
    def _check_existence(self):
        exists = None
        if self.merged_file.exists():
            exists = self.merged_file
        elif self.video_file.exists():
            exists = self.video_file
        elif self.audio_file.exists():
            exists = self.audio_file

        if exists and not Settings.get_default().overwrite:
            raise CoubExistsError(exists)

    @cancellable
    async def _download(self):
        args = []
        if self.video:
            args.append([self.video_link, self.video_file, self.session])
        if self.audio:
            args.append([self.audio_link, self.audio_file, self.session])

        tasks = [save_stream(*a) for a in args]
        await asyncio.gather(*tasks)

        # After this point the file won't be removed when the program quits
        # Don't do it later to not mess with FFmpeg's automatic format detection
        if self.video:
            self.video_file.with_suffix(f"{self.video_file.suffix}.gyre").replace(self.video_file)
        if self.audio:
            self.audio_file.with_suffix(f"{self.audio_file.suffix}.gyre").replace(self.audio_file)

    @cancellable
    def _check_integrity(self):
        if self.video and file_corrupted(self.video_file):
            fix_old_storage_method(self.video_file)
            # Video files have a chance of being fixed, so check again
            if file_corrupted(self.video_file):
                raise CoubCorruptedError(self.video_file)

        if self.audio and file_corrupted(self.audio_file):
            raise CoubCorruptedError(self.audio_file)

    @cancellable
    def _merge_streams(self):
        # temp_file uses prefix to not mess with FFmpeg's automatic muxer detection
        temp_file = pathlib.Path(self.merged_file.parent, f"temp_{self.merged_file.name}")
        concat_file = self.merged_file.with_suffix(".txt")

        with concat_file.open("w") as f:
            for _ in range(Settings.get_default().loop_limit):
                print(f"file '{self.video_file}'", file=f)

        command = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-i", str(self.audio_file),
        ]
        if Settings.get_default().duration_limit:
            command.extend(["-t", Settings.get_default().duration_limit])
        command.extend(["-c", "copy", "-shortest", str(temp_file)])

        subprocess.run(command, check=False)

        concat_file.unlink()
        # necessary as FFmpeg can't change files in-place, if merge ext is mp4
        temp_file.replace(self.merged_file)

    @cancellable
    async def process(self):
        retries = Settings.get_default().retry_attempts
        attempt = 0
        while retries < 0 or attempt <= retries:
            try:
                if not (self.video_link or self.audio_link):
                    await self._fetch_infos()
                self._check_existence()
                await self._download()
                self._check_integrity()
                if self.audio and self.video and not Settings.get_default().download_share_version:
                    self._merge_streams()
                if Settings.get_default().archive:
                    self._log_archive_entry()
                if Settings.get_default().info_json:
                    self._log_infos()
                break
            except (ClientError, json.decoder.JSONDecodeError):
                attempt += 1
            except CoubUnavailableError:
                write_error_log(f"https://coub.com/view/{self.id} is unavailable")
                self.container.invalid += 1
                break
            except CoubExistsError as error:
                write_error_log(f"{error.path.name} already exists")
                self.container.exist += 1
                break
            except CoubCorruptedError as error:
                write_error_log(f"{error.path.name} corrupted")
                self.container.invalid += 1
                break

        self._finish()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@cancellable
def get_valid_filename(title, allow_unicode):
    if allow_unicode:
        title = unicodedata.normalize("NFKC", title)
    else:
        title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")

    title = re.sub(r"[^\w\s().,+-]", " ", title)
    title = re.sub(r"[\s]+", " ", title)

    # Make sure there are any words left after ASCII conversion
    if not re.sub(r"[^\w]|_", "", title):
        return ""
    # Fix weird looking paranthesis when words are missing after ASCII conversion
    title = re.sub(r"\( ", "(", title)
    title = re.sub(r" \)", ")", title)
    # Remove starting/trailing characters, which are either invalid or another
    # byproduct of the Unicode->ASCII conversion
    title = title.strip("-. ")

    try:
        # Add example extension to simulate the full name length
        test = pathlib.Path(title).with_suffix(".ext.gyre")
        test.touch()
        test.unlink(missing_ok=True)
    except OSError:
        return ""

    return title

@cancellable
def get_stream_lists(api_json):
    # All the following resolutions are max. values
    # Depending on the aspect ratio, one side can be smaller
    # Think of them as windows, which the video is fit into
    #
    # 'html5' has 3 video and 2 audio versions
    #     video: med    (640x480)
    #            high   (1280x960)
    #            higher (1600x1200)
    #     audio: med    (MP3@128Kbps CBR)
    #            high   (MP3@160Kbps VBR)
    #
    # 'mobile' has 1 video and 2 audio versions
    #     video: video  (640x480)
    #     audio: 0      (MP3@128Kbps CBR)
    #
    # 'share' has 1 version (video/audio combined)
    #     default (1280x960 or 640x480 and AAC@128Kbps CBR)
    #
    # More infos:
    #     All videos come with a watermark
    #     html5 video/audio may have less versions available
    #     html5 video med and mobile video are the same file
    #     html5 audio med and mobile audio are the same file
    #     mobile audio was available as AAC and MP3 in the past (now only MP3)
    #     share audio is always AAC
    #     share version is often cut short (never saw it exceed 30 seconds)
    #     videos come as mp4, audio as mp3
    #     video versions may also be upscaled to fit the resolution window
    #
    # Streams that may still be unavailable:
    #     share
    #     html5 video higher
    #     html5 video med in a non-broken state (doesn't require \x00\x00 fix)

    # Api returns "error: Coub not found" if Coub unavailable
    if "error" in api_json:
        return ([], [])

    # Share video
    if Settings.get_default().download_share_version:
        share = api_json["file_versions"]["share"]["default"]
        # Non-existence results in None or '{}' (the latter is rare)
        if share and share != "{}":
            return ([share], [])
        return ([], [])

    # Video streams
    available = api_json["file_versions"]["html5"]["video"]
    formats =  ["med", "high", "higher"]
    lowest = Settings.get_default().min_video_resolution
    highest = Settings.get_default().max_video_resolution

    video = []
    for f in formats[lowest:highest+1]:
        if f in available and available[f]["size"]:
            # html5 stream sizes can be 0 or None in case of a missing stream
            # None is the exception and an irregularity in the Coub API
            video.append(available[f]["url"])

    # Audio streams
    try:
        available = api_json["file_versions"]["html5"]["audio"]
        formats = ["med", "high"]

        audio = []
        for f in formats:
            if f in available and available[f]["size"]:
                audio.append(available[f]["url"])
    except KeyError:
        # No audio
        audio = []

    return (video, audio)


@cancellable
async def save_chunk(stream, file):
    chunk = await stream.content.read(Settings.get_default().download_chunk_size)

    if not chunk:
        return False

    file.write(chunk)

    return True


@cancellable
async def save_stream(link, path, session):
    async with session.get(link) as stream:
        # Open file with .gyre suffix to easily distinguish temp files
        # .gyre was chosen, to ensure no accidental file erasure (possible with .part)
        with path.with_suffix(f"{path.suffix}.gyre").open("wb") as f:
            chunk = True
            while chunk:
                chunk = await save_chunk(stream, f)


@cancellable
def fix_old_storage_method(path):
    # Coub used to store videos in a broken state and fixed them before playback
    # They stopped doing this when they introduced the watermarks
    # Some old coubs might still be stored like this
    with path.open("r+b") as f:
        temp = f.read()
    with path.open("w+b") as f:
        f.write(b'\x00\x00' + temp[2:])


@cancellable
def file_corrupted(path):
    command = ["ffmpeg", "-v", "error", "-i", str(path), "-t", "1", "-f", "null", "-"]
    out = subprocess.run(command, capture_output=True, text=True, check=False)

    # Checks against typical error messages
    # "Header missing"/"Failed to read frame size" -> audio corruption
    # "Invalid NAL" -> video corruption
    # "moov atom not found" -> old Coub storage method
    typical = [
        "Header missing",
        "Failed to read frame size",
        "Invalid NAL",
        "moov atom not found",
    ]
    for error in typical:
        if error in out.stderr:
            return True

    return False
