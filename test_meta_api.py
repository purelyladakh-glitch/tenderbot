import httpx

token = "EAAqOjiO9IIoBQxS3kVO6SddNNrk0xs0NzXm8rvo6f5sggyDZBwL7hJ9i2UFdBAY1Deptc8kQj5EsgfLKaZC73AGCKe2WpjzkOfFahYuwz5FGthQzExjwZAdfOZA7es9vJbcxAI83qv7QbSDZAVe7mcOqqMWzdD1YetjSNnHNlwfPh4hNqgpjBpE2pYEddHc7pwQZDZD"
phone_id = "999987769870141"

url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "messaging_product": "whatsapp",
    "to": "917051603851",
    "type": "text",
    "text": {"body": "TenderBot test"}
}

response = httpx.post(url, json=payload, headers=headers)
print(response.status_code)
print(response.text)
