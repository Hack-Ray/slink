from urllib.parse import urlparse
from typing import Tuple

def validate_url(url: str) -> Tuple[bool, str]:
    """
    驗證 URL 是否安全
    返回: (是否安全, 錯誤訊息)
    """
    # 檢查是否為 HTTPS
    parsed_url = urlparse(url)
    if parsed_url.scheme != 'https':
        return False, "URL must use HTTPS protocol"

    # 檢查是否為有效的 URL
    if not all([parsed_url.scheme, parsed_url.netloc]):
        return False, "Invalid URL format"

    return True, ""
