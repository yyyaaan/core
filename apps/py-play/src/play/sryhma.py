from asyncio import gather

from play.PlayPage import PlayPage


async def play_hok_elanto():
    async with PlayPage(
        "https://hok-elanto.fi/s-etukortti/ajankohtaista-asiakasomistajalle",
        timeout=12000,
    ) as play:  # noqa: E501
        output = ">>>ready>>>"
        for x in await play.page.query_selector_all(
            "body > div:nth-child(2) > div > main > div:nth-child(3) > div > div > article"
        ):
            title_element = await x.query_selector("h2")
            title = await title_element.text_content()
            if title and "tuplana" in title.lower():
                elements = await x.query_selector_all("span")
                for each_span in elements:
                    span_text = await each_span.text_content()
                    output = output + "\n" + span_text

        output = "\n".join([x for x in output.split("\n") if x.startswith("-")])
        print("Before processing Hok-Elanto:", output)
        return output


async def play_vbo():
    async with PlayPage(
        "https://vbo.fi/ajankohtaista-osuuskaupastasi/?cat=edut-ja-vinkit",
        timeout=12000,
    ) as play:  # noqa: E501
        title = await play.page.text_content("h3")
        print("Before processing VBO:", title)
        titles = [
            x
            for x in title.split("\n")
            if "tuplana" in x.lower() and "31.10.–3.11." not in x
        ]

        return "".join(titles)


async def play_hameenmaa():
    async with PlayPage(
        "https://hameenmaa.fi/ajankohtaista/?cat=etu-s-etukortilla", timeout=12000
    ) as play:  # noqa: E501
        title = await play.page.text_content("div.news_card")
        print("Before processing Hameenmaa:", title)
        titles = [x for x in title.split("\n") if "tuplana" in x.lower()]
        return "".join(titles)


async def bonus_doubled():
    output = {"flag": False, "text": "no offer available"}
    text_vbo, text_hameenmaa, text_hok_elanto = "", "", ""

    results = await gather(
        play_vbo(),
        play_hameenmaa(),
        play_hok_elanto(),
        return_exceptions=True,
    )

    if isinstance(results[0], Exception):
        print("Error VBO", results[0])
    else:
        text_vbo = results[0]

    if isinstance(results[1], Exception):
        print("Error Hameenmaa", results[1])
    else:
        text_hameenmaa = results[1]

    if isinstance(results[2], Exception):
        print("Error Hok Elanto", results[2])
        return {
            "flag": False,
            "text": f"failed to load content: {results[2]}",
        }
    else:
        text_hok_elanto = results[2]

    shops = [
        x
        for x in text_hok_elanto.split("\n")
        if "Ei kampanjoita tällä hetkellä" not in x and len(x) > 5
    ]
    shops += [text_vbo] if len(text_vbo) > 3 else []
    shops += [text_hameenmaa] if len(text_hameenmaa) > 3 else []
    if len(shops):
        output = {
            "flag": True,
            "text": "- " + "<br/>- ".join(shops),
        }
    return output
