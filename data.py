def calorie_lookup(ingredients):
    import csv

    data = {}
    with open("data/calories.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row["FoodItem"].strip().lower()
            kcal = row["Cals_per100grams"].replace(" cal", "").strip()
            kj = row["KJ_per100grams"].replace(" kJ", "").strip()
            try:
                data[name] = {
                    "kcal": int(kcal),
                    "kj": int(kj)
                }
            except ValueError:
                data[name] = {
                    "kcal": 0,
                    "kj": 0
                }

    total_kcal = 0
    total_kj = 0
    breakdown = {}

    for item in ingredients:
        key = item.strip().lower()
        if key in data:
            kcal = data[key]["kcal"]
            kj = data[key]["kj"]
            breakdown[item] = {"kcal": kcal, "kj": kj}
            total_kcal += kcal
            total_kj += kj
        else:
            breakdown[item] = {"kcal": "N/A", "kj": "N/A"}

    total = {"kcal": total_kcal, "kj": total_kj}
    return total, breakdown
