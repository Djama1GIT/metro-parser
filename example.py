import pandas as pd

from src import MetroParser

parser = MetroParser()
cities = ["Москва", "Санкт-Петербург"]
for city in cities:
    df = pd.DataFrame(data=parser.parse_chocolate_category(city=city))
    df.to_csv(f"{city}.csv", index=False)
    print(df)
