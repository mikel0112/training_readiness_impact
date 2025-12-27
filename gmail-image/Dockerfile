FROM ubuntu:20.04
RUN apt update && apt install -y python3-pip
RUN pip3 install -r requirements.txt
COPY weekly_summary_email.py /
CMD ["python3", "weekly_summary_email.py"]
