# -*- coding: utf-8 -*-
"""Replicate 工具：上传文件、下载输出等"""
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
BG_REMOVER_VERSION = "851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc"


def ensure_token():
    if not REPLICATE_API_TOKEN:
        raise ValueError("请设置 REPLICATE_API_TOKEN（.env 或环境变量）")


def download_url(url: str, out_path: str) -> str:
    """从 URL 下载文件到本地"""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    urllib.request.urlretrieve(url, out_path)
    return out_path
