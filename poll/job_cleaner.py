from datetime import datetime

tag = f"{datetime.now():%Y%m%d}"

for log in ["dyndns", "elenia"]:
    with open(f"/mnt/{log}.log", "r") as f:
        content = f.read()
    with open(f"/mnt/archive/{log}.{tag}.log", "w") as f:
        f.write(content)
    with open(f"/mnt/{log}.log", "w") as f:
        f.write("")


with open("/media/data_energy.txt", "r") as f:
    data_energy = f.read()

with open("/media/data_energy.txt", "w") as f:
    f.write(data_energy[-29:])


with open("/media/data_energy_prices.txt", "r") as f:
    data_energy = f.read()

with open("/media/data_energy_prices.txt", "w") as f:
    f.write(data_energy[-60:])
