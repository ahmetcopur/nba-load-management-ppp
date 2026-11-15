from pathlib import Path
import tempfile
import unittest
import pandas as pd
from scripts.data_rebuild.experiment_2025_team_metadata import compare_csv, compare_models, require_team_only_difference, tree_hashes, stage, resumed_identity
from scripts.data_rebuild.generate_2025_selector_inputs import generate


class MetadataExperimentTests(unittest.TestCase):
    def test_equal_counts_do_not_hide_changed_scientific_cells(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/"a.csv",Path(folder)/"b.csv"
            a.write_text("id,onset\n1,True\n2,False\n"); b.write_text("id,onset\n1,False\n2,True\n")
            result=compare_csv(a,b,["id"])
            self.assertFalse(result["exact_decoded_bytes"])
            self.assertEqual(result["differences_by_column"],{"onset":2})

    def test_keyed_cell_equality_does_not_claim_exact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/"a.csv",Path(folder)/"b.csv"
            a.write_text("id,x\n1,a\n2,b\n");b.write_text("id,x\n2,b\n1,a\n")
            result=compare_csv(a,b,["id"])
            self.assertFalse(result["exact_decoded_bytes"])
            self.assertFalse(result["row_order_equal"])
            self.assertEqual(result["differing_cells"],0)

    def test_duplicate_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"a.csv";p.write_text("id,x\n1,a\n1,b\n")
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                compare_csv(p,p,["id"])

    def test_changed_observability_rejects_otherwise_valid_experiment(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/"a.csv",Path(folder)/"b.csv"
            frame=pd.DataFrame({"game_id":range(1598),"team_role":["home"]*1598,
                "team_final_status":["inferred"]*1598,"inferred_no_listed_players":[True]*1598,
                "usable_submitted_status":[True]*1598})
            frame.to_csv(a,index=False)
            frame["team_final_status"]="submitted";frame["inferred_no_listed_players"]=False;frame.to_csv(b,index=False)
            self.assertEqual(require_team_only_difference(a,b)["differing_cells"],3196)
            frame.loc[0,"usable_submitted_status"]=False;frame.to_csv(b,index=False)
            with self.assertRaisesRegex(ValueError,"beyond"):
                require_team_only_difference(a,b)

    def test_diagnostic_export_cannot_claim_strict_selector_acceptance(self):
        with self.assertRaisesRegex(ValueError,"audit-only"):
            generate(Path("missing"),Path("missing"),Path("missing"),diagnostic_frames={})

    def test_input_fingerprint_detects_drift_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/"input.csv";p.write_text("first")
            before=tree_hashes(root);p.write_text("changed")
            self.assertNotEqual(before,tree_hashes(root))
            (root/"link").symlink_to(p)
            with self.assertRaisesRegex(ValueError,"symlink"):
                tree_hashes(root)

    def test_resume_rejects_changed_stage_outputs(self):
        import sys
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/"stage"
            cmd=[sys.executable,"-c",f"from pathlib import Path;p=Path({str(out)!r});p.mkdir();(p/'data').write_text('original')"]
            first=stage(root,"test",cmd,out,False)
            self.assertEqual(stage(root,"test",cmd,out,True),first)
            (out/"data").write_text("tampered")
            with self.assertRaisesRegex(ValueError,"checkpoint"):
                stage(root,"test",cmd,out,True)

    def test_only_original_runtime_seconds_can_differ_between_models(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/"a.csv",Path(folder)/"b.csv"
            rows=[{"definition":d,"controls":c,"n":10,"estimate_pp":"1.23456789012345","seconds":1}
                  for d in ("legacy_primary","harmonized_linear") for c in ("full","none")]
            frame=pd.DataFrame(rows);frame.to_csv(a,index=False)
            frame["seconds"]=2;frame.to_csv(b,index=False)
            result=compare_models(a,b)
            self.assertFalse(result["exact_decoded_bytes"])
            self.assertTrue(result["scientific_model_cells_exact"])
            frame.loc[0,"estimate_pp"]="1.23456789012346";frame.to_csv(b,index=False)
            with self.assertRaisesRegex(ValueError,"Scientific model"):
                compare_models(a,b)

    def test_resume_cannot_ignore_unknown_code_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,"identity changed"):
                resumed_identity({"code_hashes":{"unknown":"old"}},
                                 {"code_hashes":{"unknown":"new"}},Path(folder))


if __name__=="__main__":unittest.main()
