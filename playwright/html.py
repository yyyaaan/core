from bbcsports import bbc_sports
from sryhma import bonus_doubled


def sports_and_bonus():
    output = bbc_sports()
    bonus = bonus_doubled()
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

    output["html"] += """
        <p><small>
            <a href="https://www.bbc.com/sport/football/scores-fixtures">BBC Sports</a> |
            <a href="https://hok-elanto.fi/asiakasomistajapalvelu/ajankohtaista-asiakasomistajalle/">HOK Elanto</a> |
            <a href="https://hameenmaa.fi/ajankohtaista/?cat=etu-s-etukortilla">Hämeenmaa</a> |
            <a href="https://vbo.fi/ajankohtaista-osuuskaupastasi/?cat=edut-ja-vinkit">VBO</a>
        </small></p>
    """
    return output
