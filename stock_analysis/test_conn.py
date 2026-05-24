import os
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ['NO_PROXY'] = '*'

print("Test 1: HTTP (not HTTPS)...")
import requests
try:
    r = requests.get(
        'http://82.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f12&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f12,f14,f2',
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(r.text[:300])
except Exception as e:
    print(f"Failed: {e}")

print("\nTest 2: akshare directly...")
import akshare as ak
try:
    df = ak.stock_zh_a_spot_em()
    print(f"Success! Got {len(df)} rows")
    print(df.head())
except Exception as e:
    print(f"akshare failed: {e}")

print("\nTest 3: http with different host...")
try:
    r = requests.get('http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f12&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f12,f14,f2', timeout=15)
    print(f"Status: {r.status_code}")
    print(r.text[:300])
except Exception as e:
    print(f"Failed: {e}")