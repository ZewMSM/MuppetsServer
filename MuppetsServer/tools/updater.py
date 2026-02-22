import asyncio
import json
import logging
import os
import shutil
import zipfile
from asyncio import create_task

import aiohttp

from MuppetsServer.tools.MSMLocalization import MSMLocalization
from ZewSFS.Client import SFSClient
from ZewSFS.Types import SFSObject
from config import GameConfig
from database import init_database, logger
from database.daily_cumulative_login import DailyCumulativeLogin
from database.flip_board import FlipBoard, FlipLevel
from database.gene import Gene, AttunerGene
from database.island import Island, IslandMonster, IslandStructure, IslandThemeData
from database.level import Level
from database.monster import Monster, MonsterCostume, FlexEggs, RareMonsterData, EpicMonsterData, MonsterHome, \
    MonsterLevel
from database.scratch_offer import ScratchOffer
from database.store import StoreItem, StoreGroup, StoreCurrency, StoreReplacement
from database.structure import Structure
from database.stuff import NucleusReward, EntityAltCosts, TitanSoulLevel, TimedEvents, GameSettings

logging.basicConfig(
    level=logging.DEBUG if os.environ.get('type', 'release') == 'debug' else logging.INFO,
    format='%(levelname)s/%(name)s:\t%(message)s'
)


class Updater:
    username: str
    password: str
    login_type: str
    client_version: str
    access_key: str

    access_token: str
    user_game_id: str

    server_ip: str
    content_url: str

    async def _init(self, username: str, password: str, login_type: str, client_version: str, access_key: str):
        self.username = username
        self.password = password
        self.login_type = login_type
        self.client_version = client_version
        self.access_key = access_key

        async with aiohttp.ClientSession() as session:
            async with session.post('https://auth.bbbgame.net/auth/api/token', data={
                "g": 27,
                "u": self.username,
                "p": self.password,
                "t": self.login_type,
                "auth_version": "2.0.0",
            }) as resp:
                auth_response = json.loads(await resp.text())
                if not auth_response.get("ok"):
                    raise RuntimeError(auth_response.get("message"))

                self.access_token = auth_response.get("access_token")
                self.user_game_id = auth_response.get("user_game_id")[0]

            async with session.post('https://msmpc.bbbgame.net/pregame_setup.php', headers={"Authorization": self.access_token}, data={
                'client_version': self.client_version,
                'access_key': self.access_key,
                "device_model": "PCDevice",
                "device_vendor": "wintel",
                "device_id": "d0f6b5ed-0bb8-486d-b2dc-2c92fc3cba7d",
                "platform": 'pc',
                "os_version": "10",
                "auth_version": "2.0.0",
                "g": "27",
                "tcs": "1"
            }) as resp:
                pregame_response = json.loads(await resp.text())
                if not pregame_response.get("ok"):
                    raise RuntimeError(pregame_response.get("message"))

                self.server_ip = pregame_response.get("serverIp")
                self.content_url = pregame_response.get("contentUrl")

            return self


class DatabaseUpdater(Updater):
    sfs_client: SFSClient

    async def init(self, username: str, password: str, login_type: str, client_version: str, access_key: str):
        await self._init(username, password, login_type, client_version, access_key)

        self.sfs_client = SFSClient()
        await self.sfs_client.connect(self.server_ip, 9933)

        login_params = SFSObject()
        login_params.putUtfString("access_key", self.access_key)
        login_params.putUtfString("token", self.access_token)
        login_params.putUtfString("last_update_version", '')
        login_params.putUtfString("client_os", '18.1')
        login_params.putUtfString("client_platform", 'ios')
        login_params.putUtfString("client_device", 'iPad8,6')
        login_params.putUtfString("raw_device_id", '56B30EF0-DBD1-5755-9040-B649B587DE1E')
        login_params.putUtfString("client_version", self.client_version)

        await self.sfs_client.send_login_request("MySingingMonsters", self.user_game_id, "", login_params)
        while 1:
            cmd, params = await self.sfs_client.wait_requests(["gs_initialized", "gs_player_banned", "gs_client_version_error", "gs_display_generic_message", "game_settings"])
            if cmd == "gs_initialized":
                return True
            elif cmd == "gs_player_banned":
                raise RuntimeError(params.get("reason"))
            elif cmd == "gs_client_version_error":
                raise RuntimeError("Client version is outdated.")
            elif cmd == "gs_display_generic_message":
                raise RuntimeError("Generic message: " + params.getUtfString("message"))
            elif cmd == 'game_settings' and 'user_game_settings' in params:
                for data in params.get('user_game_settings'):
                    obj = await GameSettings.from_sfs_object(data)
                    await obj.update_if_exists()
                    await obj.save()

    async def update_genes(self):
        response = await self.sfs_client.request('db_gene')
        for data in response.get('genes_data'):
            obj = await Gene.from_sfs_object(data)
            await obj.save()

    async def update_levels(self):
        response = await self.sfs_client.request('db_level')
        for data in response.get('level_data'):
            obj = await Level.from_sfs_object(data)
            await obj.save()

    async def update_scratch_offers(self):
        response = await self.sfs_client.request('db_scratch_offs')
        for data in response.get('scratch_offs'):
            obj = await ScratchOffer.from_sfs_object(data)
            await obj.save()

    async def update_monsters(self):
        async def monster_task(data):
            obj = await Monster.from_sfs_object(data)
            for level in data.get('levels', []):
                async with await MonsterLevel.from_sfs_object(level) as lvl:
                    lvl.monster_id = obj.id
                    await lvl.update_if_exists()
            await obj.save()

        response = await self.sfs_client.request('db_monster')
        await asyncio.gather(*[asyncio.create_task(monster_task(data)) for data in response.get('monsters_data')])

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_monster')
            await asyncio.gather(*[asyncio.create_task(monster_task(data)) for data in response.get('monsters_data')])

    async def update_structures(self):
        response = await self.sfs_client.request('db_structure')
        for data in response.get('structures_data'):
            obj = await Structure.from_sfs_object(data)
            await obj.save()

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_structure')
            for data in response.get('structures_data'):
                obj = await Structure.from_sfs_object(data)
                await obj.save()

    async def update_islands(self):
        async def update_i_task(dat):
            obj = await Island.from_sfs_object(dat)
            await obj.save()

            await asyncio.gather(*[asyncio.create_task(update_c_task(IslandMonster, monster, obj.id)) for monster in dat.get('monsters')])
            await asyncio.gather(*[asyncio.create_task(update_c_task(IslandStructure, structure, obj.id)) for structure in dat.get('structures')])

        async def update_c_task(cls, dat, iid):
            x_obj = await cls.from_sfs_object(dat)
            x_obj.island_id = iid
            if cls == IslandMonster and x_obj.monster == 815:
                cls.instrument = '018_SOUL_1.bin'
            await x_obj.update_if_exists()
            await x_obj.save()

        response = await self.sfs_client.request('db_island_v2')
        await asyncio.gather(*[asyncio.create_task(update_i_task(data)) for data in response.get('islands_data')])

    async def update_island_themes(self):
        response = await self.sfs_client.request('db_island_themes')
        for data in response.get('island_theme_data'):
            obj = await IslandThemeData.from_sfs_object(data)
            await obj.save()

    async def update_store(self):
        response = await self.sfs_client.request('db_store_v2')
        for data in response.get('store_item_data'):
            obj = await StoreItem.from_sfs_object(data)
            await obj.save()
        for data in response.get('store_group_data'):
            obj = await StoreGroup.from_sfs_object(data)
            await obj.save()
        for data in response.get('store_currency_data'):
            obj = await StoreCurrency.from_sfs_object(data)
            await obj.save()

    async def update_costumes(self):
        response = await self.sfs_client.request('db_costumes')
        for data in response.get('costume_data'):
            obj = await MonsterCostume.from_sfs_object(data)
            await obj.save()

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_costumes')
            for data in response.get('costume_data'):
                obj = await MonsterCostume.from_sfs_object(data)
                await obj.save()

    async def update_flip_boards(self):
        response = await self.sfs_client.request('gs_flip_boards')
        for data in response.get('flip_boards'):
            obj = await FlipBoard.from_sfs_object(data)
            await obj.save()

    async def update_flip_levels(self):
        response = await self.sfs_client.request('gs_flip_levels')
        for data in response.get('flip_levels'):
            obj = await FlipLevel.from_sfs_object(data)
            await obj.save()

    async def update_daily_cumulative_login(self):
        response = await self.sfs_client.request('db_daily_cumulative_login')
        for data in response.get('daily_cumulative_login_data'):
            obj = await DailyCumulativeLogin.from_sfs_object(data)
            await obj.save()

    async def update_flexeggdefs(self):
        response = await self.sfs_client.request('db_flexeggdefs')
        for data in response.get('flex_egg_def_data'):
            obj = await FlexEggs.from_sfs_object(data)
            await obj.save()

    async def update_attuner_genes(self):
        response = await self.sfs_client.request('db_attuner_gene')
        for data in response.get('attuner_gene_data'):
            obj = await AttunerGene.from_sfs_object(data)
            await obj.save()

    async def update_loot(self):
        response = await self.sfs_client.request('db_loot')
        # for data in response.get('loot_data'):
        #     obj = await AttunerGene.from_sfs_object(data)
        #     await obj.save()

    async def update_nucleus_reward(self):
        response = await self.sfs_client.request('db_nucleus_reward')
        for data in response.get('nucleus_reward_data'):
            obj = await NucleusReward.from_sfs_object(data)
            await obj.save()

    async def update_alt_costs(self):
        response = await self.sfs_client.request('db_entity_alt_costs')
        for data in response.get('entity_alt_data'):
            obj = await EntityAltCosts.from_sfs_object(data)
            await obj.save()

        for _ in range(response.get("numChunks", 1) - 1):
            response = await self.sfs_client.wait_extension_response('db_entity_alt_costs')
            for data in response.get('entity_alt_data'):
                obj = await EntityAltCosts.from_sfs_object(data)
                await obj.save()

    async def update_store_replacements(self):
        response = await self.sfs_client.request('db_store_replacements')
        for data in response.get('store_replacement_data'):
            obj = await StoreReplacement.from_sfs_object(data)
            await obj.save()

    async def update_titan_souls_levels(self):
        response = await self.sfs_client.request('db_titansoul_levels')
        for data in response.get('titansoul_level_data'):
            obj = await TitanSoulLevel.from_sfs_object(data)
            await obj.save()

    async def update_timed_events(self):
        response = await self.sfs_client.request('gs_timed_events')
        for data in response.get('timed_event_list'):
            obj = await TimedEvents.from_sfs_object(data)
            await obj.save()

    async def update_rare_monster_data(self):
        response = await self.sfs_client.request('gs_rare_monster_data')
        for data in response.get('rare_monster_data'):
            obj = await RareMonsterData.from_sfs_object(data)
            await obj.save()

    async def update_epic_monster_data(self):
        response = await self.sfs_client.request('gs_epic_monster_data')
        for data in response.get('epic_monster_data'):
            obj = await EpicMonsterData.from_sfs_object(data)
            await obj.save()

    async def update_monster_home_data(self):
        response = await self.sfs_client.request('gs_monster_island_2_island_data')
        for data in response.get('monster_island_2_island_data'):
            obj = await MonsterHome.from_sfs_object(data)
            await obj.update_if_exists()
            await obj.save()

    async def update_cant_breed(self):
        response = await self.sfs_client.request('gs_cant_breed')
        async with GameSettings() as obj:
            obj.key = 'cant_breed_monsters'
            obj.value = json.dumps(response.get('monsterIds'))
            await obj.update_if_exists()

    async def test(self):
        response = await self.sfs_client.request('gs_player', SFSObject().putLong('user_structure_id', 3).putInt('pos_x', 200).putInt('pos_y', 50))
        print(response.tokenize())
        await self.sfs_client.read_response()
        await self.sfs_client.read_response()
        await self.sfs_client.read_response()


class ContentUpdater(Updater):
    sfs_client: SFSClient
    localization_patch = None

    async def init(self, username: str, password: str, login_type: str, client_version: str, access_key: str):
        await self._init(username, password, login_type, client_version, access_key)

        with open('content/localization_patch.json') as f:
            self.localization_patch = json.loads(f.read())

    @staticmethod
    def create_path(path):
        folder_list = path.split('/')
        current_path = ''

        for ind, folder in enumerate(folder_list):
            current_path = os.path.join(current_path, folder)
            if not os.path.exists(current_path) and ind < len(folder_list) - 1:
                os.mkdir(current_path)
        return path

    async def get_files(self):
        result = []

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.content_url}") as resp:
                # {'localName': 'text/ru.utf8', 'serverName': 'text/ru.utf8', 'checksum': '36115b6d5d548d5bb0acd704cb8990e3', 'link': 'https://dlc2.bbbgame.net/my_singing_monsters/dlc/4.1.2/r39218-PheTmwhc/text/ru.utf8'}
                for item in json.loads(await resp.text()):
                    item["link"] = f"{'/'.join(self.content_url.split('/')[:-1])}/{item['serverName']}"
                    result.append(item)
                return result


    async def download_file(self, path, link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                with open(path, "wb") as f:
                    f.write(await resp.read())

    async def download_task(self, file):
        rev, *filename = '/r'.join(file.get('link').split('/r')[1:]).split('/')
        filename = "/".join(filename)
        if not '.' in filename:
            return

        download_path = f'content/updates/{self.client_version}/r{rev}/{filename}'
        await self.download_file(self.create_path(download_path), file.get('link'))

        logger.info(f'Downloaded {filename} for {self.client_version}/r{rev}')

        if 'text/' in file['localName']:
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(f"content/updates/{self.client_version}/tmp/")

            for ffl in os.listdir(f"content/updates/{self.client_version}/tmp/text/"):
                source_file = os.path.join(f"content/updates/{self.client_version}/tmp/text/", ffl)
                target_file = os.path.join(f"content/updates/{self.client_version}/tmp/", ffl)

                if os.path.exists(target_file):
                    os.remove(target_file)
                shutil.move(source_file, target_file)

            file['localName'] = file['localName'].split('/')[-1]

            try:
                a = open(f"content/updates/{self.client_version}/tmp/{file['localName']}", 'rb')
                local = MSMLocalization().loadFromFile(a)
                enc = 'utf-8'
            except:
                a = open(f"content/updates/{self.client_version}/tmp/{file['localName']}", 'rb')
                local = MSMLocalization().loadFromFile(a, "latin-1")
                enc = 'latin-1'
            finally:
                a.close()

            lang = file['localName'].split('.')[0]

            for k, v in self.localization_patch.items():
                local.setLocalByKey(k, v.get(lang, v.get('en', k)))

            with open(f"content/updates/{self.client_version}/tmp/{file['localName']}", 'wb') as f:
                local.saveToFile(f, enc)

            self.create_path(f'content/updates/{self.client_version}/patched_text/text/')
            with zipfile.ZipFile(f"content/updates/{self.client_version}/patched_text/text/{file['localName']}", 'w', zipfile.ZIP_DEFLATED) as zipf:
                arcname = os.path.join('text/' + file['localName'])
                zipf.write(f"content/updates/{self.client_version}/tmp/{file['localName']}", arcname)


            logger.info(f'Patched localizations in {filename}')

    async def download_updates(self):
        logger.info(f"Downloading updates from {self.content_url}")
        await asyncio.gather(*[asyncio.create_task(self.download_task(file)) for file in await self.get_files()])


async def main():
    content_updater = ContentUpdater()
    await content_updater.init(GameConfig.ServiceAccount.Steam.login, GameConfig.ServiceAccount.Steam.password, GameConfig.ServiceAccount.Steam.login_type, GameConfig.ServiceAccount.version, GameConfig.ServiceAccount.access_key)
    await content_updater.download_updates()

    await init_database()

    database_updater = DatabaseUpdater()
    await database_updater.init(GameConfig.ServiceAccount.Steam.login, GameConfig.ServiceAccount.Steam.password, GameConfig.ServiceAccount.Steam.login_type, GameConfig.ServiceAccount.version, GameConfig.ServiceAccount.access_key)
    # await database_updater.test()

    await database_updater.update_islands()

    await database_updater.update_monsters()
    await database_updater.update_genes()
    await database_updater.update_levels()
    await database_updater.update_scratch_offers()
    await database_updater.update_structures()
    await database_updater.update_islands()
    await database_updater.update_island_themes()
    await database_updater.update_store()
    await database_updater.update_costumes()
    await database_updater.update_flip_boards()
    await database_updater.update_flip_levels()
    await database_updater.update_daily_cumulative_login()
    await database_updater.update_flexeggdefs()
    await database_updater.update_attuner_genes()
    await database_updater.update_loot()
    await database_updater.update_nucleus_reward()
    await database_updater.update_alt_costs()
    await database_updater.update_store_replacements()
    await database_updater.update_titan_souls_levels()
    await database_updater.update_timed_events()
    await database_updater.update_rare_monster_data()
    await database_updater.update_epic_monster_data()
    await database_updater.update_monster_home_data()
    await database_updater.update_cant_breed()


if __name__ == '__main__':
    asyncio.run(main())
