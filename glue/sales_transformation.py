import boto3
import pandas as pd
from io import BytesIO
import sys
from awsglue.utils import getResolvedOptions


args = getResolvedOptions(
    sys.argv,
    [
        "WORKFLOW_NAME",
        "WORKFLOW_RUN_ID"
    ]
)

WORKFLOW_NAME = args["WORKFLOW_NAME"]
WORKFLOW_RUN_ID = args["WORKFLOW_RUN_ID"]

glue = boto3.client("glue")

workflow_properties = glue.get_workflow_run_properties(
    Name=WORKFLOW_NAME,
    RunId=WORKFLOW_RUN_ID
)["RunProperties"]

INPUT_BUCKET = workflow_properties["INPUT_BUCKET"]
INPUT_KEY = workflow_properties["INPUT_KEY"]
OUTPUT_BUCKET = workflow_properties["OUTPUT_BUCKET"]

print(f"Input bucket: {INPUT_BUCKET}")
print(f"Input file: {INPUT_KEY}")
print(f"Output bucket: {OUTPUT_BUCKET}")


s3 = boto3.client("s3")

print(f"Reading: s3://{INPUT_BUCKET}/{INPUT_KEY}")

obj = s3.get_object(
    Bucket=INPUT_BUCKET,
    Key=INPUT_KEY
)

df = pd.read_csv(
    BytesIO(obj["Body"].read())
)

print(f"Total input records: {len(df)}")


# Clean customer names
df["customer_name"] = (
    df["customer_name"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Standardize status
df["status"] = (
    df["status"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Standardize city
df["city"] = (
    df["city"]
    .astype(str)
    .str.strip()
    .str.title()
)

# Standardize date
df["order_date"] = pd.to_datetime(
    df["order_date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")


# Calculate total amount
df["total_amount"] = (
    df["quantity"] * df["unit_price"]
)


# Assign discount rates
df["discount_rate"] = df["status"].map({
    "COMPLETED": 0.10,
    "PENDING": 0.05,
    "SHIPPED": 0.05
}).fillna(0)


# Calculate discount
df["discount_amount"] = (
    df["total_amount"] * df["discount_rate"]
)


# Calculate final amount
df["final_amount"] = (
    df["total_amount"] - df["discount_amount"]
)


# Round numerical values
df["unit_price"] = df["unit_price"].round(2)
df["total_amount"] = df["total_amount"].round(2)
df["discount_rate"] = df["discount_rate"].round(2)
df["discount_amount"] = df["discount_amount"].round(2)
df["final_amount"] = df["final_amount"].round(2)


# Create output filename
input_filename = INPUT_KEY.split("/")[-1]
output_filename = "processed_" + input_filename

OUTPUT_KEY = output_filename


# Convert dataframe to CSV
output_buffer = BytesIO()

df.to_csv(
    output_buffer,
    index=False
)

output_buffer.seek(0)


# Upload transformed file
s3.put_object(
    Bucket=OUTPUT_BUCKET,
    Key=OUTPUT_KEY,
    Body=output_buffer.getvalue()
)


print("Transformation completed successfully.")
print(f"Input records: {len(df)}")
print(f"Output location: s3://{OUTPUT_BUCKET}/{OUTPUT_KEY}")

print("Sample transformed records:")
print(
    df.head(5).to_string(index=False)
)