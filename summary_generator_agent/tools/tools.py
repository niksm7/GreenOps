# tools/google_docs_tool.py

from googleapiclient.discovery import build
from google.oauth2 import service_account


from google.cloud import bigquery
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SCOPES = ["https://www.googleapis.com/auth/documents"]
SERVICE_ACCOUNT_FILE = "path/to/your-service-account.json"
client = bigquery.Client()

def create_google_doc(title: str, body_content: str) -> dict:
    """
    Creates a Google Doc with the given title and HTML/markdown body_content.
    Returns: {"doc_url": <webViewLink>}
    """
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    docs = build("docs", "v1", credentials=creds)
    # Create document
    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    # Insert the body_content (as simple text; you could convert markdown→Google Docs requests)
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [
            {"insertText": {"location": {"index": 1}, "text": body_content}}
        ]}
    ).execute()
    return {"doc_url": f"https://docs.google.com/document/d/{doc_id}/edit"}


def run_query(sql):
    query_job = client.query(sql)
    df = query_job.result().to_dataframe()
    return df


def build_charts();
    df_ts = run_query(f"SELECT date, round(sum(total_carbon),2) as value FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` where date < '{datetime.now().strftime('%Y-%m-%d')}' group by date order by date desc limit 7")

    plt.figure(figsize=(10, 5))
    plt.plot(df_ts['date'], df_ts['value'], marker='o')
    plt.title("Time Series: Carbon Emissions")
    plt.xlabel("Date")
    plt.ylabel("Emission (kg)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("chart1_timeseries.png")


    df_bar = run_query(f"SELECT region, round(avg(cpu_util),2) as cpu_util, round(avg(memory_util),2) as memory_util FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) group by region")

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
    plt.savefig("chart2_bar.png")


    df_scatter = run_query(f"SELECT instance_id, round(avg(cpu_util),2) as cpu_util, round(sum(total_carbon),2) as total_carbon FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) group by instance_id")

    plt.figure(figsize=(8, 6))
    plt.scatter(df_scatter['cpu_util'], df_scatter['total_carbon'], alpha=0.7, c='green', label="Instance Id")
    plt.title("CPU vs Carbon Emission for Instance Ids")
    plt.xlabel("Average CPU Utilization")
    plt.ylabel("Total Carbon Emission (kg)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.savefig("chart3_scatter.png")


    df_area = run_query("SELECT DATE(date) AS day, COUNTIF(cpu_util < 30 OR memory_util < 40) * 100.0 / COUNT(*) AS underutilization_rate FROM `greenops-460813.gcp_server_details.server_metrics_timeseries` WHERE DATE(date) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) GROUP BY day ORDER BY day")


    # Plotting the area chart
    plt.figure(figsize=(10, 5))
    plt.fill_between(df_area['day'], df_area['underutilization_rate'], color='skyblue', alpha=0.6)
    plt.title("Under-utilization Rate Over Time")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xlabel("Date")
    plt.ylabel("Underutilized Servers (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()

