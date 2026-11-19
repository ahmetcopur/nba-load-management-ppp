"""Fail-closed synthetic tests of independent original NBA announcement extraction.

All NBA schedule PDFs, original WBD/ESPN HTML, individual game tables, and
original research source ZIPs stay PRIVATE: none are uploaded to CI.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.data_rebuild import verify_official_nba_tv_announcements as tv


class OriginalBroadcastSourceTests(unittest.TestCase):
    def test_all_seasons_have_original_first_party_NBA_release_URLs(self):
        self.assertEqual(len(tv.OFFICIAL_RELEASES), 5)
        self.assertEqual(len(tv.OFFICIAL_2020_RELEASES), 6)
        self.assertTrue(all(x.startswith("https://pr.nba.com/")
                            for x in tv.OFFICIAL_RELEASES.values()))
        self.assertTrue(all("espnpressroom.com" in x or "press.wbd.com" in x
                            for x in tv.OFFICIAL_2020_RELEASES.values()))

    def test_original_PDF_and_HTML_source_hashes_are_explicit(self):
        self.assertEqual(len(tv.BROADCAST_PDF_SHA), 5)
        self.assertEqual(len(tv.BROADCAST_HTML_SHA), 6)
        self.assertEqual(len(tv.TEAM), 30)
        self.assertTrue(all(len(s) == 64 for s in
                        list(tv.BROADCAST_PDF_SHA.values()) +
                        list(tv.BROADCAST_HTML_SHA.values())))

    def test_original_2025_streaming_coverage_distinct_from_old_linear_TV(self):
        self.assertIn("NBC/Peacock", tv.PRIMARY_NETWORK["2025-26"])
        self.assertIn("Peacock", tv.PRIMARY_NETWORK["2025-26"])
        self.assertIn("Prime", tv.PRIMARY_NETWORK["2025-26"])
        for season in ("2021-22", "2022-23", "2023-24", "2024-25"):
            self.assertEqual(tv.PRIMARY_NETWORK[season],
                             {"ABC","ABC/ESPN","ESPN","TNT"})
            self.assertNotIn("NBA TV", tv.PRIMARY_NETWORK[season])
        self.assertNotIn("NBA TV", tv.PRIMARY_NETWORK["2025-26"])

    def test_source_pdf_word_layout_extracts_full_2025_first_party_row(self):
        import fitz
        with fitz.open() as doc:
            page=doc.new_page(width=612,height=792)
            for x,word in [(77,"Tue."),(113,"10/21/25"),(183,"Houston"),
                           (248,"at"),(269,"Oklahoma City"),(357,"6:30 PM"),
                           (409,"7:30 PM"),(452,"NBC/Peacock")]:
                page.insert_text((x,150),word,fontsize=8)
            parsed=tv.parse_pdf_rows(doc.tobytes(),"2025-26")
        self.assertEqual(len(parsed),1)
        row=parsed[0]
        self.assertEqual(row["date"],"2025-10-21")
        self.assertEqual(row["away"],"Houston Rockets")
        self.assertEqual(row["home"],"Oklahoma City Thunder")
        self.assertEqual(row["network"],"NBC/Peacock")

    def test_2025_early_local_tip_time_not_mistaken_for_home_team(self):
        import fitz
        with fitz.open() as doc:
            page=doc.new_page(width=612,height=792)
            for x,word in [(77,"Sun."),(113,"12/7/25"),(183,"Orlando"),
                           (248,"at"),(280,"New York"),(348,"12:00"),
                           (378,"PM"),(409,"12:00"),(431,"PM")]:
                page.insert_text((x,150),word,fontsize=8)
            rows=tv.parse_pdf_rows(doc.tobytes(),"2025-26")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["home"],"New York Knicks")
        self.assertEqual(rows[0]["network"],"")

    def test_original_2021_TNT_PDF_still_recognized_as_national(self):
        import fitz
        with fitz.open() as doc:
            page=doc.new_page(width=612,height=792)
            for x,word in [(112,"Tue."),(152,"10/19/21"),(221,"Brooklyn"),
                           (299,"Milwaukee"),(377,"6:30 PM"),
                           (430,"7:30 PM"),(490,"TNT")]:
                page.insert_text((x,150),word,fontsize=8)
            parsed=tv.parse_pdf_rows(doc.tobytes(),"2021-22")
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed[0]["network"],"TNT")

    def test_original_ESPN_2020_release_parser_inherits_blank_dates(self):
        html=b"""<table>
        <tr><th>Date</th><th>Time</th><th>Game</th></tr>
        <tr><td>Wed, Dec 23</td><td>7 PM</td><td>Dallas Mavericks at Phoenix Suns</td></tr>
        <tr><td></td><td>10 PM</td><td>Golden State Warriors at Brooklyn Nets</td></tr>
        </table>"""
        result=tv.parse_2020_html(html,"espn_abc_first")
        self.assertEqual(len(result),2)
        self.assertEqual(result[0]["date"],"2020-12-23")
        self.assertEqual(result[1]["date"],"2020-12-23")
        self.assertEqual(result[1]["network"],"ABC")

    def test_original_2020_flex_TNT_TBD_games_cannot_be_backfilled(self):
        html=b"""<table>
        <tr><th>Day</th><th>Date</th><th>Time</th><th>Game</th></tr>
        <tr><td>Tuesday</td><td>May 11</td><td>7 PM</td><td>TBD vs. TBD</td></tr>
        <tr><td>Tuesday</td><td>May 11</td><td>10 PM</td><td>Boston Celtics vs. Brooklyn Nets</td></tr>
        </table>"""
        result=tv.parse_2020_html(html,"tnt_second")
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["network"],"TNT")
        self.assertEqual(result[0]["away"],"Boston Celtics")

    def test_original_2020_Christmas_platform_is_ABC_not_ABC_ESPN_app(self):
        html=b"""<table><tr><th>Time</th><th>Telecast</th><th>Platform</th></tr>
        <tr><td>5 PM</td><td>Brooklyn Nets at Boston Celtics</td><td>ABC, ESPN App</td></tr>
        <tr><td>8 PM</td><td>Dallas Mavericks at Los Angeles Lakers</td>
            <td>ABC, ESPN, ESPN App</td></tr></table>"""
        # Historical ESPN press page uses its fourth table for Christmas;
        # add three distinct placeholder tables to preserve page structure.
        pre=b"<table><tr><th>Date</th></tr></table>"*3
        result=tv.parse_2020_html(pre+html,"espn_abc_first")
        self.assertEqual([r["network"] for r in result],["ABC","ABC/ESPN"])

    def test_full_2020_broadcast_counts_must_fail_closed_when_missing(self):
        with self.assertRaisesRegex(ValueError,"2020 49\\+46"):
            tv.source_2020_counts([{
                "source_key":"nbatv_first","segment":"first_half",
                "date":"2020-12-26","away":"Atlanta Hawks",
                "home":"Memphis Grizzlies","network":"NBA TV"
            }])

    def test_source_2020_early_2021_month_date_is_not_in_2020(self):
        self.assertEqual(tv.parse_2020_date("Wed, Jan 6"),"2021-01-06")
        self.assertEqual(tv.parse_2020_date("Dec. 22"),"2020-12-22")
        self.assertEqual(tv.parse_2020_date(""),None)

    def test_incomplete_private_source_archives_fail_before_reading_an_NBA_row(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            source=root/"incomplete-inventory.zip"
            final=root/"incomplete-original-freeze.zip"
            source.write_bytes(b"not the genuine original archive")
            final.write_bytes(b"not the genuine original frozen archive")
            with self.assertRaisesRegex(ValueError,"source inventory ZIP SHA"):
                tv.verify_original_sources(source,final)

    def test_2020_second_half_NBA_TV_is_never_inferred_from_highlights_page(self):
        self.assertIn("nbatv_second",tv.BROADCAST_HTML_SHA)
        self.assertNotIn("NBA TV",tv.PRIMARY_NETWORK["2025-26"])


if __name__=="__main__":
    unittest.main()
