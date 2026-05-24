import os
for _key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_key, None)
os.environ['NO_PROXY'] = '*'

import akshare as ak
import requests

# 设置 akshare 使用的 requests session 的 headers
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

print("Testing akshare stock_zh_a_spot_em()...")
print("(This may take a while due to pagination)")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"Success! Got {len(df)} stocks")
    print(df.head(3))
except Exception as e:
    print(f"Failed: {e}")
    print("\nTrying alternative: stock_info_a_code_name...")
    try:
        df2 = ak.stock_info_a_code_name()
        print(f"Got {len(df2)} stocks from stock_info_a_code_name")
        print(df2.head(3))
    except Exception as e2:
        print(f"Also failed: {e2}")