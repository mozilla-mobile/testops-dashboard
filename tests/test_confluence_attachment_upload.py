#!/usr/bin/env python3

import os
import tempfile
import unittest

from pathlib import Path
from unittest.mock import MagicMock, patch


with patch.dict(
    os.environ,
    {
        "ATLASSIAN_API_TOKEN": "test-token",
        "ATLASSIAN_USERNAME": "test-user",
        "ATLASSIAN_HOST": "example.atlassian.net",
    },
):
    from api.confluence import api_confluence


class TestConfluenceAttachmentUpload(unittest.TestCase):
    @patch.object(api_confluence.requests, "post")
    def test_uploads_image_using_confluence_rest_api(self, mock_post):
        mock_post.return_value = MagicMock()
        with tempfile.TemporaryDirectory() as image_dir:
            image_path = Path(image_dir) / "dashboard.png"
            image_path.write_bytes(b"image data")

            with patch.object(api_confluence, "PATH_IMAGES", Path(image_dir)):
                api_confluence.image_attachments_upload("12345")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], api_confluence.url_attachments("12345"))
        self.assertEqual(kwargs["auth"], api_confluence.auth)
        self.assertEqual(
            kwargs["headers"]["X-Atlassian-Token"],
            "no-check",
        )
        uploaded_filename, uploaded_file = kwargs["files"]["file"]
        self.assertEqual(uploaded_filename, "dashboard.png")
        self.assertTrue(uploaded_file.closed)
