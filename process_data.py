import os
import pandas as pd

input_folder = "raw_csvs"
output_folder = "processed_csvs"

os.makedirs(output_folder, exist_ok=True)

dt = 100  # 10Hz = 100 ms 

for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        df = pd.read_csv(input_path)

        # add timestamp column
        timestamps = [i * dt for i in range(len(df))]
        df.insert(0, "timestamp", timestamps)

        df.to_csv(output_path, index=False)

        print(f"Processed {filename}: {len(df)} rows")

print("Done!")