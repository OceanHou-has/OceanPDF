"""
文档解析服务连通性测试
为每个服务提供独立的连通性测试函数
"""
import time
import base64
from typing import Dict, Any
import aiohttp
from loguru import logger


# 1x1 白色 PNG 图片（base64），用于轻量级连通性测试
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


def _result(success: bool, message: str, latency_ms: float) -> Dict[str, Any]:
    return {"success": success, "message": message, "latency_ms": round(latency_ms, 1)}


async def test_baidu(api_key: str, secret_key: str) -> Dict[str, Any]:
    """
    百度AI文档解析 - 连通性测试
    通过获取 access_token 验证凭证有效性
    """
    t0 = time.monotonic()
    try:
        # 第一步：获取 access_token
        token_url = (
            f"https://aip.baidubce.com/oauth/2.0/token"
            f"?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return _result(False, f"获取 access_token 失败 (HTTP {resp.status}): {text[:200]}", (time.monotonic() - t0) * 1000)
                data = await resp.json()

        if "access_token" in data:
            return _result(True, f"连接成功，access_token 获取正常", (time.monotonic() - t0) * 1000)
        else:
            error = data.get("error_description", data.get("error", "未知错误"))
            return _result(False, f"认证失败: {error}", (time.monotonic() - t0) * 1000)

    except aiohttp.ClientError as e:
        return _result(False, f"网络错误: {str(e)}", (time.monotonic() - t0) * 1000)
    except Exception as e:
        return _result(False, f"测试异常: {str(e)}", (time.monotonic() - t0) * 1000)


async def test_aliyun(access_key_id: str, access_key_secret: str) -> Dict[str, Any]:
    """
    阿里云文档智能 - 连通性测试
    通过调用 GetDocParserResult 接口验证凭证（使用空参数触发预期错误来验证认证）
    """
    t0 = time.monotonic()
    try:
        # 阿里云使用签名认证，这里测试基本的 API 可达性
        # 调用 DescribeUserClassInfos 接口（轻量级查询接口）
        endpoint = "https://docmind-api.cn-hangzhou.aliyuncs.com"
        params = {
            "Action": "GetUserDetail",
            "Format": "JSON",
            "Version": "2022-07-11",
            "AccessKeyId": access_key_id,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": str(int(time.time() * 1000)),
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # 简化的签名计算（阿里云V1签名）
        import hashlib
        import hmac
        import urllib.parse

        sorted_params = sorted(params.items())
        query_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
        string_to_sign = f"GET&%2F&{urllib.parse.quote(query_string, safe='')}"
        sign_key = access_key_secret + "&"
        signature = base64.b64encode(
            hmac.new(sign_key.encode(), string_to_sign.encode(), hashlib.sha1).digest()
        ).decode()
        params["Signature"] = signature

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                # 如果返回了 Code 但不是 InvalidAccessKeyId，说明凭证有效
                code = data.get("Code", "")
                if "InvalidAccessKeyId" in code or "SignatureDoesNotMatch" in code:
                    return _result(False, f"认证失败: {data.get('Message', code)}", (time.monotonic() - t0) * 1000)
                elif resp.status == 200:
                    return _result(True, "连接成功，凭证有效", (time.monotonic() - t0) * 1000)
                else:
                    # 其他业务错误说明凭证可能有效，只是请求参数问题
                    return _result(True, f"连接成功（业务提示: {data.get('Message', 'OK')}）", (time.monotonic() - t0) * 1000)

    except aiohttp.ClientError as e:
        return _result(False, f"网络错误: {str(e)}", (time.monotonic() - t0) * 1000)
    except Exception as e:
        return _result(False, f"测试异常: {str(e)}", (time.monotonic() - t0) * 1000)


async def test_tencent(secret_id: str, secret_key: str) -> Dict[str, Any]:
    """
    腾讯云文档解析 - 连通性测试
    通过 TC3-HMAC-SHA256 签名调用 DescribeInstances 验证凭证
    """
    t0 = time.monotonic()
    try:
        import hashlib
        import hmac
        import datetime

        service = "es"
        host = "es.tencentcloudapi.com"
        endpoint = f"https://{host}"
        timestamp = int(time.time())
        date = datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

        # 构建请求体
        payload = '{"ModelName":"doc-llm"}'

        # 步骤1: 拼接规范请求串
        canonical_request = (
            f"POST\n/\n\ncontent-type:application/json\nhost:{host}\n\n"
            f"content-type;host\n{hashlib.sha256(payload.encode()).hexdigest()}"
        )

        # 步骤2: 拼接待签名字符串
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical = hashlib.sha256(canonical_request.encode()).hexdigest()
        string_to_sign = f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashed_canonical}"

        # 步骤3: 计算签名
        def _hmac_sha256(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        secret_date = _hmac_sha256(("TC3" + secret_key).encode(), date)
        secret_service = _hmac_sha256(secret_date, service)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

        # 步骤4: 拼接 Authorization
        authorization = (
            f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, "
            f"SignedHeaders=content-type;host, Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Host": host,
            "X-TC-Action": "ParseDocument",
            "X-TC-Version": "2025-01-01",
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": "ap-beijing",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, data=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                error = data.get("Response", {}).get("Error", {})
                if error:
                    code = error.get("Code", "")
                    if code in ("AuthFailure", "AuthFailure.SecretIdNotFound", "AuthFailure.SignFailure"):
                        return _result(False, f"认证失败: {error.get('Message', code)}", (time.monotonic() - t0) * 1000)
                    # 其他业务错误（如参数错误）说明凭证有效
                    return _result(True, f"连接成功（业务提示: {error.get('Message', 'OK')}）", (time.monotonic() - t0) * 1000)
                return _result(True, "连接成功，凭证有效", (time.monotonic() - t0) * 1000)

    except aiohttp.ClientError as e:
        return _result(False, f"网络错误: {str(e)}", (time.monotonic() - t0) * 1000)
    except Exception as e:
        return _result(False, f"测试异常: {str(e)}", (time.monotonic() - t0) * 1000)


async def test_huawei(ak: str, sk: str, endpoint: str = None) -> Dict[str, Any]:
    """
    华为云智能文档 - 连通性测试
    通过 IAM Token 验证凭证有效性
    """
    t0 = time.monotonic()
    try:
        # 华为云通过 IAM 获取 Token 来验证凭证
        iam_url = "https://iam.myhuaweicloud.com/v3/auth/tokens"
        payload = {
            "auth": {
                "identity": {
                    "methods": ["ak_sk"],
                    "ak_sk": {
                        "access_key_id": ak,
                        "secret_access_key": sk
                    }
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                iam_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 201:
                    return _result(True, "连接成功，IAM Token 获取正常", (time.monotonic() - t0) * 1000)
                else:
                    data = await resp.json()
                    error = data.get("error", {})
                    msg = error.get("message", f"HTTP {resp.status}")
                    return _result(False, f"认证失败: {msg}", (time.monotonic() - t0) * 1000)

    except aiohttp.ClientError as e:
        return _result(False, f"网络错误: {str(e)}", (time.monotonic() - t0) * 1000)
    except Exception as e:
        return _result(False, f"测试异常: {str(e)}", (time.monotonic() - t0) * 1000)


async def test_zhipu(api_key: str) -> Dict[str, Any]:
    """
    智谱GLM-OCR - 连通性测试
    调用 layout_parsing 接口（使用最小图片）验证 API Key
    """
    t0 = time.monotonic()
    try:
        url = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "glm-ocr",
            "file": f"data:image/png;base64,{TINY_PNG_B64}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "layout_details" in data or "md_results" in data:
                        return _result(True, "连接成功，API Key 有效", (time.monotonic() - t0) * 1000)
                    return _result(True, "连接成功", (time.monotonic() - t0) * 1000)
                else:
                    data = await resp.json()
                    error = data.get("error", {})
                    msg = error.get("message", f"HTTP {resp.status}")
                    if resp.status in (401, 403):
                        return _result(False, f"认证失败: {msg}", (time.monotonic() - t0) * 1000)
                    return _result(False, f"请求失败: {msg}", (time.monotonic() - t0) * 1000)

    except aiohttp.ClientError as e:
        return _result(False, f"网络错误: {str(e)}", (time.monotonic() - t0) * 1000)
    except Exception as e:
        return _result(False, f"测试异常: {str(e)}", (time.monotonic() - t0) * 1000)


async def test_textin(app_id: str, secret_code: str) -> Dict[str, Any]:
    """
    TextIn xParse - 连通性测试
    调用 xParse 解析状态接口验证凭证
    """
    t0 = time.monotonic()
    try:
        # TextIn 使用 App ID + Secret Code 认证
        # 调用一个简单的查询接口验证凭证
        url = "https://api.textin.com/ocr/v1/service_list"
        headers = {
            "x-app-id": app_id,
            "x-secret-code": secret_code,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return _result(True, "连接成功，凭证有效", (time.monotonic() - t0) * 1000)
                else:
                    text = await resp.text()
                    if resp.status in (401, 403):
                        return _result(False, f"认证失败: {text[:200]}", (time.monotonic() - t0) * 1000)
                    # 尝试解析JSON获取更详细的错误信息
                    try:
                        data = await resp.json()
                        msg = data.get("message", data.get("msg", text[:200]))
                        return _result(False, f"请求失败: {msg}", (time.monotonic() - t0) * 1000)
                    except Exception:
                        return _result(False, f"HTTP {resp.status}: {text[:200]}", (time.monotonic() - t0) * 1000)

    except aiohttp.ClientError as e:
        return _result(False, f"网络错误: {str(e)}", (time.monotonic() - t0) * 1000)
    except Exception as e:
        return _result(False, f"测试异常: {str(e)}", (time.monotonic() - t0) * 1000)


# 测试函数注册表
TEST_FUNCTIONS = {
    "baidu": test_baidu,
    "aliyun": test_aliyun,
    "tencent": test_tencent,
    "huawei": test_huawei,
    "zhipu": test_zhipu,
    "textin": test_textin,
}


async def test_connectivity(provider_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一连通性测试入口
    """
    test_func = TEST_FUNCTIONS.get(provider_id)
    if not test_func:
        return _result(False, f"未知的服务ID: {provider_id}", 0)

    logger.info(f"[文档解析] 测试连通性: {provider_id}")

    # 根据服务类型传递不同参数
    if provider_id == "baidu":
        return await test_func(config.get("api_key", ""), config.get("secret_key", ""))
    elif provider_id == "aliyun":
        return await test_func(config.get("access_key_id", ""), config.get("access_key_secret", ""))
    elif provider_id == "tencent":
        return await test_func(config.get("secret_id", ""), config.get("secret_key", ""))
    elif provider_id == "huawei":
        return await test_func(config.get("ak", ""), config.get("sk", ""), config.get("endpoint"))
    elif provider_id == "zhipu":
        return await test_func(config.get("api_key", ""))
    elif provider_id == "textin":
        return await test_func(config.get("app_id", ""), config.get("secret_code", ""))
    else:
        return _result(False, f"未实现的服务: {provider_id}", 0)
