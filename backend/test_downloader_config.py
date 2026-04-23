import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))

from downloader import VideoDownloader


class DownloaderConfigTests(unittest.TestCase):
    def test_bilibili_options_include_cookiefile_when_configured(self):
        downloader = VideoDownloader()

        with tempfile.NamedTemporaryFile() as cookie_file:
            with patch.dict(os.environ, {"BILIBILI_COOKIE_FILE": cookie_file.name}):
                opts = {"http_headers": {}}
                downloader._apply_site_options(
                    opts,
                    "https://www.bilibili.com/video/BV1xx411c7mD/",
                )

        self.assertEqual(
            opts["http_headers"]["Referer"],
            "https://www.bilibili.com/",
        )
        self.assertEqual(
            opts["http_headers"]["Origin"],
            "https://www.bilibili.com",
        )
        self.assertEqual(opts["cookiefile"], cookie_file.name)

    def test_non_bilibili_options_do_not_include_cookiefile(self):
        downloader = VideoDownloader()

        with tempfile.NamedTemporaryFile() as cookie_file:
            with patch.dict(os.environ, {"BILIBILI_COOKIE_FILE": cookie_file.name}):
                opts = {"http_headers": {}}
                downloader._apply_site_options(
                    opts,
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                )

        self.assertNotIn("cookiefile", opts)
        self.assertEqual(opts["http_headers"], {})


if __name__ == "__main__":
    unittest.main()
