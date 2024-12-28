alertmanager webhooks:
```
  receivers:
  - name: 'webhook'
    webhook_configs:
    - url: 'http://webhook-server/alert'
```
run docker container:
```
sudo /usr/local/bin/nerdctl run -d -p 5000:5000 -e PROMETHEUS_URL=http://ip_address:port -e SMTP_SERVER=smtp_server_uri -e SMTP_PORT=25 -e SMTP_USERNAME=#### -e SMTP_PASSWORD=#### -e SENDER_EMAIL=example@yandex.ru -e RECEIVER_EMAIL=example@yandex.ru do3fh1/prometheus-alert-grapher
```
curl запрос для проверки:
```
curl -X POST   http://localhost:5000/alert   -H 'Content-Type: application/json'   -d '{
    "alerts": [
        {
            "labels": {
                "alertname": "CPUThrottlingHigh"
            },
            "annotations": {
                "description": "CPU usage is above 80%",
                "summary": "High CPU usage detected",
                "query": "sum by (pod) (up{pod=~\".*\"}) < 1",
                "Create graph": "yes"
            },
            "start": "2024-12-27T07:00:00",
            "end": "2024-12-24T09:00:00"
        }
    ]
}'
```
dockerhub:
https://hub.docker.com/repository/docker/do3fh1/prometheus-alert-grapher
