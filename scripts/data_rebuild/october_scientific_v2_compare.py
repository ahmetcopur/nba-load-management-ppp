"""Bounded-memory, complete-cell comparisons for explicit scientific versions."""
from __future__ import annotations
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

KEY = 'player_team_game_id'


def open_csv(path):
    return gzip.open(path, 'rt', newline='') if str(path).endswith('.gz') else path.open(newline='')


def identities(path):
    raw = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1<<20), b''): raw.update(block)
    decoded = hashlib.sha256()
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rb') as f:
        for block in iter(lambda: f.read(1<<20), b''): decoded.update(block)
    return {'compressed_sha256':raw.hexdigest(), 'decoded_sha256':decoded.hexdigest(),
            'bytes':path.stat().st_size}


def bit(value):
    if value not in ('True','False'): raise ValueError('Unexpected serialized scientific boolean')
    return value == 'True'


def summary(path):
    games, players, seasons = set(), set(), set()
    counts = Counter(); cells = Counter()
    with open_csv(path) as f:
        reader = csv.DictReader(f); columns = reader.fieldnames
        for r in reader:
            counts['rows'] += 1; games.add(r['game_id']); players.add(r['nba_player_id']); seasons.add(r['season'])
            risk,onset,star = (bit(r[c]) for c in ['at_risk_for_new_onset_harm','absence_onset_harm','star_PPP_it'])
            if onset and not risk: raise ValueError('Onset outside risk set')
            counts['risk'] += risk; counts['onsets'] += onset
            counts['star_risk'] += star and risk; counts['nonstar_risk'] += not star and risk
            counts['star_onsets'] += star and onset; counts['nonstar_onsets'] += not star and onset
            if risk:
                key=(star,bit(r['postPPP']),bit(r['announced_tv_primary']))
                cells[key+('risk',)] += 1; cells[key+('onset',)] += onset
    raw_cells=[{'star':s,'post':p,'tv':t,'risk':cells[s,p,t,'risk'],'onsets':cells[s,p,t,'onset']}
               for s in (False,True) for p in (False,True) for t in (False,True)]
    return {**dict(counts),'games':len(games),'players':len(players),'seasons':sorted(seasons),
            'columns':columns,'raw_eight_cells':raw_cells,**identities(path)}


def compare(left: Path, right: Path, allowed: set[str] | None, diff_path: Path | None=None):
    """SQLite disk join checks all keys/cells, independent of CSV row order.

    If allowed is None this is an unrestricted diagnostic, NOT acceptance.
    Full keyed differences, if requested, stay in the private execution folder.
    """
    changed_cols=Counter(); seasons=Counter(); rows=cells=0
    with tempfile.TemporaryDirectory(prefix='nba_scientific_compare_') as temp:
        db=sqlite3.connect(Path(temp)/'keys.sqlite')
        db.execute('PRAGMA cache_size=-16000')
        db.execute('CREATE TABLE ref (key TEXT PRIMARY KEY, value TEXT, seen INTEGER DEFAULT 0)')
        with open_csv(left) as f:
            a=csv.DictReader(f); fields=a.fieldnames
            if not fields or KEY not in fields or len(set(fields))!=len(fields): raise ValueError('Invalid reference schema')
            try:
                for r in a:
                    if not r[KEY]:raise ValueError('Missing reference key')
                    db.execute('INSERT INTO ref(key,value) VALUES(?,?)',(r[KEY],json.dumps(r)))
            except sqlite3.IntegrityError as e:raise ValueError('Duplicate reference key') from e
        n=db.execute('SELECT COUNT(*) FROM ref').fetchone()[0]
        db.commit()
        out=diff_path.open('x') if diff_path else None
        try:
            with open_csv(right) as f:
                b=csv.DictReader(f)
                if b.fieldnames!=fields: raise ValueError('Scientific schema or column order changed')
                count=0
                for r in b:
                    count+=1; item=db.execute('SELECT value,seen FROM ref WHERE key=?',(r[KEY],)).fetchone()
                    if item is None:raise ValueError('Unexpected candidate key')
                    if item[1]:raise ValueError('Duplicate candidate key')
                    db.execute('UPDATE ref SET seen=1 WHERE key=?',(r[KEY],))
                    old=json.loads(item[0]); changes={c:[old[c],r[c]] for c in fields if old[c]!=r[c]}
                    if allowed is not None and set(changes)-allowed:
                        raise ValueError('Unauthorized scientific column change: '+str(sorted(set(changes)-allowed)))
                    if changes:
                        rows+=1; cells+=len(changes); changed_cols.update(changes.keys()); seasons[r.get('season','')]+=1
                        if out:out.write(json.dumps({KEY:r[KEY],'changes':changes})+'\n')
            if count!=n or db.execute('SELECT COUNT(*) FROM ref WHERE seen=0').fetchone()[0]:
                raise ValueError('Missing candidate keys')
        finally:
            if out:out.close()
            db.close()
    return {'rows':n,'unique_keys':n,'same_schema':True,'changed_rows':rows,'changed_cells':cells,
            'changed_columns':dict(changed_cols),'affected_seasons':dict(seasons),
            'comparison':'exact decoded CSV cells by stable key; output hashes separately retain row order'}
