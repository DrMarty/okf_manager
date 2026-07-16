### okf_fetch_url:
Fetch a single web page and return markdown plus outbound links. Mirrors the reference agent's `fetch_url` capability with crawl guards for allowed hosts, path prefixes, denied substrings, max pages, and max depth.

Args: `url`; optional `seeds`, `allowed_hosts`, `max_pages`, `max_depth`, `allowed_path_prefixes`, `denied_path_substrings`, `reset_state`.
