"""Explicit scientific corrections; never imported by historical commands."""
from __future__ import annotations
import hashlib
import numbers
from pathlib import Path
import numpy as np
import pandas as pd

ORIGINAL_SHA256 = '81cab67185083572051b44cefbf836acfe6e1860ccf27dd812dc3729aa2a9272'
VERSIONS = {
    'legacy': (False, False),
    'october_scientific_v2': (True, False),
    'october_workload_physical_sensitivity_v1': (False, True),
    'october_scientific_v2_physical_sensitivity_v1': (True, True),
}
WORKLOAD_COLUMNS = ['games_played_before_game_harm',
                    'minutes_sum_prior_10_roster_games_harm', 'dist_to_65_before_game_harm']
KEYS = ['season', 'nba_player_id']


def strict_bool(value, label='boolean'):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, numbers.Real) and pd.notna(value) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in ('true', 'false', '1', '0', '1.0', '0.0'):
        return value.strip().lower() in ('true', '1', '1.0')
    raise ValueError(f'Missing or invalid {label}')


def eligible(opening, selected, effective, date):
    opening, selected = strict_bool(opening, 'opening star'), strict_bool(selected, 'current All-Star selection')
    when = pd.to_datetime(date, errors='raise')
    if pd.isna(when):
        raise ValueError('Missing game date')
    eff = pd.to_datetime(effective, errors='raise') if pd.notna(effective) and str(effective).strip() else pd.NaT
    if selected and pd.isna(eff):
        raise ValueError('Selected current All-Star is missing an effective date')
    return opening or (selected and pd.notna(eff) and when >= eff)


def load_calendar(path):
    c = pd.read_csv(path, dtype={'season': str, 'nba_player_id': 'Int64'})
    required = KEYS + ['star_at_opening_night', 'current_season_all_star', 'current_all_star_effective_date']
    if not set(required) <= set(c) or c[KEYS].isna().any().any() or c.duplicated(KEYS).any():
        raise ValueError('Calendar columns/identities missing or duplicated')
    if c.season.str.strip().eq('').any() or c.nba_player_id.le(0).any():
        raise ValueError('Invalid calendar identity')
    for col in ['star_at_opening_night', 'current_season_all_star']:
        c[col] = c[col].map(lambda v: strict_bool(v, col))
    c['current_all_star_effective_date'] = pd.to_datetime(c.current_all_star_effective_date, errors='raise')
    if (c.current_season_all_star & c.current_all_star_effective_date.isna()).any():
        raise ValueError('Selected current All-Star is missing an effective date')
    return c.set_index(KEYS)


def star_for_player(calendar, season, player, date):
    number = pd.to_numeric(player, errors='raise')
    if pd.isna(number) or number <= 0 or number % 1:
        raise ValueError('Invalid player identity')
    key = (str(season), int(number))
    if key not in calendar.index:
        raise ValueError('Player-season missing from authoritative star calendar')
    row = calendar.loc[key]
    return eligible(row.star_at_opening_night, row.current_season_all_star,
                    row.current_all_star_effective_date, date)


def flags_for_frame(frame, calendar):
    # Only the three identity/date columns are joined; preserve the caller's index.
    m = frame[KEYS + ['game_date_et']].merge(calendar.reset_index(), on=KEYS,
                                           how='left', validate='many_to_one', indicator=True)
    if not m._merge.eq('both').all():
        raise ValueError('Player-season missing from authoritative star calendar')
    date = pd.to_datetime(m.game_date_et, errors='raise')
    if date.isna().any():
        raise ValueError('Missing game date')
    flags = m.star_at_opening_night | (m.current_season_all_star & date.ge(m.current_all_star_effective_date))
    return pd.Series(flags.to_numpy(dtype=bool), index=frame.index)


def physical_history(frame):
    """Sensitivity: prior 10 distinct physical games in observed player history.

    Multiple team associations for ONE physical game receive identical histories.
    No unobserved games are invented. Conflicting minutes or simultaneous distinct
    games require review; arbitrary sorting is never used to resolve them.
    """
    key = ['nba_player_id', 'season', 'game_id']
    f = frame[key + ['tip_utc', 'game_date_et', 'minutes_played', 'played_bool']].copy()
    if f[key].isna().any().any():
        raise ValueError('Missing workload history identity')
    f['tip_utc'] = pd.to_datetime(f.tip_utc, utc=True, errors='raise')
    if f.tip_utc.isna().any() or f.game_date_et.isna().any():
        raise ValueError('Missing physical-game tip time')
    f['played_bool'] = f.played_bool.map(strict_bool)
    f['minutes_played'] = pd.to_numeric(f.minutes_played, errors='raise').fillna(0)
    if (~np.isfinite(f.minutes_played) | f.minutes_played.lt(0)).any():
        raise ValueError('Invalid workload minutes')
    grouped = f.groupby(key, sort=False)
    if (grouped.tip_utc.nunique().gt(1) | grouped.game_date_et.nunique().gt(1)).any():
        raise ValueError('Conflicting physical-game chronology')
    if f[f.minutes_played.gt(0)].groupby(key).minutes_played.nunique().gt(1).any():
        raise ValueError('Conflicting physical-game minutes')
    u = grouped.agg(tip_utc=('tip_utc','first'), minutes=('minutes_played','max'), played=('played_bool','max')).reset_index()
    if u.duplicated(['nba_player_id','season','tip_utc']).any():
        raise ValueError('Simultaneous distinct physical games require review')
    u = u.sort_values(['nba_player_id','season','tip_utc','game_id'])
    g = u.groupby(['nba_player_id','season'], sort=False)
    u[WORKLOAD_COLUMNS[0]] = g.played.transform(lambda s: s.astype(int).cumsum().shift(fill_value=0))
    u[WORKLOAD_COLUMNS[1]] = g.minutes.transform(lambda s: s.shift(1).rolling(10,min_periods=1).sum())
    u[WORKLOAD_COLUMNS[2]] = 65 - u[WORKLOAD_COLUMNS[0]]
    result = frame[key].merge(u[key + WORKLOAD_COLUMNS], on=key, how='left', validate='many_to_one')
    return pd.DataFrame({c: result[c].to_numpy() for c in WORKLOAD_COLUMNS}, index=frame.index)


def render_source(original: bytes, version: str) -> bytes:
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256:
        raise ValueError('Original October builder SHA-256 differs')
    star, workload = VERSIONS[version]
    if version == 'legacy':
        return original
    source = original.decode()
    def replace(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise ValueError('Pinned scientific patch context changed')
        source = source.replace(old, new, 1)
    imports = ('from scripts.data_rebuild.october_scientific_v2_rules import '
               'load_calendar as _v2_load, flags_for_frame as _v2_flags, '
               'star_for_player as _v2_star, physical_history as _v2_history\n')
    if star:
        replace('roster=base[base.from_boxscore_roster].copy()',
                "_v2_calendar=_v2_load(ROOT/'scientific/star_calendar.csv')\n"
                'roster=base[base.from_boxscore_roster].copy()\n'
                "roster['star_PPP_it']=_v2_flags(roster,_v2_calendar)")
        replace("        opening=bool(ps.get('star_at_opening_night',False))\n"
                "        eff=pd.to_datetime(ps.get('current_all_star_effective_date'),errors='coerce')\n"
                "        gd=pd.to_datetime(row['game_date_et'])\n"
                "        row['star_PPP_it']=opening or (pd.notna(eff) and gd>=eff)",
                "        row['star_PPP_it']=_v2_star(_v2_calendar,r.season,r.nba_player_id,row['game_date_et'])")
        replace("    else:\n        row['star_PPP_it']=False\n    extra_rows.append(row)",
                "    else:\n        row['star_PPP_it']=_v2_star(_v2_calendar,r.season,r.nba_player_id,row['game_date_et'])\n    extra_rows.append(row)")
    if workload:
        marker="panel['dist_to_65_before_game_harm']=65-panel.games_played_before_game_harm"
        replace(marker, marker + '\n_v2_work=_v2_history(panel)\n'
                'for _v2_col in _v2_work: panel[_v2_col]=_v2_work[_v2_col]')
    marker='# Model: player + team-season FE, full controls, two-way player/game clustering.'
    replace(marker, '# Versioned panel-only boundary; the separately pinned original fast models run next.\n'
            'raise SystemExit(0)\n'+marker)
    return (imports + source).encode()
