import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts.data_rebuild import reproduce_final_datasets as final
from scripts.data_rebuild import rebuild_six_season_october_sources as six
from scripts.data_rebuild.fixture_date_chronology_sensitivity import chronology_generated_hashes, SEL
from scripts.data_rebuild.inject_2021_generated_inputs import exact_csv_rows


class SixSeasonTests(unittest.TestCase):
    def test_byte_identity_fast_path_checks_every_CSV_record_without_pandas(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a.csv',Path(folder)/'b.csv'
            a.write_text('id,reason\n1,"two\nlines"\n2,other\n');b.write_bytes(a.read_bytes())
            self.assertTrue(exact_csv_rows(a,b,2))
            with self.assertRaisesRegex(ValueError,'row count'):exact_csv_rows(a,b,3)
            b.write_text('id,reason\n1,different\n2,other\n')
            self.assertFalse(exact_csv_rows(a,b,2))

    def test_canonical_plan_connects_sources_before_both_builders(self):
        plan=final.stage_commands(Path('/sources'),Path('/output'),verify_original_pdfs=True,six_season_sources=True)
        names=[name for name,_ in plan];commands=dict(plan)
        self.assertLess(names.index('00c_six_season_original_PDF_sources'),names.index('03_frozen_cadence'))
        self.assertIn('--emit-full-2020-source-rows',commands['00_independent_original_six_pdf_baseline'])
        self.assertIn('--six-season-sources-dir',commands['03_frozen_cadence'])
        self.assertIn('--chronology-adjusted-generated-inputs',commands['04_corrected_cadence'])
        self.assertIn('--required-input-hashes',commands['04_corrected_cadence'])
        self.assertNotIn('--skip-2025-parse',commands['03_frozen_cadence'])

    def test_six_source_mode_cannot_silently_use_legacy_or_missing_PDF_mode(self):
        for options in ({'verify_original_pdfs':False},{'verify_original_pdfs':True,'raw_2020_selector':True},
                        {'verify_original_pdfs':True,'rebuild_2020_2024_selectors':True}):
            with self.assertRaisesRegex(ValueError,'Six-season'):
                final.stage_commands(Path('/sources'),Path('/output'),six_season_sources=True,**options)

    def test_source_archive_hash_is_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'source.zip';p.write_bytes(b'authentic fixture')
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            with patch.object(final,'SOURCE_HASHES',{'source.zip':digest}),patch.object(final,'SELECTOR_SCHEDULE_EXTRA_ZIPS',{}),patch.object(six,'EXTRA_ZIPS',{}):
                self.assertEqual(six.originals(root),{'source.zip':digest})
                p.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'SHA differs'):six.originals(root)
                p.unlink()
                with self.assertRaisesRegex(ValueError,'missing'):six.originals(root)

    def test_reused_source_and_generated_selector_hashes_are_both_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';generated=root/'generated';source.mkdir();generated.mkdir()
            (source/'rows.csv').write_text('fresh rows');(generated/'selector.csv').write_text('fresh selector')
            record={'source':str(source),'generated':str(generated),'source_sha256':six.tree_hashes(source),'generated_sha256':six.tree_hashes(generated)}
            self.assertEqual(six.checked_season(record),(source,generated))
            (generated/'selector.csv').write_text('archived fallback')
            with self.assertRaisesRegex(ValueError,'changed or missing'):six.checked_season(record)

    def test_incomplete_season_manifest_rejects_fallback_before_injection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';source.mkdir();historical=root/'historical';historical.mkdir()
            (source/'six_season_sources.json').write_text(json.dumps({'all_six_source_inputs_ready':True,'cases':{}}))
            with patch.object(six,'originals',return_value={}),patch.object(six,'controlled_exception',return_value={}):
                with self.assertRaisesRegex(ValueError,'All six'):six.inject(root,source,historical)
            self.assertEqual(list(historical.iterdir()),[])

    def test_unpinned_2025_exception_evidence_is_not_accepted(self):
        with patch.object(six,'file_sha256',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'evidence differs'):six.controlled_exception()

    def test_all_18_actual_opens_and_hashes_are_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'result';out.mkdir();wanted={}
            for n in range(18):
                p=root/f'input-{n}.csv';p.write_text('fresh input');wanted[p.name]=six.file_sha256(p)
            (root/'six_season_source_handoff.json').write_text(json.dumps({'all_six_source_inputs_injected':True,'required_input_sha256':wanted}))
            actual={'required_sha256':wanted,'original_builder_opened_paths':list(wanted),'pre_and_post_execution_hashes_match':True}
            env=out/'replay_environment.json';env.write_text(json.dumps({'generated_input_consumption':actual}))
            self.assertEqual(six.consumption(root,out),actual)
            actual['original_builder_opened_paths'].pop();env.write_text(json.dumps({'generated_input_consumption':actual}))
            with self.assertRaisesRegex(ValueError,'all 18'):six.consumption(root,out)
            (root/'input-0.csv').write_text('changed')
            with self.assertRaisesRegex(ValueError,'SHA-256'):six.consumption(root,out)

    def test_chronology_cannot_change_a_third_generated_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);names=[SEL+'/2021-22_game_snapshot_join_harmonized_canonical.csv',
                SEL+'/2021-22_team_game_status_harmonized_canonical.csv',*[f'rows-{n}.csv' for n in range(16)]]
            before={}
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('original');before[name]=six.file_sha256(p)
            for name in names[:2]:(root/name).write_text('documented correction')
            after=chronology_generated_hashes(root,before)
            self.assertEqual({k for k in before if before[k]!=after[k]},set(names[:2]))
            (root/names[2]).write_text('unexpected rows')
            with self.assertRaisesRegex(ValueError,'Unexpected'):chronology_generated_hashes(root,before)

    def test_real_cli_lists_six_source_inputs_from_clean_script_entry(self):
        result=subprocess.run([sys.executable,str(final.TOOLS/'reproduce_final_datasets.py'),'--list-inputs'],capture_output=True,text=True,check=True)
        data=json.loads(result.stdout)
        self.assertEqual(set(data['additional_if_rebuilding_six_season_october_sources']),set(six.EXTRA_ZIPS))


if __name__=='__main__':unittest.main()
