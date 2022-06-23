import requests, os, json, time, re
from colorama import Fore, init
init()

os.system('cls')

config = json.load(open('config.json','r'))
webhook = config['webhook']
assetId = config['assetId']
cookie = config['cookie']
currentSellingPrice = ''
userAssetId = ''

userId = str(requests.get('https://www.roblox.com/mobileapi/userinfo', cookies={'.ROBLOSECURITY': cookie}).json()['UserID'])
infoReq = requests.get(f'https://api.roblox.com/marketplace/productinfo?assetId={assetId}').json()
productId = infoReq['ProductId']
itemName = infoReq['Name']

def getUserAssetId():
    global userAssetId
    cursor = ''
    while cursor != None:
        r = requests.get(f'https://inventory.roblox.com/v1/users/{userId}/assets/collectibles?sortOrder=Asc&limit=100&cursor={cursor}').json()
        if 'data' in r:
            for item in r['data']:
                if item['assetId'] == int(assetId):
                    userAssetId = item['userAssetId']
                    print(f'[{Fore.LIGHTCYAN_EX}={Fore.WHITE}] Found matching assetId ({Fore.LIGHTCYAN_EX}{assetId}{Fore.WHITE}) in inventory > userAssetId = {Fore.LIGHTCYAN_EX}{userAssetId}')
                    return None
            cursor = r['nextPageCursor']
        else:
            print(f'[{Fore.RED}-{Fore.WHITE}] Ratelimited, waiting {Fore.RED}60{Fore.WHITE} seconds')
    print(f'[{Fore.RED}={Fore.WHITE}] Unable to find {Fore.RED}{assetId}{Fore.WHITE} in your inventory')


def getCsrf():
    return requests.post('https://auth.roblox.com/v2/login', cookies={'.ROBLOSECURITY': cookie}).headers['X-CSRF-TOKEN']

def grabPrice():
    while True:
        itemInfo = requests.get(f'https://www.roblox.com/catalog/{assetId}', cookies={'.ROBLOSECURITY': cookie}).text
        currentPrice = int(re.search('data-expected-price="(.*?)"', itemInfo).group(1))
        sellerId = re.search('data-expected-seller-id="(.*?)"', itemInfo).group(1)

        if userId != sellerId:
            print(f'{Fore.WHITE}[{Fore.YELLOW}={Fore.WHITE}] {Fore.YELLOW}{sellerId}{Fore.WHITE} was selling lower than you, relisting for {Fore.YELLOW}{currentPrice-1}{Fore.WHITE} robux')
            x = putOffSale()
            if x == 'Sold':
                return None

            z = putOnSale(currentPrice)
            if z == 'Sold':
                return None
        time.sleep(5)

def putOffSale():
    csrf = getCsrf()
    sale = requests.patch(
        f'https://economy.roblox.com/v1/assets/{assetId}/resellable-copies/{userAssetId}',
        cookies={'.ROBLOSECURITY': cookie},
        json={},
        headers={'X-CSRF-TOKEN': csrf}
    ).json()
    if sale == {}:
        print(f'[{Fore.MAGENTA}+{Fore.WHITE}] {Fore.MAGENTA}{itemName} {Fore.WHITE}was put offsale (if it was never onsale, ignore)')
        return None
    else:
        if 'The user does not own the asset' in str(sale):
            print(f'[{Fore.BLUE}+{Fore.WHITE}] {Fore.BLUE}{itemName} {Fore.WHITE}sold for {Fore.BLUE}{currentSellingPrice} {Fore.WHITE}robux')

            data = {
                'embeds':[{
                    'color': int('2e88f5',16),
                    'fields': [
                        {'name': f'{itemName}','value': f'Sold for {currentSellingPrice} robux','inline':False},
                    ]
                }]
            }
            requests.post(webhook, json=data)

            return 'Sold'
        else:
            print(f'[{Fore.RED}-{Fore.WHITE}] {Fore.RED}{itemName} {Fore.WHITE}was NOT put offsale: {str(sale)}')
            return None

def putOnSale(currentPrice):
    global currentSellingPrice
    csrf = getCsrf()
    sale = requests.patch(
        f'https://economy.roblox.com/v1/assets/{assetId}/resellable-copies/{userAssetId}',
        cookies={'.ROBLOSECURITY': cookie},
        json={'price': currentPrice-1},
        headers={'X-CSRF-TOKEN': csrf}
    ).json()

    if sale == {}:
        currentSellingPrice = currentPrice-1

        print(f'[{Fore.GREEN}+{Fore.WHITE}] {Fore.GREEN}{itemName} {Fore.WHITE}was put onsale for {Fore.GREEN}{currentPrice-1}{Fore.WHITE} robux')

        data = {
            'embeds':[{
                'color': int('ff700f',16),
                'fields': [
                    {'name': f'{itemName}','value': f'Relisted for {currentPrice-1} robux','inline':False},
                ]
            }]
        }
        requests.post(webhook, json=data)

        return None
    else:
        if 'The user does not own the asset' in str(sale):
            print(f'[{Fore.BLUE}+{Fore.WHITE}] {Fore.BLUE}{itemName} {Fore.WHITE}sold for {Fore.BLUE}{currentSellingPrice} {Fore.WHITE}robux')

            data = {
                'embeds':[{
                    'color': int('2e88f5',16),
                    'fields': [
                        {'name': f'{itemName}','value': f'Sold for {currentSellingPrice} robux','inline':False},
                    ]
                }]
            }
            requests.post(webhook, json=data)

            return 'Sold'
        else:
            print(f'[{Fore.RED}-{Fore.WHITE}] {Fore.RED}{itemName} {Fore.WHITE}was NOT put onsale: {str(sale)}')
            return None

getUserAssetId()
grabPrice()