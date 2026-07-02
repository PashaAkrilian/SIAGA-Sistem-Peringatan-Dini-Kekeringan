import csv
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
CSV_PATH = HERE / "master_dataset_godzilla_elnino_2000_2025.csv"
DB_PATH = HERE / "data" / "siaga.db"

ISLANDS = {
    "Indo": "Nasional",
    "Sumatera": "Sumatera",
    "Jawa": "Jawa",
    "Kalimantan": "Kalimantan",
    "Sulawesi": "Sulawesi",
    "NusaTenggara": "Nusa Tenggara",
    "Maluku": "Maluku",
    "Papua": "Papua",
}

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Databasa lama dihapus")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # executescript() bisa menjalankan beberapa perintah SQL
    cur.executescript("""
        CREATE TABLE islands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL
        );

        CREATE TABLE ocean_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_key TEXT NOT NULL,
            sst_nino34  REAL,
            sst_anomaly REAL,
            oni         REAL
        );

        CREATE TABLE island_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            island_id INTEGER NOT NULL,
            date_key TEXT NOT NULL,
            ndvi REAL,
            lst REAL,
            precip REAL,
            sdci REAL,
            FOREIGN KEY (island_id) REFERENCES islands(id)
        );

        CREATE INDEX idx_ir_island ON island_readings (island_id);
        CREATE INDEX idx_ir_date ON island_readings (date_key);
    """)

    # Tanda '?' adalah placeholder — cara AMAN memasukkan nilai
    code_to_id = {}
    for code, name in ISLANDS.items():
        cur.execute(
            "INSERT INTO islands (code, name) VALUES (?, ?)",
            (code, name),
        )
        # lastrowid = id yang baru saja dibuat, kita simpan untuk dipakai nanti
        code_to_id[code] = cur.lastrowid
    print(f"islands: {len(code_to_id)} baris")

    n_ocean = 0
    n_island = 0
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)  # baca CSV sebagai dict per baris
        for row in reader:
            date = row["date_key"]

            # -- ocean_readings: satu baris per bulan --
            cur.execute(
                "INSERT INTO ocean_readings (date_key, sst_nino34, sst_anomaly, oni) "
                "VALUES (?, ?, ?, ?)",
                (date, row["sst_nino34"], row["sst_anomaly"], row["ONI"]),
            )
            n_ocean += 1

            # -- island_readings: ubah data 'lebar' jadi 'panjang' --
            for code in ISLANDS:
                cur.execute(
                    "INSERT INTO island_readings "
                    "(island_id, date_key, ndvi, lst, precip, sdci) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        code_to_id[code],
                        date,
                        row[f"ndvi_{code}"],
                        row[f"lst_{code}"],
                        row[f"precip_{code}"],
                        row[f"SDCI_{code}"],
                    ),
                )
                n_island += 1

    print(f"ocean_readings: {n_ocean} baris")
    print(f"island_readings: {n_island} baris (wide->long transform)")

    # commit() menyimpan semua perubahan ke file. WAJIB, kalau tidak data hilang!
    conn.commit()
    conn.close()

    print(f"\nDatabase selesai dibuat: {DB_PATH}")
    print("Sekarang jalankan: python query.py  (untuk mencoba query)")

if __name__ == "__main__":
    main()
