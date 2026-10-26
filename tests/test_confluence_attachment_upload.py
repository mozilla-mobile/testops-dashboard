#!/usr/bin/env python3

import os
import requests
import tempfile
import unittest
import unittest.mock

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
    def setUp(self):
        self._orig_headers = dict(api_confluence.headers)
        self.addCleanup(self._restore_headers)

    def _restore_headers(self):
        api_confluence.headers.clear()
        api_confluence.headers.update(self._orig_headers)

    @patch.object(api_confluence.requests, "post")
    @patch.object(api_confluence.requests, "put")
    def test_uploads_image_using_confluence_rest_api(
        self, mock_put, mock_post
    ):
        mock_put.return_value = MagicMock()
        with tempfile.TemporaryDirectory() as image_dir:
            image_path = Path(image_dir) / "dashboard.png"
            image_path.write_bytes(b"image data")

            with patch.object(api_confluence, "PATH_IMAGES", Path(image_dir)):
                api_confluence.image_attachments_upload("12345")

        mock_put.assert_called_once()
        mock_post.assert_not_called()
        args, kwargs = mock_put.call_args
        self.assertEqual(args[0], api_confluence.url_attachments("12345"))
        self.assertEqual(kwargs["auth"], api_confluence.auth)
        self.assertEqual(
            kwargs["headers"]["X-Atlassian-Token"],
            "no-check",
        )
        uploaded_filename, uploaded_file = kwargs["files"]["file"]
        self.assertEqual(uploaded_filename, "dashboard.png")
        self.assertTrue(uploaded_file.closed)

    @patch.object(api_confluence.requests, "put")
    def test_page_write_does_not_leak_content_type_into_upload(
        self, mock_put
    ):
        mock_put.return_value = MagicMock(
            ok=True, status_code=200)
        before = dict(api_confluence.headers)

        api_confluence.page_payload_write("1", {"title": "t"})

        self.assertEqual(api_confluence.headers, before)
        self.assertEqual(
            mock_put.call_args.kwargs["headers"]["Content-Type"],
            "application/json",
        )
        with tempfile.TemporaryDirectory() as image_dir:
            (Path(image_dir) / "a.png").write_bytes(b"x")
            with patch.object(api_confluence, "PATH_IMAGES", Path(image_dir)):
                api_confluence.image_attachments_upload("1")

        self.assertEqual(mock_put.call_count, 2)
        sent = mock_put.call_args.kwargs["headers"]
        self.assertNotIn("content-type", {k.lower() for k in sent})

    @patch.object(api_confluence.time, "sleep")
    @patch.object(api_confluence.requests, "put")
    def test_retries_upload_on_429(self, mock_put, mock_sleep):
        mock_put.side_effect = [
            MagicMock(ok=False, status_code=429, text="slow",
                      headers={"Retry-After": "0"}),
            MagicMock(ok=True, status_code=200),
        ]
        with tempfile.TemporaryDirectory() as image_dir:
            (Path(image_dir) / "a.png").write_bytes(b"x")
            with patch.object(api_confluence, "PATH_IMAGES", Path(image_dir)):
                api_confluence.image_attachments_upload("1")

        self.assertEqual(mock_put.call_count, 2)
        mock_sleep.assert_called_once_with(0)


def _images(image_dir, *names):
    for name in names:
        (Path(image_dir) / name).write_bytes(b"x")
    return patch.object(api_confluence, "PATH_IMAGES", Path(image_dir))


class TestConfluenceFailureReporting(unittest.TestCase):
    def setUp(self):
        self._orig_headers = dict(api_confluence.headers)
        self.addCleanup(self._restore_headers)

    def _restore_headers(self):
        api_confluence.headers.clear()
        api_confluence.headers.update(self._orig_headers)

    @patch.object(api_confluence.requests, "put")
    def test_upload_returns_failure_for_415(self, mock_put):
        mock_put.return_value = MagicMock(
            ok=False, status_code=415, text="unsupported")
        with tempfile.TemporaryDirectory() as d, _images(d, "a.png"):
            failures = api_confluence.image_attachments_upload("1")

        self.assertEqual(len(failures), 1)
        self.assertIn("a.png", failures[0])
        self.assertIn("415", failures[0])

    @patch.object(api_confluence.requests, "put")
    def test_upload_records_exception_and_continues(self, mock_put):
        mock_put.side_effect = requests.ConnectionError("boom")
        with tempfile.TemporaryDirectory() as d, _images(d, "a.png", "b.png"):
            failures = api_confluence.image_attachments_upload("1")

        self.assertEqual(len(failures), 2)
        self.assertEqual(mock_put.call_count, 2)
        self.assertTrue(all("boom" in f for f in failures))

    @patch.object(api_confluence.requests, "delete")
    @patch.object(api_confluence.requests, "get")
    def test_delete_reports_failures(self, mock_get, mock_delete):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {"results": [{"id": "9"}]})
        mock_delete.return_value = MagicMock(status_code=403, text="no")
        failures = api_confluence.image_attachments_delete("1")

        self.assertEqual(len(failures), 1)
        self.assertIn("9", failures[0])
        self.assertIn("403", failures[0])

    @patch.object(api_confluence.requests, "get")
    def test_delete_reports_list_fetch_failure(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500, text="err")
        failures = api_confluence.image_attachments_delete("1")
        self.assertEqual(len(failures), 1)
        self.assertIn("500", failures[0])

    def _run_pages(self, delete_failures, upload_failures):
        config = {"wiki_page": {"page_title": "T", "page_id": "1",
                                "sections": [{}]}}
        page_data = {"body": {"storage": {"value": ""}},
                     "version": {"number": 1}}
        with patch.object(api_confluence.glob, "glob",
                          return_value=["a.yaml", "b.yaml"]), \
                patch("builtins.open", unittest.mock.mock_open()), \
                patch.object(api_confluence.yaml, "safe_load",
                             return_value=config), \
                patch.object(api_confluence, "image_attachments_list"), \
                patch.object(api_confluence, "image_attachments_delete",
                             return_value=delete_failures), \
                patch.object(api_confluence, "image_attachments_upload",
                             return_value=upload_failures), \
                patch.object(api_confluence, "page_object",
                             return_value=page_data), \
                patch.object(api_confluence, "page_html",
                             return_value="<p>x</p>"), \
                patch.object(api_confluence, "page_payload"), \
                patch.object(api_confluence, "page_payload_write") as write:
            try:
                api_confluence.pages_looker_graphs()
            finally:
                self.write_calls = write.call_count

    def test_exits_1_on_upload_failure_after_all_pages(self):
        with self.assertRaises(SystemExit) as ctx:
            self._run_pages([], ["upload a.png: HTTP 415: x"])
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(self.write_calls, 2)

    def test_exits_1_on_delete_failure(self):
        with self.assertRaises(SystemExit) as ctx:
            self._run_pages(["delete attachment 9: HTTP 403: no"], [])
        self.assertEqual(ctx.exception.code, 1)

    def test_no_exit_when_all_succeed(self):
        self._run_pages([], [])
        self.assertEqual(self.write_calls, 2)

    @patch.object(api_confluence.requests, "delete")
    @patch.object(api_confluence.requests, "get")
    def test_delete_follows_pagination(self, mock_get, mock_delete):
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {
                "results": [{"id": "1"}, {"id": "2"}],
                "_links": {"next": "/next"}}),
            MagicMock(status_code=200, json=lambda: {
                "results": [{"id": "3"}], "_links": {}}),
        ]
        mock_delete.return_value = MagicMock(status_code=204)

        failures = api_confluence.image_attachments_delete("1")

        self.assertEqual(failures, [])
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(
            mock_get.call_args_list[1].kwargs["params"]["start"], 2)
        deleted = [c.args[0].rsplit("/", 1)[1]
                   for c in mock_delete.call_args_list]
        self.assertEqual(deleted, ["1", "2", "3"])
