import csv

def load_calorie_data(filepath="data/calories.csv"):
    data = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item = row["FoodItem"].strip().lower()
            cal_value = row["Cals_per100grams"].replace(" cal", "").strip()
            try:
                data[item] = int(cal_value)
            except ValueError:
                data[item] = None
    return data

def calorie_lookup(ingredients):
    calorie_data = load_calorie_data()
    total = 0
    details = {}

    for item in ingredients:
        key = item.strip().lower()
        cals = calorie_data.get(key)
        if cals is not None:
            details[item] = cals
            total += cals
        else:
            details[item] = "N/A"
    return total, details
