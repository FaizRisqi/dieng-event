import subprocess
from collections import defaultdict

out = subprocess.run(
    ["git", "log", "--reverse", "--date=short", "--pretty=format:%ad|%s"],
    capture_output=True, text=True, encoding="utf-8",
).stdout.strip().splitlines()

per_hari = defaultdict(list)
for baris in out:
    tgl, pesan = baris.split("|", 1)
    per_hari[tgl].append(pesan)

with open("HISTORY.md", "w", encoding="utf-8") as f:
    f.write("# Riwayat Pengerjaan\n\n_Dibuat otomatis dari git log._\n")
    for tgl in sorted(per_hari, reverse=True):
        f.write(f"\n## {tgl}\n\n")
        for pesan in per_hari[tgl]:
            f.write(f"- {pesan}\n")

print("HISTORY.md diperbarui")