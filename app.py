import os
import io
from flask import Flask, request
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

@app.route('/alert', methods=['POST'])
def handle_alert():
    alert_data = request.json
    app.logger.info(f"Received alert data: {alert_data}")
    
    # Проверяем наличие запроса для промета
    if 'alerts' in alert_data and alert_data['alerts']:
        metric_name = alert_data['alerts'][0].get('annotations', {}).get('query', 'Unknown Metric')
        if metric_name == 'Unknown Metric':
            app.logger.info("Alert does not contain query in annotations. Skipping.")
            return "Alert skipped", 200

        alert_name = alert_data['alerts'][0].get('labels', {}).get('alertname', 'Unknown Alertname')
    else:
        app.logger.info("Invalid alert data. Skipping.")
        return "Alert skipped", 200
    
    app.logger.info(f"Processing metric: {metric_name}, alert: {alert_name}")
    
    # Создаем график
    image_buffer = create_graph(metric_name, alert_name)
    
    # Отправляем email с графиком
    send_email(image_buffer, alert_name)
    
    return "Alert processed", 200

def create_graph(metric_name, alert_name):
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)  # График за последний час
    query = f'{metric_name}'
    params = {
        'query': query,
        'start': start_time.isoformat("T") + "Z",
        'end': end_time.isoformat("T") + "Z",
        'step': '15s',  # Интервал между точками данных
    }
    response = requests.get(f'{PROMETHEUS_URL}/api/v1/query_range', params=params)
    data = response.json()

    plt.figure(figsize=(12, 6))

    if data['status'] == 'success' and data['data']['result']:
        for result in data['data']['result']:
            df = pd.DataFrame(result['values'], columns=['timestamp', 'value'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['value'] = df['value'].astype(float)
            
            # Создаем метку для легенды
            label = result['metric'].get('pod', 'Unknown Pod')
            
            plt.plot(df['timestamp'], df['value'], label=label)
        
        plt.title(f'{alert_name} - Last Hour')
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, f'{alert_name} - No Data Available',
                 horizontalalignment='center', verticalalignment='center')
        plt.axis('off')

    plt.grid(True)
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    return buffer

def send_email(image_buffer, alert_name):
    sender_email = os.environ.get('SENDER_EMAIL')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    msg = MIMEMultipart()
    msg['Subject'] = f'Prometheus Alert: {alert_name}'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    text = MIMEText(f"Prometheus alert '{alert_name}' triggered. See attached graph.")
    msg.attach(text)

    image = MIMEImage(image_buffer.getvalue())
    image.add_header('Content-Disposition', 'attachment', filename=f'{alert_name}_graph.png')
    msg.attach(image)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        app.logger.info("Email sent successfully")
    except Exception as e:
        app.logger.error(f"Failed to send email: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
