import plotly.express as px

from datetime import datetime, timedelta
from glob import glob
from json import loads, dumps
from os import makedirs, path, remove
from pytz import timezone
from requests import get


class Electricity:
    cache_file = "/tmp/cache/spot_price.json"
    cache_svg_folder = "/tmp/cache/svg/"
    spot_prices_fi = {}
    output_time_fmt = "%H"

    def __determine_cache_svg_filename(self):
        return f"{self.cache_svg_folder}{datetime.now():%H}.svg"

    def __determine_update_strategy(self):
        self.get_spot_prices()
        if len(self.spot_prices_fi) < 1:
            self.get_spot_prices(force_update=True)
        if datetime.now().hour > 15 and len(self.spot_prices_fi) < 30:
            self.get_spot_prices(force_update=True)
        return None

    def get_current_svg(self):
        """get SVG from cache or render a new one"""

        current_file = self.__determine_cache_svg_filename()
        available_files = glob(f"{self.cache_svg_folder}*.svg")

        print(current_file, available_files)

        if current_file not in available_files:
            try:
                _ = [remove(x) for x in available_files]
            except Exception as e:
                print(e)
            self.render_plot_to_svg()

        with open(current_file, "r") as f:
            return f.read()
        return ""

    def render_plot_to_svg(self):
        """create SVG for the hour use get_svg for caching"""
        self.__determine_update_strategy()
        if not path.exists(self.cache_svg_folder):
            makedirs(self.cache_svg_folder)

        data = self.spot_prices_fi
        helsinki_tz = timezone('Europe/Helsinki')
        for entry in data:
            utc_time = datetime.fromtimestamp(entry['timestamp'])
            helsinki_time = utc_time.astimezone(helsinki_tz)
            entry["ts"] = helsinki_time.strftime(self.output_time_fmt)
            entry["cent"] = round(entry["price"] * 1.255 / 10, 2)
            entry["ts"] = "24" if entry["ts"] == "00" else entry["ts"]

        now = datetime.now()
        yesterday_end = datetime(now.year, now.month, now.day)
        data = [x for x in data if x['timestamp'] > yesterday_end.timestamp()]
        current_hour = now.strftime(self.output_time_fmt.replace("%M", "00"))
        price_now = next(x['cent'] for x in data if x['ts'] == current_hour)

        plot_data = {
            "ts": [x['ts'] for x in data],
            "cent": [x['cent'] for x in data],
            "colors": ["#a291e1" if x['ts'] == current_hour else "#c2d0e9" for x in data],
        }
        fig = px.bar(
            plot_data,
            x="ts",
            y="cent",
            labels={'x': 'Time', 'y': 'Price'},
            title=f"Nordpool Finland: {price_now} €ent/kWh",
            category_orders={'x': plot_data["ts"]}  # maintain order
        )
        fig.update_traces(
            marker_color=plot_data["colors"],
            showlegend=False,
            text=plot_data["cent"],
            textposition='inside'
        )
        fig.add_hline(y=8.96, line_dash="dash", line_color="#a291e1")
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_size=15,
            margin=dict(l=0, r=0, t=50, b=0),
        )
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        fig.write_image(self.__determine_cache_svg_filename())
        return None

    def get_spot_prices(self, force_update=False):
        """similar one used in poll"""
        try:
            with open(self.cache_file, "r") as f:
                spot_prices_fi = loads(f.read())
        except Exception as e:
            print("Spot price cache", e)
            force_update = True

        if force_update:
            spot_price = get(
                url=(
                    "https://dashboard.elering.ee/api/nps/price"
                    f"?start={datetime.now()-timedelta(days=1):%Y-%m-%d}T20:59:59.999Z"
                    f"&end={datetime.now()+timedelta(days=1):%Y-%m-%d}T03:59:59.999Z"
                )
            )
            print("Elering EE", spot_price.status_code, end=" ")
            spot_prices_fi = spot_price.json().get("data", {}).get("fi", [])
            with open(self.cache_file, "w") as f:
                f.write(dumps(spot_prices_fi, indent=2))

            print(
                f"n={len(spot_prices_fi)}",
                f"{datetime.fromtimestamp(spot_prices_fi[0]['timestamp']):%b%d %H:%M}",   # noqa: E501
                f"{datetime.fromtimestamp(spot_prices_fi[-1]['timestamp']):%b%d %H:%M}",  # noqa: E501
            ),
        
        self.spot_prices_fi = spot_prices_fi
        return spot_prices_fi
