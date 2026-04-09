from datetime import datetime, timedelta
from re import IGNORECASE, compile

from play.play.PlayPage import PlayPage, random_color


def u_time_cleaner(text):
    try:
        utc = datetime.strptime(text.split("\n")[0], "%H:%M")
        return f"{utc + timedelta(hours=2):%H:%M}"
    except Exception:
        return text


async def play_bbc_sports():
    async with PlayPage("https://www.bbc.com/sport/football/scores-fixtures") as play:
        fas = await play.page.query_selector_all(".e4zdov50")
        output = {}
        fa_name = ""
        for fa in fas:
            try:
                games_elements = await fa.query_selector_all("li.e1dih4s32")
                fa_games = []
                for game in games_elements:
                    try:
                        time_el = await game.query_selector("div.e1efi6g51")
                        home_el = await game.query_selector(
                            "div.e1efi6g53 > div > div > span:nth-child(2)"
                        )
                        away_el = await game.query_selector(
                            "div.e1efi6g52 > div > div > span:nth-child(2)"
                        )
                        note_el = await game.query_selector("span.e16en2lz0")

                        fa_games.append({
                            "time": u_time_cleaner(await time_el.inner_text())
                            if time_el
                            else "",
                            "home": await home_el.inner_text() if home_el else "",
                            "away": await away_el.inner_text() if away_el else "",
                            "note": await note_el.inner_text() if note_el else "",
                        })
                    except Exception as e:
                        print(f"Error processing a game: {e}")

                try:
                    fa_name_el = await fa.query_selector("h2")
                    if fa_name_el:
                        fa_name = await fa_name_el.inner_text()
                        output[fa_name] = fa_games
                except Exception:
                    # likely it is a group from the same FA
                    if fa_name in output:
                        output[fa_name] += fa_games
            except Exception as e:
                print(e)

        return output


async def bbc_sports():
    re_exclusion = compile(
        r"league one|league two|national league|fa trophy|efl trophy|scottish cup|lowland",
        IGNORECASE,
    )

    all_games = await play_bbc_sports()
    html_content = ""
    title_text = ""

    i = 0
    for fa, games in all_games.items():
        if bool(re_exclusion.search(fa)):
            continue

        i += 1
        the_color = random_color()

        formatted_games = [
            (
                '<span style="font-family: monospace; font-weight: bold;">'
                f"{x.get('time')}</span>&nbsp;&nbsp;"
                f'{x.get("home")} <span style="color:#999">vs</span> {x.get("away")}'
            )
            for x in games
        ]

        the_style = "margin-bottom: 30px; font-family: system-ui; "
        if i % 2:
            the_style += f"border-right: 9px solid {the_color}33; padding-right: 30px;"  # noqa: E501
        else:
            the_style += f"border-left: 9px solid {the_color}33;  padding-left: 30px; "  # noqa: E501

        html_content += f"""
            <div style="{the_style}">
                <h3 style="color: {the_color}">{fa}</h3>
                <p>{"<br/>".join(formatted_games)}</p>
            </div>
        """

        if i < 2:
            title_text += f"{len(formatted_games)} {fa.replace('THE ', '')}"

    return {
        "title": title_text,
        "html": html_content,
    }
