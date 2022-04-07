import asyncio
import json
import os
import random
import re
import sys
import zipfile
from configparser import ConfigParser

import aiohttp
import requests
import urllib3
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Prompt

console = Console()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
config = ConfigParser()

headers = {"Sec-Ch-Ua": "\"(Not(A:Brand\";v=\"8\", \"Chromium\";v=\"99\"",
           "Accept": "application/json, text/plain, */*",
           "Content-Type": "application/x-www-form-urlencoded",
           "Sec-Ch-Ua-Mobile": "?0",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
           "Sec-Ch-Ua-Platform": "\"Windows\"",
           "Origin": "https://steamworkshopdownloader.io",
           "Sec-Fetch-Site": "same-site",
           "Sec-Fetch-Mode": "cors",
           "Sec-Fetch-Dest": "empty",
           "Referer": "https://steamworkshopdownloader.io/",
           "Accept-Encoding": "gzip, deflate",
           "Accept-Language": "zh-CN,zh;q=0.9"
           }


def get_config():
    config_path = os.getcwd()
    config_file = os.path.join(config_path, "config.ini")
    if os.path.exists(config_file):
        config.read(config_file)
        if "savePath" in config.sections():
            save_path = config.get("savePath", "path")
            if not save_path:
                save_path = Prompt.ask(f"[{color()}][?]请输入下载文件保存目录,(例：D:\Wallpaper.Engine\projects\myprojects)\n")
                if save_path:
                    if not os.path.exists(save_path):
                        console.print("[red][!] 目录不存在")
                        Prompt.ask(f"[{color()}][&]按任意按键退出")
                        sys.exit(0)
                    config.set("savePath", "path", save_path)
                    with open(config_file, 'w') as fw:
                        config.write(fw)
                else:
                    console.print("[red][!] 输入错误")
                    Prompt.ask(f"[{color()}][&]按任意按键退出")
                    sys.exit(0)
            return save_path
        else:
            config.add_section("savePath")
            config.set("savePath", "path", "")
            with open(config_file, 'w') as fw:
                config.write(fw)
            get_config()
    else:
        console.print(f"[{color()}][-] 配置文件不存在,创建配置文件 {config_file}\n")
        sp = open(config_file, 'a')
        sp.close()
        get_config()


def state(func):
    def wrapper():
        return func()

    return wrapper()


def color():
    # colores = ["grey","green","yellow","blue","magenta","cyan","#6d9eeb", "#4fe8a6", "#33ffff"]
    # # return random.choice(colores)
    colores = "#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
    return colores


@state
def logo():
    logo = """
███████╗████████╗███████╗ █████╗ ███╗   ███╗                                          
██╔════╝╚══██╔══╝██╔════╝██╔══██╗████╗ ████║                                          
███████╗   ██║   █████╗  ███████║██╔████╔██║                                          
╚════██║   ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║                                          
███████║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║                                          
╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝                                          
                                                                                      
                ██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  █████╗ ██████╗ 
                ██╔══██╗██╔═══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔══██╗██╔══██╗
                ██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║███████║██║  ██║
                ██║  ██║██║   ██║██║███╗██║██║╚██╗██║██║     ██║   ██║██╔══██║██║  ██║
                ██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝██║  ██║██████╔╝
                ╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝  """

    console.print(f"[{color()}]{logo}")
    get_config()


async def get_link(session, node, publishedFileId):
    url = f"{node}/prod/api/download/request"
    # print(url)
    data = {"autodownload": False,
            "collectionId": None,
            "downloadFormat": "raw",
            "hidden": False,
            "publishedFileId": publishedFileId
            }

    try:
        # async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            res = await resp.text()
            uuid = json.loads(res)["uuid"] if resp.status == 200 else ""
            if uuid:
                down_link = await dow_path(node, uuid)
                if down_link:
                    # print(down_link)
                    return down_link
            return None
    except RuntimeError as e:
        console.print(f"[red]{e}")


async def dow_path(node, uuid):
    url = f"{node}/prod/api/download/status"
    data = {"uuids": [f"{uuid}"]}
    await asyncio.sleep(2)
    # 此处必须sleep,不然无法获取所有节点返回的信息
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                res = await resp.text()
                # print(res)
                storagePath = json.loads(res)[uuid]["storagePath"]
                if storagePath:
                    # storagePath = "431960/2009158089/1596418154/2009158089_sea_bunny_girl.raw.download.zip"
                    file_name = str(storagePath).split("/")[-1].replace("raw.download.", "")
                    # print(file_name)
                    down_link = f"{node}/prod/storage/{storagePath}?uuid={uuid}"
                    return down_link, file_name
                return ""
    except RuntimeError as e:
        console.print(f"[red]{e}")


def download(link, save_path, file_name):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36"}
    file_ = os.path.join(save_path, file_name)
    # print(link)
    try:
        resp = requests.get(link, headers=header, verify=False, stream=True, timeout=15)
        # print(resp.status_code)
        if resp.status_code == 200:
            console.print(f"[{color()}]Requesting [blue]{link}")
            with Progress() as progress:
                with open(file_, "wb") as f:
                    task = progress.add_task(f'[{color()}]Downloading...', total=int(resp.headers["Content-length"]))
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
            console.print(f"[{color()}]Downloaded [blue]{file_}")

            zip_file = zipfile.ZipFile(file_)
            unzip_path = os.path.join(save_path, str(file_name).replace(".zip", ""))
            if not os.path.exists(unzip_path):
                os.mkdir(unzip_path)
            for names in zip_file.namelist():
                console.print(f"[{color()}][&] try to unzip file [{names}] to path [{unzip_path}]")
                zip_file.extract(names, unzip_path)
                console.print(f"[{color()}][+] finish to unzip file [{names}] to path [{unzip_path}]")
            zip_file.close()
            os.remove(file_)
            return True
        return False
    except Exception as e:
        console.print(f"[red]{e}")
        return False


async def start(publishedFileId):
    console.print(f"[{color()}][*] 获取uuid中... ...")
    async with aiohttp.ClientSession() as session:
        task = [get_link(session, f"https://node0{i}.steamworkshopdownloader.io", publishedFileId) for i in range(1, 6)]
        console.print(f"[{color()}][%] 获取下载地址中 ... ...")
        links = await asyncio.gather(*task)
        # print(links)
    save_path = get_config()
    console.print(f"[{color()}][+] 开始下载 ... ...")
    for link, file_name in links:
        download_status = download(link, save_path, file_name)
        if download_status:
            Prompt.ask(f"[{color()}][&]按任意按键退出")
            return "Done"


if __name__ == "__main__":
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    console.print(f"[{color()}][0]创意工坊地址: https://steamcommunity.com/workshop/browse/?appid=431960")
    while True:
        id = Prompt.ask(
            f"[{color()}][&] 请输入下载ID(例：链接 https://steamcommunity.com/sharedfiles/filedetails/?id=2311180253 只需输入 2311180253 即可)\n")
        if id:
            unmber = re.findall("\D", id)
            if unmber:
                console.print("[red][!] 输入错误")
                Prompt.ask(f"[{color()}][&]按任意按键退出")
                sys.exit(0)
            try:
                asyncio.run(start(int(id)))
            except Exception as e:
                console.print(f"[red]{e}")
                Prompt.ask(f"[{color()}][&]按任意按键退出")
                sys.exit(0)
        else:
            console.print("[red][!] 输入错误")
            Prompt.ask(f"[{color()}][&]按任意按键退出")
            break
