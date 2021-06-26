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
import math
import pathlib
import re
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote

from aiohttp import ClientError, ClientResponseError
from gi.repository import GObject

from gyre import checker
from gyre.coub import Coub
from gyre.utils import CancelledError, write_error_log
from gyre.settings import Settings

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Global variables
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CANCELLED = False

# A hard limit on how many Coubs to process at once
# Prevents excessive RAM usage for very large downloads
COUB_LIMIT = 1000

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Classes
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ContainerUnavailableError(Exception):
    pass


class InsufficientRetriesError(Exception):
    pass


class BaseContainer(GObject.GObject):
    type = ""
    id = ""
    sort = ""
    quantity = None
    template = ""

    # Attempts are done on a per-page level, but the attempt limit is for all pages
    attempt = 0

    status_value = ""
    page_progress = GObject.Property(type=int, default=0)
    done = GObject.Property(type=int, default=0)

    pages = 0
    count = 0
    invalid = 0
    exist = 0

    PER_PAGE = 25

    def __init__(self, id, sort, quantity):
        super().__init__()
        # Links copied from the browser already have special characters escaped
        # Using urlquote again leads to invalid templates
        self.id = urlunquote(id)
        self.sort = sort
        self.quantity = quantity

    @GObject.Property(type=str)
    def status(self):
        return self.status_value

    @status.setter
    def status(self, value):
        if not self.status.startswith("Error"):
            self.status_value = value

    def _assemble_template(self):
        pass

    async def _fetch_page_count(self, session):
        if CANCELLED:
            raise CancelledError

        try:
            async with session.get(self.template) as response:
                api_json = await response.read()
                self.pages = json.loads(api_json)["total_pages"]
        except ClientResponseError:
            raise ContainerUnavailableError

    async def _fetch_page_ids(self, request, session):
        api_json = None
        retries = Settings.get_default().retry_attempts
        while retries < 0 or self.attempt <= retries:
            if CANCELLED:
                raise CancelledError

            try:
                async with session.get(request) as response:
                    api_json = await response.read()
                    api_json = json.loads(api_json)
                break
            except ClientError:
                self.attempt += 1

        if api_json is None:
            raise InsufficientRetriesError

        ids = []
        for coub in api_json["coubs"]:
            if coub["recoub_to"]:
                c_id = coub["recoub_to"]["permalink"]
            else:
                c_id = coub["permalink"]

            if not (checker.in_archive(c_id) or checker.in_session(c_id)):
                ids.append(c_id)

        self.page_progress += 1
        return ids

    async def _get_ids(self, session):
        self._assemble_template()

        try:
            await self._fetch_page_count(session)

            if self.quantity:
                max_pages = math.ceil(self.quantity/self.PER_PAGE)
                if self.pages > max_pages:
                    self.pages = max_pages

            requests = [f"{self.template}&page={p}" for p in range(1, self.pages+1)]
            tasks = [self._fetch_page_ids(r, session) for r in requests]
            ids = await asyncio.gather(*tasks)
            ids = [i for page in ids for i in page]
        except ContainerUnavailableError:
            self.status = f"Error: Invalid {self.type}"
            write_error_log(f"Invalid {self.type}: {self.id}")
            ids = []
        except InsufficientRetriesError:
            # Be strict about not handling only partially parsed containers
            self.status = "Error: No retry attempts left!"
            write_error_log("No retry attempts left for {self.type} {self.id}!")
            ids = []

        if self.quantity:
            return ids[:self.quantity]
        return ids

    def _reset(self):
        self.page_progress = 0
        self.pages = 0
        self.count = 0
        self.done = 0
        self.invalid = 0
        self.exist = 0

    async def process(self, session):
        self._reset()
        self.status = "Parsing"
        ids = await self._get_ids(session)
        self.count = len(ids)

        if Settings.get_default().output_list:
            links = [f"https://coub.com/view/{i}" for i in ids]
            with pathlib.Path(Settings.get_default().output_list_path).open("a") as f:
                print(*links, sep="\n", file=f)
            self.status = "Finished"
            return
        elif not self.count:
            self.status = "No new coubs"
        else:
            self.status = "Downloading"

        coubs = [Coub(i, self, session) for i in ids]

        while coubs:
            tasks = [c.process() for c in coubs[:COUB_LIMIT]]
            await asyncio.gather(*tasks)
            coubs = coubs[COUB_LIMIT:]


class SingleCoub(BaseContainer):
    type = "Coub"

    def __init__(self, id, sort="", quantity=0):
        super().__init__(id, sort, quantity)

    # async is unnecessary here, but avoids the need for special treatment
    async def _get_ids(self, session):
        # To trigger status change
        self.pages = 1
        self.page_progress = 1

        return [self.id]


class LinkList(BaseContainer):
    type = "List"

    def __init__(self, id, sort="", quantity=0):
        super().__init__(id, sort, quantity)
        self.list = pathlib.Path(id)

    def _valid_list_file(self):
        try:
            # Avoid using path object methods as they always read the whole file
            with self.list.open("r") as f:
                _ = f.read(1)
        except FileNotFoundError:
            self.status = "Error: List doesn't exist!"
            return False
        except (OSError, UnicodeError):
            self.status = "Error: Invalid list file!"
            return False

        return True

    async def _get_ids(self, session):
        # To trigger status change
        self.pages = 1
        self.page_progress = 1

        if not self._valid_list_file():
            return []

        ids = self.list.read_text().strip()
        ids = re.split(r"\s+", ids)
        ids = [i for i in ids if i.startswith("https://coub.com/view/")]
        ids = [i.replace("https://coub.com/view/", "") for i in ids]

        if self.quantity:
            return ids[:self.quantity]
        return ids


class Channel(BaseContainer):
    type = "Channel"

    def __init__(self, id, sort="Most Recent", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Most Recent": "newest",
            "Most Liked": "likes_count",
            "Most Viewed": "views_count",
            "Oldest": "oldest",
            "Random": "random",
        }

        template = f"https://coub.com/api/v2/timeline/channel/{urlquote(self.id)}"
        template = f"{template}?per_page={self.PER_PAGE}"

        if not Settings.get_default().download_recoubs:
            template = f"{template}&type=simples"
        elif Settings.get_default().download_recoubs == 2:
            template = f"{template}&type=recoubs"

        template = f"{template}&order_by={sort_map[self.sort]}"

        self.template = template


class Tag(BaseContainer):
    type = "Tag"

    def __init__(self, id, sort="Popular", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Popular": "newest_popular",
            "Top": "likes_count",
            "Views Count": "views_count",
            "Fresh": "newest"
        }

        template = f"https://coub.com/api/v2/timeline/tag/{urlquote(self.id)}"
        template = f"{template}?per_page={self.PER_PAGE}"
        template = f"{template}&order_by={sort_map[self.sort]}"

        self.template = template

    async def _fetch_page_count(self, session):
        await super()._fetch_page_count(session)
        # API limits tags to 99 pages
        if self.pages > 99:
            self.pages = 99


class Search(BaseContainer):
    type = "Search"

    def __init__(self, id, sort="Relevance", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Relevance": None,
            "Top": "likes_count",
            "Views Count": "views_count",
            "Most Recent": "newest"
        }

        template = f"https://coub.com/api/v2/search/coubs?q={urlquote(self.id)}"
        template = f"{template}&per_page={self.PER_PAGE}"

        if sort_map[self.sort]:
            template = f"{template}&order_by={sort_map[self.sort]}"

        self.template = template


class Community(BaseContainer):
    type = "Community"

    def __init__(self, id, sort="Hot (Monthly)", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Hot (Daily)": "daily",
            "Hot (Weekly)": "weekly",
            "Hot (Monthly)": "monthly",
            "Hot (Quarterly)": "quarter",
            "Hot (Six Months)": "half",
            "Rising": "rising",
            "Fresh": "fresh",
            "Top": "likes_count",
            "Views Count": "views_count",
            "Random": "random",
        }

        template = f"https://coub.com/api/v2/timeline/community/{urlquote(self.id)}"

        if self.sort in ("Top", "Views Count"):
            template = f"{template}/fresh?order_by={sort_map[self.sort]}&"
        elif self.sort == "Random":
            template = f"https://coub.com/api/v2/timeline/random/{self.id}?"
        else:
            template = f"{template}/{sort_map[self.sort]}?"

        template = f"{template}per_page={self.PER_PAGE}"

        self.template = template

    async def _fetch_page_count(self, session):
        await super()._fetch_page_count(session)
        # API limits communities to 99 pages
        if self.pages > 99:
            self.pages = 99


class Featured(Community):
    type = "Featured"

    def __init__(self, id="", sort="Recent", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Recent": None,
            "Top of the Month": "top_of_the_month",
            "Undervalued": "undervalued",
        }
        template = "https://coub.com/api/v2/timeline/explore?"

        if sort_map[self.sort]:
            template = f"{template}order_by={sort_map[self.sort]}&"

        template = f"{template}per_page={self.PER_PAGE}"

        self.template = template


class CoubOfTheDay(Community):
    type = "Coub of the Day"

    def __init__(self, id="", sort="Recent", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Recent": None,
            "Top": "top",
            "Views Count": "views_count",
        }
        template = "https://coub.com/api/v2/timeline/explore/coub_of_the_day?"

        if sort_map[self.sort]:
            template = f"{template}order_by={sort_map[self.sort]}&"

        template = f"{template}per_page={self.PER_PAGE}"

        self.template = template


class Story(BaseContainer):
    type = "Story"
    PER_PAGE = 20

    def __init__(self, id, sort="", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        # Story URL contains ID + title separated by a dash
        template = f"https://coub.com/api/v2/stories/{self.id.split('-')[0]}/coubs"
        template = f"{template}?per_page={self.PER_PAGE}"

        self.template = template


class HotSection(BaseContainer):
    type = "Hot Section"

    def __init__(self, id="", sort="Hot (Monthly)", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Hot (Daily)": "daily",
            "Hot (Weekly)": "weekly",
            "Hot (Monthly)": "monthly",
            "Hot (Quarterly)": "quarter",
            "Hot (Six Months)": "half",
            "Rising": "rising",
            "Fresh": "fresh",
        }

        template = "https://coub.com/api/v2/timeline/subscriptions"
        template = f"{template}/{sort_map[self.sort]}"
        template = f"{template}?per_page={self.PER_PAGE}"

        self.template = template

    async def _fetch_page_count(self, session):
        await super()._fetch_page_count(session)
        # API limits hot section to 99 pages
        if self.pages > 99:
            self.pages = 99


class Random(BaseContainer):
    type = "Random"

    def __init__(self, id="", sort="Popular", quantity=0):
        super().__init__(id, sort, quantity)

    def _assemble_template(self):
        sort_map = {
            "Popular": None,
            "Top": "top",
        }

        template = "https://coub.com/api/v2/timeline/explore/random?"

        if sort_map[self.sort]:
            template = f"{template}order_by={sort_map[self.sort]}&"

        template = f"{template}per_page={self.PER_PAGE}"

        self.template = template

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def uncancel_containers():
    global CANCELLED
    CANCELLED = False


def cancel_containers():
    global CANCELLED
    CANCELLED = True


def create_container(type, id, sort, quantity):
    args = {}
    if id:
        args["id"] = id
    if sort:
        args["sort"] = sort
    if quantity:
        args["quantity"] = quantity

    if type == "Coub":
        return SingleCoub(**args)
    if type == "List":
        return LinkList(**args)
    if type == "Channel":
        return Channel(**args)
    if type == "Tag":
        return Tag(**args)
    if type == "Search":
        return Search(**args)
    if type == "Community":
        return Community(**args)
    if type == "Featured":
        return Featured(**args)
    if type == "Coub of the Day":
        return CoubOfTheDay(**args)
    if type == "Story":
        return Story(**args)
    if type == "Hot Section":
        return HotSection(**args)
    if type == "Random":
        return Random(**args)
