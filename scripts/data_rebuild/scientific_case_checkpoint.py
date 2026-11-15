"""Revalidate completed private cases before reusing an interrupted run.

Never accepts a bare panel or fabricates a successful subprocess receipt.
"""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pandas as pd


def check_reported_models(path,reported):
    if pd.read_csv(path).to_dict('records')!=reported:
        raise ValueError('Checkpoint reported model values differ from actual CSV')


def reuse_case(previous,commit,phase,version,hashes,destination):
    from scripts.data_rebuild import reproduce_october_scientific_v2 as run
    if destination.exists():raise FileExistsError(destination)
    old=previous/(phase+'__'+version);manifest=old/'case_manifest.json'
    if not manifest.is_file():return None
    if previous.is_symlink() or old.is_symlink():raise ValueError('Symlinked case checkpoint')
    # Exactly the same scientific helpers and execution/model functions must
    # have been used. Orchestration may acquire explicit resume/error reporting.
    paths=['scripts/data_rebuild/october_scientific_v2_rules.py',
           'scripts/data_rebuild/october_scientific_v2_compare.py',
           'scripts/data_rebuild/audit_star_status_against_calendar.py',
           'scripts/executed/06_cadence_harmonized_identification/build_harmonized_panel_and_models.py',
           'scripts/executed/06_cadence_harmonized_identification/run_cadence_models_fast.py']
    for path in paths:
        data=subprocess.check_output(['git','show',commit+':'+path],cwd=run.REPO)
        if hashlib.sha256(data).hexdigest()!=run.sha(run.REPO/path):raise ValueError('Checkpoint scientific code differs')
    path='scripts/data_rebuild/reproduce_october_scientific_v2.py'
    def functions(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
    previous_functions=functions(subprocess.check_output(['git','show',commit+':'+path],cwd=run.REPO).decode())
    current=functions((run.REPO/path).read_text())
    for name in ('execute','audit_prefix','run_models','sample_identities','verify_panel_identity','require_semantics','verify_legacy_models','model_deltas'):
        if previous_functions[name]!=current[name]:raise ValueError('Checkpoint computation/verification functions differ')
    c=json.loads(manifest.read_text());receipt=json.loads((old/'execution_receipt.json').read_text())
    expected_source=run.rules.render_source(run.SOURCE.read_bytes(),version)
    if (c['phase']!=phase or c['scientific_version']!=version or c['builder']!=receipt
        or receipt['required_input_sha256']!=hashes
        or receipt['canonical_source_sha256']!=hashlib.sha256(expected_source).hexdigest()
        or receipt['executed_sha256']!=run.sha(old/'builder.py')
        or receipt['pre_and_post_hashes_equal'] is not True):raise ValueError('Checkpoint builder source/receipt/input identity differs')
    if json.loads((old/'opened_inputs.json').read_text())!=receipt['actual_opened_inputs']:
        raise ValueError('Checkpoint builder read trace differs')
    if not set(hashes)-{'cadence_work/player_alias_table.csv'}<=set(receipt['actual_opened_inputs']):
        raise ValueError('Checkpoint did not consume all required inputs')
    original_inputs=previous/('inputs_frozen' if phase=='frozen' else 'inputs_chronology')
    run.legacy.verify_required_inputs(original_inputs,hashes)
    panel=old/run.PANEL;stats=run.summary(panel)
    if stats!=c['panel']:raise ValueError('Checkpoint panel changed')
    run.verify_panel_identity(stats,phase,version)
    run.require_semantics(panel,original_inputs/run.CALENDAR,run.rules.VERSIONS[version][0])
    models=c['four_models'];model_root=old/'models'
    full=model_root/'inputs/cadence_harmonized_results/cadence_harmonized_model_results.csv'
    if run.identities(full)!=models['complete_result_csv'] or run.identities(model_root/'model_results_scientific.csv')!=models['scientific_result_csv']:
        raise ValueError('Checkpoint model tables changed')
    check_reported_models(full,models['models'])
    if run.sample_identities(panel)!=models['samples']:raise ValueError('Checkpoint model sample differs')
    model_receipt=json.loads((model_root/'execution/execution_receipt.json').read_text())
    if model_receipt!=models['execution'] or model_receipt['executed_sha256']!=run.sha(model_root/'execution/original_fast_models.py'):
        raise ValueError('Checkpoint model executable/receipt changed')
    if json.loads((model_root/'execution/opened_inputs.json').read_text())!=model_receipt['actual_opened_inputs']:
        raise ValueError('Checkpoint model read trace differs')
    if run.identities(model_root/'inputs/cadence_harmonized_results'/run.PANEL)!=run.identities(panel):
        raise ValueError('Checkpoint models did not use that complete panel')
    if version=='legacy':run.verify_legacy_models(models['models'],phase)
    else:
        baseline=previous/(phase+'__legacy')
        for name,h in c['unchanged_auxiliary_output_sha256'].items():
            if run.identities(old/name)['decoded_sha256']!=h or run.identities(baseline/name)['decoded_sha256']!=h:
                raise ValueError('Checkpoint auxiliary changed')
        permitted=({'star_PPP_it'} if run.rules.VERSIONS[version][0] else set())|(set(run.rules.WORKLOAD_COLUMNS) if run.rules.VERSIONS[version][1] else set())
        if run.compare(baseline/run.PANEL,panel,permitted)!=c['vs_legacy']:raise ValueError('Checkpoint whole-cell differences changed')
    shutil.copytree(old,destination)
    c['reused_completed_case']={'original_code_commit':commit,'previous_case_manifest_sha256':run.sha(manifest),
                               'all_scientific_helpers_and_computation_functions_equal':True,'actual_original_execution_receipts_revalidated':True}
    return c
