import os
import pandas as pd

# Define the root directory and the new directory for aligned data
root_dir = "data"
align_dir = "data-align"

# Ensure the new directory exists
os.makedirs(align_dir, exist_ok=True)

# Function to process CSV files


def process_csv_file(file_path, output_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Ensure the DataFrame has 1000 rows
    if len(df) > 1000:
        df = df.head(1000)
    else:
        # Repeat the DataFrame if it has less than 1000 rows
        df = pd.concat([df] * (1000 // len(df) + 1), ignore_index=True)
        df = df.head(1000)

    # Process 'timestamp' column
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    # Process 'success_rate' column
    if "success_rate" in df.columns:
        df["success_rate"] = df["success_rate"] / 100.0

    # Process 'duration' column
    if "duration" in df.columns:
        df["duration"] = df["duration"].apply(lambda x: x if x == 0 else x / 1000000.0)

    # Process 'cpu' column
    if "cpu" in df.columns:
        df["cpu"] = (df["cpu"] - df["cpu"].min()) / (df["cpu"].max() - df["cpu"].min())

    # Retain only the specified columns and remove duplicates
    columns_to_keep = [
        "timestamp",
        "ops",
        "success_rate",
        "duration",
        "cpu",
        "memory",
        "receive",
        "transmit",
    ]
    # Check for the existence of each column before selecting
    existing_columns = [col for col in columns_to_keep if col in df.columns]
    df = df[existing_columns]

    # Save the processed DataFrame to the new path
    df.to_csv(output_path, index=False)


# Walk through the directory structure
for subdir, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".csv"):
            # Construct the full file path
            file_path = os.path.join(subdir, file)

            # Determine the new file path
            relative_path = os.path.relpath(subdir, root_dir)
            new_dir = os.path.join(align_dir, relative_path)
            os.makedirs(new_dir, exist_ok=True)
            output_path = os.path.join(new_dir, file)

            # Process the CSV file
            process_csv_file(file_path, output_path)

print("CSV processing complete. Files saved in", align_dir)
