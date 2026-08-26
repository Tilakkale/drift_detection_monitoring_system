import pandas as pd

df = pd.read_csv("your_dataset.csv")

print("Rows:", df.shape[0])
print("Columns:", df.shape[1])
print(df.columns.tolist())