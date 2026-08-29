#!/usr/bin/env python3
import argparse
import requests
import sys

def add_torrent(magnet_uri, savepath=None):
    # Hit the qBittorrent API via the local network IP to bypass auth 
    # (enabled via WebUI\AuthSubnetWhitelist in qBittorrent config)
    url = "http://192.168.1.12:8091/api/v2/torrents/add"
    data = {
        "urls": magnet_uri,
    }
    if savepath:
        data["savepath"] = savepath
        
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        if response.text == "Ok.":
            print(f"Successfully added magnet URI to qBittorrent (savepath: {savepath}).")
        else:
            print(f"qBittorrent response: {response.text}")
    except Exception as e:
        print(f"Error adding torrent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a magnet URI to qBittorrent")
    parser.add_argument("magnet", help="Magnet URI")
    parser.add_argument("--savepath", help="Optional save path inside the container (e.g. /video)", default="/video")
    args = parser.parse_args()
    
    add_torrent(args.magnet, args.savepath)
