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

from gi.repository import Gio

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Settings(Gio.Settings):
    """
    Gio.Settings handler
    Implements the basic dconf-settings as properties
    """

    # Default Settings instance
    instance = None

    def __init__(self):
        super().__init__(self)

    @staticmethod
    def valid():
        settings = Settings.get_default()
        # Keep this list as short as possible
        if settings.max_video_resolution < settings.min_video_resolution:
            return False

        return True

    @staticmethod
    def new():
        g_settings = Gio.Settings.new("io.github.helpseeker.Gyre")
        g_settings.__class__ = Settings
        return g_settings

    @staticmethod
    def get_default():
        if Settings.instance is None:
            Settings.instance = Settings.new()

        return Settings.instance

    @property
    def output_path(self):
        return self.get_string("output-path")

    @output_path.setter
    def output_path(self, value):
        self.set_string("output-path", value)

    @property
    def file_extension(self):
        return self.get_enum("file-extension")

    @file_extension.setter
    def file_extension(self, value):
        self.set_enum("file-extension", value)

    @property
    def file_extension_nick(self):
        value = self.file_extension
        return ["mkv", "mp4", "asf", "avi", "flv", "f4v", "mov"][value]

    @property
    def name_template(self):
        return self.get_string("name-template")

    @name_template.setter
    def name_template(self, value):
        self.set_string("name-template", value)

    @property
    def overwrite(self):
        return self.get_boolean("overwrite")

    @overwrite.setter
    def overwrite(self, value):
        self.set_boolean("overwrite", value)

    @property
    def loop_limit(self):
        return self.get_int("loop-limit")

    @loop_limit.setter
    def loop_limit(self, value):
        self.set_int("loop-limit", value)

    @property
    def duration_limit(self):
        return self.get_string("duration-limit")

    @duration_limit.setter
    def duration_limit(self, value):
        self.set_string("duration-limit", value)

    @property
    def keep_streams(self):
        return self.get_boolean("keep-streams")

    @keep_streams.setter
    def keep_streams(self, value):
        self.set_boolean("keep-streams", value)

    @property
    def download_video(self):
        return self.get_boolean("download-video")

    @download_video.setter
    def download_video(self, value):
        self.set_boolean("download-video", value)

    @property
    def video_resolution(self):
        return self.get_enum("video-resolution")

    @video_resolution.setter
    def video_resolution(self, value):
        self.set_enum("video-resolution", value)

    @property
    def max_video_resolution(self):
        return self.get_enum("max-video-resolution")

    @max_video_resolution.setter
    def max_video_resolution(self, value):
        self.set_enum("max-video-resolution", value)

    @property
    def min_video_resolution(self):
        return self.get_enum("min-video-resolution")

    @min_video_resolution.setter
    def min_video_resolution(self, value):
        self.set_enum("min-video-resolution", value)

    @property
    def download_audio(self):
        return self.get_boolean("download-audio")

    @download_audio.setter
    def download_audio(self, value):
        self.set_boolean("download-audio", value)

    @property
    def audio_quality(self):
        return self.get_enum("audio-quality")

    @audio_quality.setter
    def audio_quality(self, value):
        self.set_enum("audio-quality", value)

    @property
    def download_share_version(self):
        return self.get_boolean("download-share-version")

    @download_share_version.setter
    def download_share_version(self, value):
        self.set_boolean("download-share-version", value)

    @property
    def connections(self):
        return self.get_int("connections")

    @connections.setter
    def connections(self, value):
        self.set_int("connections", value)

    @property
    def retry_attempts(self):
        return self.get_int("retry-attempts")

    @retry_attempts.setter
    def retry_attempts(self, value):
        self.set_int("retry-attempts", value)

    @property
    def download_recoubs(self):
        return self.get_enum("download-recoubs")

    @download_recoubs.setter
    def download_recoubs(self, value):
        self.set_enum("download-recoubs", value)

    @property
    def auto_remove(self):
        return self.get_boolean("auto-remove")

    @auto_remove.setter
    def auto_remove(self, value):
        self.set_boolean("auto-remove", value)

    @property
    def repeat_download(self):
        return self.get_boolean("repeat-download")

    @repeat_download.setter
    def repeat_download(self, value):
        self.set_boolean("repeat-download", value)

    @property
    def repeat_interval(self):
        return self.get_int("repeat-interval")

    @repeat_interval.setter
    def repeat_interval(self, value):
        self.set_int("repeat-interval", value)

    @property
    def archive(self):
        return self.get_boolean("archive")

    @archive.setter
    def archive(self, value):
        self.set_boolean("archive", value)

    @property
    def archive_path(self):
        return self.get_string("archive-path")

    @archive_path.setter
    def archive_path(self, value):
        self.set_string("archive-path", value)

    @property
    def output_list(self):
        return self.get_boolean("output-list")

    @output_list.setter
    def output_list(self, value):
        self.set_boolean("output-list", value)

    @property
    def output_list_path(self):
        return self.get_string("output-list-path")

    @output_list_path.setter
    def output_list_path(self, value):
        self.set_string("output-list-path", value)

    @property
    def info_json(self):
        return self.get_boolean("info-json")

    @info_json.setter
    def info_json(self, value):
        self.set_boolean("info-json", value)

    @property
    def info_json_path(self):
        return self.get_string("info-json-path")

    @info_json_path.setter
    def info_json_path(self, value):
        self.set_string("info-json-path", value)

    @property
    def tag_separator(self):
        return self.get_string("tag-separator")

    @tag_separator.setter
    def tag_separator(self, value):
        self.set_string("tag-separator", value)

    @property
    def download_chunk_size(self):
        return self.get_int("download-chunk-size")

    @download_chunk_size.setter
    def download_chunk_size(self, value):
        self.set_int("download-chunk-size", value)

    @property
    def allow_unicode(self):
        return self.get_boolean("allow-unicode")

    @allow_unicode.setter
    def allow_unicode(self, value):
        return self.set_boolean("allow-unicode", value)

    @property
    def first_start(self):
        return self.get_boolean("first-start")

    @first_start.setter
    def first_start(self, value):
        return self.set_boolean("first-start", value)
