import json
import re
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class OITData:
    time: str
    services: dict


class OIT:
    def fetch_data(self) -> str:
        page_url = "https://status.ucmerced.edu/"

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa: E501  # noqa: E501
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "cache-control": "no-cache",
            "dnt": "1",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "referer": "https://www.google.com/",
            "sec-ch-ua": '"Microsoft Edge";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',  # noqa: E501
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",  # noqa: E501  # noqa: E501
        }

        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        return response.text

    def parse_status(self, html: str) -> OITData:
        # Regular expression to extract service names and statuses
        pattern = r'<p class="container_name"[^>]*>([^<]+)</p>.*?<p class="pull-right"[^>]*>([^<]+)</p>'  # noqa: E501
        matches = re.findall(pattern, html, re.DOTALL)

        services = {name.strip(): status.strip() for name, status in matches}

        # Add fetch timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return OITData(time=current_time, services=services)

    def get_status(self) -> dict:
        html = self.fetch_data()
        data = self.parse_status(html)
        return {"time": data.time, "services": data.services}


if __name__ == "__main__":
    oit = OIT()
    status_info = oit.get_status()
    print(json.dumps(status_info, indent=4))
