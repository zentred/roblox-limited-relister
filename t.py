import requests, os, json, time, re, threading
from colorama import Fore, init
init()

config = json.load(open('config.json','r'))

class Run:

    def __init__(self, config):
        self.robloxCookie = config['robloxCookie']
        self.discordWebhook = config['discordWebhook']
        self.sellUnderRap = config['sellUnderRap']
        self.relistInventory = config['relistInventory']
        self.dontSell = config['dontSell']
        self.myItems = config['myItems']
        self.req = requests.Session()
        self.req.cookies['.ROBLOSECURITY'] = self.robloxCookie
        self.inventoryData = {}
        self.userId = None
        self.important()

    def grabTotalInventory(self):
        inventory = self.req.get(f'https://inventory.roblox.com/v1/users/{self.userId}/assets/collectibles?sortOrder=Asc&limit=100').json()
        if 'data' in inventory:
            if config['relistInventory'] == True:
                for item in inventory['data']:
                    if item['assetId'] not in self.dontSell:
                        self.inventoryData[str(item['assetId'])] = [item['userAssetId'], item['recentAveragePrice'], item['name'], 0]
            else:
                for item in inventory['data']:
                    if str(item['assetId']) in self.myItems:
                        self.inventoryData[str(item['assetId'])] = [item['userAssetId'], item['recentAveragePrice'], item['name'], self.myItems[str(item['assetId'])]['minimumPrice']]

    def updateRap(self):
        while True:
            inventory = self.req.get(f'https://inventory.roblox.com/v1/users/{self.userId}/assets/collectibles?sortOrder=Asc&limit=100').json()
            if 'data' in inventory:
                for item in inventory['data']:
                    if str(item['assetId']) in self.inventoryData:
                        self.inventoryData[str(item['assetId'])][1] = item['recentAveragePrice']
            time.sleep(60)

    def grabPrice(self):
        while True:
            for item in self.inventoryData:
                userAssetId, recentAveragePrice, itemName, minimumPrice = self.inventoryData[item][0], self.inventoryData[item][1], self.inventoryData[item][2], self.inventoryData[item][3]
                itemInfo = self.req.get(f'https://www.roblox.com/catalog/{item}').text
                currentPrice = int(re.search('data-expected-price="(.*?)"', itemInfo).group(1))
                sellerId = re.search('data-expected-seller-id="(.*?)"', itemInfo).group(1)

                if self.userId != sellerId and currentPrice > minimumPrice:
                    if self.sellUnderRap == False and currentPrice <= recentAveragePrice: continue

                    print(f"{Fore.LIGHTCYAN_EX}Your price on '{itemName}' was beat, relisting for {currentPrice-1} robux")
                    self.toggleSale({'price': currentPrice-1}, userAssetId, item, itemName)
                    

            time.sleep(30)

    def getCsrf(self):
        return self.req.post('https://auth.roblox.com/v2/login').headers['X-CSRF-TOKEN']

    def toggleSale(self, json, userAssetId, assetId, itemName):
        csrf = self.getCsrf()
        sale = self.req.patch(
            f'https://economy.roblox.com/v1/assets/{assetId}/resellable-copies/{userAssetId}',
            json=json,
            headers={'X-CSRF-TOKEN': csrf}
        ).json()

        if sale == {}:
            print(f'{Fore.GREEN}{itemName} was put onsale {Fore.GREEN}for {json["price"]} robux')
            
            data = {
                'embeds':[{
                    'color': int('2e88f5',16),
                    'fields': [
                        {'name': f'{itemName}','value': f'Relisted for {json["price"]}','inline':False},
                    ]
                }]
            }
            requests.post(self.discordWebhook, json=data)

        elif 'The user does not own the asset' in str(sale):

            data = {
                'embeds':[{
                    'color': int('ff700f',16),
                    'fields': [
                        {'name': f'{itemName}','value': f'This limited sold','inline':False},
                    ]
                }]
            }
            requests.post(self.discordWebhook, json=data)
            self.inventoryData.pop(assetId)

            print(f'{Fore.YELLOW}{itemName} sold!')
        else:
            print(f'{Fore.RED}{itemName} sale status was not toggled due to this error: {str(sale)}')

            data = {
                'embeds':[{
                    'color': int('ff700f',16),
                    'fields': [
                        {'name': f'Unknown Error with {itemName}','value': f'{str(sale)}','inline':False},
                    ]
                }]
            }
            requests.post(self.discordWebhook, json=data)


    def important(self):
        self.userId = str(self.req.get('https://www.roblox.com/mobileapi/userinfo').json()['UserID'])
        self.grabTotalInventory()
        threading.Thread(target=self.updateRap).start()
        threading.Thread(target=self.grabPrice).start()
        

c = Run(config)
