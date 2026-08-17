## DPS HTTP 调用手册

### Base URL

把下面示例里的 `127.0.0.1:8001` 替换为你的实际地址与端口：

`http://127.0.0.1:8001`

### 接口一览

- `GET /health`：查看服务与模型是否就绪
- `POST /analyze`：上传 PDF，返回版面分析框
- `POST /ocr`：上传图片/PDF，返回 OCR 文本与框

### 1) GET /health

#### 请求

`GET http://127.0.0.1:8001/health`

#### 响应（关键字段）

- `status`：固定 `ok`
- `layout_status.status` / `ocr_status.status`：`loading` / `ready` / `error` / `disabled` / `lazy`
- `layout_model_loaded` / `ocr_model_loaded`：是否已实例化

调用方建议：启动后轮询 `/health`，直到需要的模型 `status=ready` 再发任务。

### 2) POST /analyze（PDF 版面分析）

#### 请求

- Method：`POST`
- URL：`http://127.0.0.1:8001/analyze`
- Query 参数（可选）：
  - `with_ocr`：`true/false`，为每个版面框附加 OCR 聚合结果（默认 `false`）
  - `ocr_min_conf`：浮点数，过滤 OCR 低置信度文本（默认 `0.0`）
  - `ocr_return_regions`：`true/false`，是否在每页额外返回 `ocr_text_regions` 明细（默认 `false`）
- Content-Type：`multipart/form-data`
- 表单字段：
  - `file`：必填，PDF 文件

curl 示例：

```bash
curl.exe -X POST -F "file=@C:\path\to\paper.pdf" http://127.0.0.1:8001/analyze
```

带 OCR 的 curl 示例：

```bash
curl.exe -X POST -F "file=@C:\path\to\paper.pdf" "http://127.0.0.1:8001/analyze?with_ocr=true&ocr_min_conf=0.5"
```

Python（requests）示例：

```python
import requests

url = "http://127.0.0.1:8001/analyze"
with open(r"C:\path\to\paper.pdf", "rb") as f:
    r = requests.post(url, files={"file": ("paper.pdf", f, "application/pdf")}, timeout=600)
    print(r.status_code)
    print(r.text[:2000])
```

#### 响应（关键字段）

- `status`：`success`
- `req_id`：请求 ID（用于在服务端日志里定位问题）
- `elapsed_sec`：版面模型推理耗时（秒）
- `pages[]`：
  - `page_index`
  - `width` / `height`
  - `boxes[]`：
    - `label`
    - `score`
    - `coordinate`：`[x0, y0, x1, y1]`
    - `ocr_text`：当 `with_ocr=true` 时返回，表示该框内聚合后的 OCR 文本（按位置从上到下拼接）
    - `ocr_avg_confidence`：当 `with_ocr=true` 时返回，该框内文本的平均置信度
  - `ocr_text_regions`：仅当 `ocr_return_regions=true` 时返回，当前页 OCR 明细数组（可能较大）

### 3) POST /ocr（图片/PDF OCR）

#### 请求

- Method：`POST`
- URL：`http://127.0.0.1:8001/ocr`
- Content-Type：`multipart/form-data`
- 表单字段：
  - `file`：必填，支持 `.jpg/.jpeg/.png/.bmp/.pdf`

curl 示例：

```bash
curl.exe -X POST -F "file=@C:\path\to\img.png" http://127.0.0.1:8001/ocr
```

Python（requests）示例：

```python
import requests

url = "http://127.0.0.1:8001/ocr"
with open(r"C:\path\to\img.png", "rb") as f:
    r = requests.post(url, files={"file": ("img.png", f, "image/png")}, timeout=600)
    print(r.status_code)
    data = r.json()
    print(data["results"][0]["total_texts"])
```

#### 响应（关键字段）

- `status`：`success`
- `req_id`
- `elapsed_sec`：OCR 推理耗时（秒）
- `results[]`：
  - `page_index`
  - `total_texts`
  - `avg_confidence`
  - `text_regions[]`：
    - `text`
    - `confidence`
    - `bbox`：`[x0, y0, x1, y1]`（可能为空）
    - `poly`：`[[x,y], ...]`（可能为空）

### 4) 错误码（调用侧只需要关心这些）

- `400`：入参不合法（例如 /analyze 不是 PDF、/ocr 后缀不支持、空文件）
- `503`：模型未就绪/未加载（建议先查 `/health` 或等待后重试）
- `500`：服务端推理异常（请把 `req_id` 对应的服务端日志抓出来定位）
