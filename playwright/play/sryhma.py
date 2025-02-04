from play.PlayPage import PlayPage


def play_hok_elanto():
    play = PlayPage("https://hok-elanto.fi/asiakasomistajapalvelu/ajankohtaista-asiakasomistajalle/", timeout=12000)  # noqa: E501

    output = "failed to load content"
    for x in play.page.query_selector_all("div.so-widget-sow-editor-base"):
        title = x.query_selector("h3").inner_text()
        if "tuplana" in title.lower():
            output = x.query_selector(
                "div#layout-column_column-3 > div:last-child"
            ).inner_text()

    print("Before processing:", output.replace("\n", ""))
    play.stop()
    return output


def play_vbo():
    play = PlayPage("https://vbo.fi/ajankohtaista-osuuskaupastasi/?cat=edut-ja-vinkit", timeout=12000)  # noqa: E501
    title = play.page.query_selector("div.row_news").inner_text()
    titles = [x for x in title.split("\n") if "tuplana" in x.lower() and "31.10.–3.11." not in x]
    play.stop()
    return "".join(titles)


def play_hameenmaa():
    play = PlayPage("https://hameenmaa.fi/ajankohtaista/?cat=etu-s-etukortilla", timeout=12000)  # noqa: E501
    title = play.page.query_selector("div.news_card").inner_text()
    titles = [x for x in title.split("\n") if "tuplana" in x.lower()]
    play.stop()
    return "".join(titles)


def bonus_doubled():
    output = {"flag": False, "text": "no offer available"}
    text_vbo, text_hameenmaa = "", ""
    try:
        text_vbo = play_vbo()
    except Exception as e:
        print("Error VBO", e)

    try:
        text_hameenmaa = play_hameenmaa()
    except Exception as e:
        print("Error Hameenmaa", e)

    try:
        text = play_hok_elanto()
        shops = [
            x for x in text.split("\n")
            if len(x) > 3 and "koske prisma.fi" not in x.lower()
        ]
        shops += [text_vbo] if len(text_vbo) > 3 else []
        shops += [text_hameenmaa] if len(text_hameenmaa) > 3 else []
        if len(shops) > 1:
            output = {
                "flag": True,
                "text": "- " + "<br/>- ".join(shops[1:]),
            }
        return output
    except Exception as e:
        print("Error Hok Elanto", e)
        return {
            "flag": False,
            "text": f"failed to load content: {e}",
        }
