# gunicorn.conf.py

bind = "0.0.0.0:10000"
workers = 2
timeout = 300  # ⏱️ allow up to 5 minutes for processing large PDFs