import pandas as pd

df = pd.read_excel("Masterdata/master_database.xlsx")

print(df.columns.tolist())
print()
print(df.head())