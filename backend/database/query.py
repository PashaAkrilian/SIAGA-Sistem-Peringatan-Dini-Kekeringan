import sqlite3 
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "siaga.db"

# row_factory = row supaya hasil bisa diakses dipakai nama kolom: row["sdci"]
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def show (title, sql, params=()):
    rows = cur.execute(sql, params).fetchall()
    if not rows:
        print(f"{title}: tidak ada data")
        return rows
    # Cetak nama kolom sebagai header
    print(" | ".join(rows[0].keys()))
    # Cetak tiap baris 
    for r in rows:
        print(" | ".join(str(r[k]) for k in r.keys()))

show(
    "[1] Daftar semua pulau",
    "SELECT id, code, name FROM islands",
)

show(
    "[2] 5 bulan dengan ONI tertinggi (El Nino terkuat)",
    "SELECT date_key, oni, sst_anomaly "
    "FROM ocean_readings "
    "ORDER BY oni DESC "
    "LIMIT 5",
)

show(
    "[3] Bulan-bulan Jawa dengan SDCI < 0.3 (kekeringan ekstrem)",
    "SELECT ir.date_key, ROUND(ir.sdci, 3) AS sdci "
    "FROM island_readings ir "
    "JOIN islands i ON ir.island_id = i.id "
    "WHERE i.code = 'Jawa' AND ir.sdci < 0.3 "
    "ORDER BY ir.sdci ASC",
)

show(
    "[4] Rata-rata SDCI tiap pulau (2000-2025)",
    "SELECT i.name, ROUND(AVG(ir.sdci), 3) AS rata_sdci, COUNT(*) AS n_bulan "
    "FROM island_readings ir "
    "JOIN islands i ON ir.island_id = i.id "
    "GROUP BY i.id "
    "ORDER BY rata_sdci ASC",
)

show(
    "[5] Potret Oktober 2015 (puncak Godzilla El Nino): SDCI semua pulau",
    "SELECT i.name, ROUND(ir.sdci, 3) AS sdci, ROUND(o.oni, 2) AS oni "
    "FROM island_readings ir "
    "JOIN islands i ON ir.island_id = i.id "
    "JOIN ocean_readings o ON ir.date_key = o.date_key "
    "WHERE ir.date_key = '2015-10-01' "
    "ORDER BY ir.sdci ASC",
)

conn.close()