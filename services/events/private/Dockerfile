FROM python:3.12-slim

WORKDIR /app
RUN mkdir common
COPY --from=common . ./common
COPY . .

RUN apt update && apt install -y git libopenblas-dev ninja-build build-essential pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/*

RUN CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install llama_cpp_python --verbose

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "server.py"] 