from datetime import datetime
from json import loads, dumps
import asyncio

from play.bbcsports import bbc_sports
from play.sryhma import bonus_doubled


async def sports_and_bonus(refresh=False):
    cache_path = "/tmp/cache/cached_sports_and_bounus.json"

    if not refresh:
        try:
            with open(cache_path, "r") as f:
                output = loads(f.read())
                print("sports_and_bonus from cache ok")
                return output
        except Exception as e:
            print(e)

    output, bonus = await asyncio.gather(bbc_sports(), bonus_doubled())

    if bonus["flag"]:
        output["title"] = f"BonusX2 {output['title']}"
        output["html"] = f"""
        <p style="font-family: system-ui; color: #999; ">
            Bonus X2<br/>{bonus["text"]}
        </p>
        {output["html"]}
        """
    else:
        output["html"] += f"""
        <p style="font-family: system-ui; color: #999; font-size:small">
            Hok Elanto {bonus["text"]}
        </p>
        """

    output["html"] += f"""
        <p><small>
            <a href="https://www.bbc.com/sport/football/scores-fixtures">BBC Sports</a> |
            <a href="https://hok-elanto.fi/asiakasomistajapalvelu/ajankohtaista-asiakasomistajalle/">HOK Elanto</a> |
            <a href="https://hameenmaa.fi/ajankohtaista/?cat=etu-s-etukortilla">Hämeenmaa</a> |
            <a href="https://vbo.fi/ajankohtaista-osuuskaupastasi/?cat=edut-ja-vinkit">VBO</a>
            <br>Updated: {datetime.now():%b%d %H:%M:%S}
        </small></p>
    """
    with open(cache_path, "w") as f:
        f.write(dumps(output))
    return output
