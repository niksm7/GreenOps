# tools/google_docs_tool.py

from googleapiclient.discovery import build
from google.oauth2 import service_account

import shutil
import os
import json

from google.cloud import bigquery
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from googleapiclient.http import MediaFileUpload
from greenops_agent.agents.summary_generator_agent.markdown_formater import convert_to_google_docs

from greenops_agent.agents.forecaster_agent.agent import execute_forecast_query


SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]


def upload_image_to_drive(image_path, drive_service):

    file_metadata = {
        'name': image_path.split('/')[-1],
        'mimeType': 'image/png'
    }
    media = MediaFileUpload(image_path, mimetype='image/png')
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    # Make it publicly viewable
    drive_service.permissions().create(
        fileId=uploaded_file['id'],
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
    
    file_id = uploaded_file['id']
    file_url = f"https://drive.google.com/uc?id={file_id}"
    print('File Id: ', str(file_id), "File uri: ", str(file_url))
    return file_url

def insert_image_from_drive(doc_id, image_url, index, docs):
    image_request = {
        'insertInlineImage': {
            'location': {'index': index},
            'uri': image_url,
            'objectSize': {
                'height': {'magnitude': 250, 'unit': 'PT'},
                'width': {'magnitude': 450, 'unit': 'PT'}
            }
        }
    }
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": [image_request]}).execute()


def create_google_doc(title: str, body_content: str) -> dict:

    print("Building Charts...")

    chart_paths = build_charts()

    print("Charts built sucessfully! ")
    
    creds = service_account.Credentials.from_service_account_info(json.loads(os.environ["SERVICE_ACCOUNT_KEY"]), scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build("docs", "v1", credentials=creds)

    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    requests = convert_to_google_docs(body_content)

    # Insert text with placeholders for charts
    docs_service.documents().batchUpdate(documentId=doc_id, body=requests).execute()

    # 3. Make it publicly viewable
    drive_service.permissions().create(
        fileId=doc_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        },
        fields='id'
    ).execute()

    google_docs_url = f"https://docs.google.com/document/d/{doc_id}/edit"

    print("Document URL: ", google_docs_url)

    # Locate positions to insert images (based on keywords like `[[chart1]]`, etc.)
    chart_inserts = {
        "[[chart_carbon_timeseries]]": chart_paths['carbon_timeseries'],
        "[[chart_region_utilization]]": chart_paths['region_utilization'],
        "[[chart_cpu_vs_carbon]]": chart_paths['cpu_vs_carbon'],
        "[[chart_underutilization]]": chart_paths['underutilization']
    }

    doc_content = docs_service.documents().get(documentId=doc_id).execute()
    full_text = doc_content.get("body").get("content")

    for key, img_path in chart_inserts.items():
        # REFRESH document content after every change
        doc_content = docs_service.documents().get(documentId=doc_id).execute()
        full_text = doc_content.get("body").get("content")

        for element in full_text:
            text_run = element.get("paragraph", {}).get("elements", [{}])[0].get("textRun", {})
            content = text_run.get("content", "")
            
            if key in content:
                start_index = element["startIndex"]
                end_index = element["endIndex"]
                
                # Step 1: Delete the placeholder
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={
                        "requests": [
                            {
                                "deleteContentRange": {
                                    "range": {
                                        "startIndex": start_index,
                                        "endIndex": end_index
                                    }
                                }
                            }
                        ]
                    }
                ).execute()

                # Step 2: Upload and insert image
                img_url = upload_image_to_drive(img_path, drive_service)
                insert_image_from_drive(doc_id, img_url, start_index, docs_service)
                break  # break inner loop once key is handled

    shutil.rmtree("charts/")

    return {
        "doc_url": google_docs_url,
        "message": f"Your weekly GreenOps report has been created: {google_docs_url}"
    }


def run_query(sql):
    client = bigquery.Client()
    query_job = client.query(sql)
    df = query_job.result().to_dataframe()
    return df

def get_weekly_data() -> dict:
    df_wk_data = run_query("""
    SELECT instance_id,instance_type, region, ROUND(AVG(cpu_util),3) as average_cpu_utilization, ROUND(AVG(memory_util),3) as average_memory_utilization, ROUND(SUM(total_carbon),3) as total_carbon_emission_kg FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) group by instance_id,instance_type, region
    """)

    return df_wk_data.to_dict("records")

def build_charts() -> dict:
    chart_paths = {}

    if not os.path.exists("charts/"):
        os.mkdir("charts/")

    # Chart 1: Time Series
    df_ts = run_query(f"""
        SELECT date, round(sum(total_carbon),2) as value FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` where date < '{datetime.now().strftime('%Y-%m-%d')}' group by date order by date desc limit 7
    """)
    path1 = "charts/chart1_timeseries.png"
    plt.figure(figsize=(10, 5))
    plt.plot(df_ts['date'], df_ts['value'], marker='o')
    plt.title("Time Series: Carbon Emissions")
    plt.xlabel("Date")
    plt.ylabel("Emission (kg)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path1)
    chart_paths['carbon_timeseries'] = path1
    plt.close()

    # Chart 2: Bar Chart
    df_bar = run_query("""
        SELECT region, round(avg(cpu_util),2) as cpu_util, round(avg(memory_util),2) as memory_util FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) group by region
    """)
    path2 = "charts/chart2_bar.png"
    x = df_bar['region']
    cpu = df_bar['cpu_util']
    mem = df_bar['memory_util']
    x_axis = range(len(x))
    plt.figure(figsize=(10, 5))
    plt.bar(x_axis, cpu, width=0.4, label='CPU', align='center')
    plt.bar([i + 0.4 for i in x_axis], mem, width=0.4, label='Memory', align='center')
    plt.xticks([i + 0.2 for i in x_axis], x, rotation=45)
    plt.title("Average CPU and Memory by Region")
    plt.xlabel("Region")
    plt.ylabel("Average Utilization")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path2)
    chart_paths['region_utilization'] = path2
    plt.close()

    # Chart 3: Scatter Plot
    df_scatter = run_query("""
        SELECT instance_id, round(avg(cpu_util),2) as cpu_util, round(sum(total_carbon),2) as total_carbon FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) group by instance_id
    """)
    path3 = "charts/chart3_scatter.png"
    plt.figure(figsize=(8, 6))
    plt.scatter(df_scatter['cpu_util'], df_scatter['total_carbon'], alpha=0.7, c='green')
    plt.title("CPU vs Carbon Emission for Instance IDs")
    plt.xlabel("Average CPU Utilization")
    plt.ylabel("Total Carbon Emission (kg)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path3)
    chart_paths['cpu_vs_carbon'] = path3
    plt.close()

    # Chart 4: Underutilization Rate (Area)
    df_area = run_query("""
        SELECT DATE(date) AS day, COUNTIF(cpu_util < 30 OR memory_util < 40) * 100.0 / COUNT(*) AS underutilization_rate FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) GROUP BY day ORDER BY day
    """)
    path4 = "charts/chart4_underutilization.png"
    plt.figure(figsize=(10, 5))
    plt.fill_between(df_area['day'], df_area['underutilization_rate'], color='skyblue', alpha=0.6)
    plt.title("Under-utilization Rate Over Time")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xlabel("Date")
    plt.ylabel("Underutilized Servers (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path4)
    chart_paths['underutilization'] = path4

    plt.close()

    return chart_paths


def get_forecast_information():
    """
    Input: None
    Use: This tool gives critical information about forecasting of the current week
    Output:
    - Total carbon emissions for the week
    - date with highest projected carbon emission
    - Top carbon emitting emissions
    """

    query = """
    SELECT Instance_ID, forecast_timestamp, forecast_value
    FROM ML.FORECAST(
    MODEL `greenops-460813.gcp_server_details.server_carbon_forecast_model`,
    STRUCT(7 AS horizon, 0.8 AS confidence_level)
    )
    """

    rows = execute_forecast_query(query)["rows"]

    date_to_emissions = {}
    instance_to_emissions = {}
    total_emission = 0

    for row in rows:
        instance_id = row["Instance_ID"]
        instance_emission = 0
        for date in row:
            if date != "Instance_ID":
                if not date_to_emissions.get(date):
                    date_to_emissions[date] = 0
                date_to_emissions[date] += row[date]
                instance_emission += row[date]
        instance_to_emissions[instance_id] = instance_emission
        total_emission += instance_emission
    
    date_with_highest = sorted(date_to_emissions.items(), key=lambda item: item[1], reverse=True)
    instance_with_highest = sorted(instance_to_emissions.items(), key=lambda item: item[1], reverse=True)

    return {
        "Total Carbon Emissions for the week" : round(total_emission, 3),
        "Date with Highest Emission" : {date_with_highest[0][0] : round(date_with_highest[0][1],3)},
        "Top 2 Carbon Emitting instances" : [
            {instance_with_highest[0][0] : round(instance_with_highest[0][1],3)},
            {instance_with_highest[1][0] : round(instance_with_highest[1][1],3)}
        ]
    }
