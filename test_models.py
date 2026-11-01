import requests

test_url = "https://image.pollinations.ai/prompt/cinematic%20shot?nologo=true"
r = requests.get(test_url, headers={"User-Agent": "Mozilla/5.0"})
print("Default:", r.status_code)

# Try pollinations with other models
for m in ["flux", "turbo", "unity", "midjourney"]:
    url = f"https://image.pollinations.ai/prompt/cinematic%20shot?model={m}&nologo=true"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"Model {m}:", res.status_code)
