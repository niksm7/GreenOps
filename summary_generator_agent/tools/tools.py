# tools/google_docs_tool.py

from googleapiclient.discovery import build
from google.oauth2 import service_account

import shutil
import os

from google.cloud import bigquery
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "/Users/nikhilmankani/Documents/GreenOps/greenops-service-account-file.json"
client = bigquery.Client()
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)


def upload_image_to_drive(image_path):
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

    
    docs = build("docs", "v1", credentials=creds)

    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    # Insert text with placeholders for charts
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": [
        {"insertText": {"location": {"index": 1}, "text": body_content}}
    ]}).execute()

    # 3. Make it publicly viewable
    drive_service.permissions().create(
        fileId=doc_id,
        body={
            'type': 'anyone',
            'role': 'reader'
        },
        fields='id'
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print("Document URL: ", doc_url)

    # Locate positions to insert images (based on keywords like `[[chart1]]`, etc.)
    chart_inserts = {
        "[[chart_carbon_timeseries]]": chart_paths['carbon_timeseries'],
        "[[chart_region_utilization]]": chart_paths['region_utilization'],
        "[[chart_cpu_vs_carbon]]": chart_paths['cpu_vs_carbon'],
        "[[chart_underutilization]]": chart_paths['underutilization']
    }

    doc_content = docs.documents().get(documentId=doc_id).execute()
    full_text = doc_content.get("body").get("content")

    for key, img_path in chart_inserts.items():
        # REFRESH document content after every change
        doc_content = docs.documents().get(documentId=doc_id).execute()
        full_text = doc_content.get("body").get("content")

        for element in full_text:
            text_run = element.get("paragraph", {}).get("elements", [{}])[0].get("textRun", {})
            content = text_run.get("content", "")
            
            if key in content:
                start_index = element["startIndex"]
                end_index = element["endIndex"]
                
                # Step 1: Delete the placeholder
                docs.documents().batchUpdate(
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
                img_url = upload_image_to_drive(img_path)
                insert_image_from_drive(doc_id, img_url, start_index, docs)
                break  # break inner loop once key is handled

    shutil.rmtree("charts/")

    return {
        "doc_url": doc_url,
        "message": f"Your weekly GreenOps report has been created: {doc_url}"
    }


def run_query(sql):
    query_job = client.query(sql)
    df = query_job.result().to_dataframe()
    return df


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