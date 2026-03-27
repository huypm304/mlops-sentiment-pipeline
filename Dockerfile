# Kéo bản CUDA từ mirror nội bộ Bosch
FROM bcr2.inside.bosch.cloud/osd/osd7
# Thiết lập môi trường không tương tác để tránh bị dừng khi cài đặt
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt Python và các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Trước khi RUN pip, hãy set biến môi trường Proxy
ENV http_proxy=http://rb-proxy-apac.bosch.com:8080
ENV https_proxy=http://rb-proxy-apac.bosch.com:8080

# Sửa dòng RUN pip3 của Huy thành thế này:
RUN pip3 install --no-cache-dir \
    --proxy http://rb-proxy-apac.bosch.com:8080 \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

COPY . .

CMD ["python3", "inference_test.py"]