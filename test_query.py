import urllib.request, json
url = 'http://127.0.0.1:8000/query'
data = json.dumps({'query': 'what did they say about inflation?'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    for line in response:
        print(line.decode('utf-8'), end='')
