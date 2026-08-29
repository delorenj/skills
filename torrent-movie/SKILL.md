---
name: torrent-movie
description: "Download a movie or show by searching torrents and adding the best magnet link to qBittorrent. Triggers: download movie, download show, torrent, magnet, TheChung. Use when the user asks to download a movie, show, or torrent."
---

# Torrent Movie Downloader

Use this skill to search for torrents and add them to the local qBittorrent client.

## Operating Principles
- **Use the MCP Server for searching:** You have access to the `torrent-search-mcp` tools. Use `search_torrents` to find the media.
- **Filter and select:** Choose the best result based on seeders and quality.
- **Add to qBittorrent:** Use `get_magnet_link` to get the magnet URI, then run the bundled `scripts/add_torrent.py` script to send it to the qBittorrent instance.

## Workflow
1. Call `search_torrents` with the requested movie or show name.
2. Select the best torrent (highest seeders, appropriate resolution like 1080p).
3. Call `get_magnet_link` with the ID of the chosen torrent.
4. Run `python3 scripts/add_torrent.py "<magnet_uri>"` from this skill's directory. This script hits the local qBittorrent API and sets the save path to `/video` (mapped to `TheChung` share).

## Out of Scope
- This skill does not manage the downloaded files after they are added.
- This skill does not configure qBittorrent settings.
