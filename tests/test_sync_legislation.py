import json
import tempfile
import unittest
from pathlib import Path

from automation.sync_legislation import sync_sources


class SyncLegislationTests(unittest.TestCase):
    def test_sync_detects_new_and_unchanged_records(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rss_path = root / "feed.xml"
            rss_path.write_text(
                """<?xml version=\"1.0\"?>
                <rss><channel>
                  <item>
                    <guid>bill-1</guid>
                    <title>Bill 1</title>
                    <description>First bill</description>
                    <link>https://example.org/b1</link>
                    <pubDate>2026-01-01</pubDate>
                  </item>
                </channel></rss>
                """,
                encoding="utf-8",
            )

            sources = [
                {
                    "name": "fixture-rss",
                    "type": "rss",
                    "url": rss_path.as_uri(),
                }
            ]

            sources_path = root / "sources.json"
            sources_path.write_text(json.dumps(sources), encoding="utf-8")
            output_path = root / "bills.json"
            state_path = root / "state.json"
            updates_path = root / "updates.json"

            first = sync_sources(sources_path, output_path, state_path, updates_path)
            self.assertEqual(first["total_records"], 1)
            self.assertEqual(first["changed_records"], 1)

            second = sync_sources(sources_path, output_path, state_path, updates_path)
            self.assertEqual(second["total_records"], 1)
            self.assertEqual(second["changed_records"], 0)


if __name__ == "__main__":
    unittest.main()
