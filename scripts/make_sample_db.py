"""Generates a synthetic algae-farm SQLite database.   run: python scripts/make_sample_db.py"""
import sqlite3, pathlib, sys, numpy as np, pandas as pd

def build(path='data/sample.db', seed=7):
    rng = np.random.default_rng(seed)
    pathlib.Path(path).parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript('''
    DROP TABLE IF EXISTS strains; DROP TABLE IF EXISTS ponds; DROP TABLE IF EXISTS harvests; DROP TABLE IF EXISTS daily;
    CREATE TABLE strains (id INTEGER PRIMARY KEY, name TEXT, optimum_temp_c REAL);
    CREATE TABLE ponds (id INTEGER PRIMARY KEY, name TEXT, strain_id INT, volume_l REAL, location TEXT);
    CREATE TABLE harvests (id INTEGER PRIMARY KEY, pond_id INT, harvest_date TEXT, dry_mass_g REAL);
    CREATE TABLE daily (date TEXT, pond_id INT, temp_c REAL, ph REAL, par_mean REAL, od750 REAL);
    ''')
    strains = [(1, 'Chlorella vulgaris', 30), (2, 'Nannochloropsis', 25), (3, 'Scenedesmus', 28)]
    conn.executemany('INSERT INTO strains VALUES (?,?,?)', strains)
    ponds = [(i, f'Pond {i:02d}', int(rng.integers(1, 4)), float(rng.choice([500, 1000, 5000])),
              str(rng.choice(['North field', 'South field', 'Greenhouse']))) for i in range(1, 13)]
    conn.executemany('INSERT INTO ponds VALUES (?,?,?,?,?)', ponds)
    days = pd.date_range('2025-01-01', '2025-12-31')
    rows, hv, hid = [], [], 1
    for pid, _, sid, vol, loc in ponds:
        od = 0.2
        for d in days:
            season = np.sin(2 * np.pi * (d.dayofyear - 80) / 365)
            temp = 24 + 9 * season + rng.normal(0, 1.5) + (3 if loc == 'Greenhouse' else 0)
            par = max(0, 900 + 600 * season + rng.normal(0, 120))
            opt = strains[sid - 1][2]
            mu = 0.35 * np.exp(-((temp - opt) / 7) ** 2) * min(1, par / 800)
            od = max(0.1, od * (1 + mu * (1 - od / 3.5) - 0.05) + rng.normal(0, 0.02))
            rows.append((d.strftime('%Y-%m-%d'), pid, round(temp, 2), round(7.4 + rng.normal(0, .25), 2), round(par, 1), round(od, 3)))
            if od > 2.8:                                   # harvest 60 percent and dilute
                hv.append((hid, pid, d.strftime('%Y-%m-%d'), round(0.6 * od * 0.85 * vol, 1))); hid += 1; od *= 0.4
    conn.executemany('INSERT INTO daily VALUES (?,?,?,?,?,?)', rows)
    conn.executemany('INSERT INTO harvests VALUES (?,?,?,?)', hv)
    conn.commit(); conn.close()
    return len(rows), len(hv)

if __name__ == '__main__':
    n, h = build()
    print(n, 'daily rows,', h, 'harvests')
