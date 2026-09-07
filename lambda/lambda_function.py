import boto3
import urllib.parse

glue = boto3.client("glue")

WORKFLOW_NAME = "sales-cfn-pipeline-workflow"
OUTPUT_BUCKET = "priya-cfn-glue-output-2026"


def lambda_handler(event, context):
    record = event["Records"][0]

    input_bucket = record["s3"]["bucket"]["name"]

    input_key = urllib.parse.unquote_plus(
        record["s3"]["object"]["key"]
    )

    response = glue.start_workflow_run(
        Name=WORKFLOW_NAME,
        RunProperties={
            "INPUT_BUCKET": input_bucket,
            "INPUT_KEY": input_key,
            "OUTPUT_BUCKET": OUTPUT_BUCKET
        }
    )

    workflow_run_id = response["RunId"]

    print(f"Started workflow: {WORKFLOW_NAME}")
    print(f"Workflow Run ID: {workflow_run_id}")
    print(f"Input bucket: {input_bucket}")
    print(f"Input key: {input_key}")

    return {
        "statusCode": 200,
        "workflowRunId": workflow_run_id,
        "inputKey": input_key
    }