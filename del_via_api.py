import requests
import json
import re


cookies = {
}

headers = {
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
}

# response = requests.get(
#     'https://www.facebook.com/adpreferences/advertisers', headers=headers, cookies=cookies)
# data = response.content
# # soup = BeautifulSoup(response.content, 'html.parser')
# # a = soup.find('script', text=re.compile("tc_seen_advertisers"))
# # print(str(a))

# # print(data.decode())
# regex = r"tc_seen_advertisers(.*)tc_hidden_advertiser"

# parsed = re.search(regex, response.content.decode(), re.S | re.M).group(1)
# parsed = parsed[slice(2, -2)]


# data_json = json.loads(parsed)
# print(json.dumps(data_json))

data2 = {
    'fb_dtsg': 'AQFMbeK3xKv9:AQEMQbFeAHaL',
    'variables': '{"input":{"client_mutation_id":"1","actor_id":"100001332636896","is_undo":false,"page_id":"114912860261686"}}',
    'doc_id': '3717265144980552',
}

response = requests.post('https://www.facebook.com/api/graphql/',
                         headers=headers, cookies=cookies, data=data2)
print(response.status_code)
print(response.text)
