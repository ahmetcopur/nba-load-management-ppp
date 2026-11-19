import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.data_rebuild import run_historical_cadence_builder as builder


class ConsumptionTests(unittest.TestCase):
    def execute(self, consume=True, tamper=False):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/"generated.csv"
            source.write_text("fresh source\n")
            hashes=root/"required.json"
            hashes.write_text(json.dumps({"generated.csv":hashlib.sha256(source.read_bytes()).hexdigest()}))
            if tamper:
                source.write_text("changed\n")
            script=root/"original.py"
            script.write_text(
                "from pathlib import Path\nROOT=Path('/mnt/data/nba_continue')\n"
                "OUT=ROOT/'cadence_harmonized_results'; OUT.mkdir(exist_ok=True)\n"
                + ("data=(ROOT/'generated.csv').read_text()\n" if consume else "data='fallback'\n"))
            out=root/"result"
            with patch.object(builder,"SCRIPT",script), patch.object(builder,"NEEDED",[]), \
                 patch.object(sys,"argv",["builder","--historical-root",str(root),"--output",str(out),
                                          "--required-input-hashes",str(hashes)]):
                builder.main()
            return json.loads((out/"replay_environment.json").read_text())

    def test_original_subprocess_open_is_observed(self):
        result=self.execute()
        self.assertEqual(result["generated_input_consumption"]["original_builder_opened_paths"],["generated.csv"])

    def test_fallback_without_open_blocks_acceptance(self):
        with self.assertRaisesRegex(ValueError,"did not open"):
            self.execute(consume=False)

    def test_changed_source_blocks_before_execution(self):
        with self.assertRaisesRegex(ValueError,"SHA-256 differs"):
            self.execute(tamper=True)


if __name__=="__main__":
    unittest.main()
