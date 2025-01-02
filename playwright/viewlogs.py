from glob import glob

def view_logs(filename = ""):
    """
    filename, if empty, shows the most useful summary and links
    """
    if len(filename):
        try:
            with open(f"/mnt/archive/{filename}", "r") as f:
                content = f.read()
        except Exception as e:
            content = str(e)
        return (
            '<a href="/play/logs">back to logs</a><br><br>'
            f'<code>{content.replace("\n", "<br>")}</code>'
            '<br><br><a href="/play/logs">back to logs</a>'
        )

    log_latest = []
    log_files = []

    for filename in ["elenia", "dyndns", "extra"]:
        try:
            with open(f"/mnt/{filename}.log", "r") as f:
                content = f.read()
                log_latest.append("".join(
                    content.split("@")[-2:]
                ))
            log_files += sorted(glob(f"/mnt/archive/{filename}*", ))[-2:]
        except Exception:
            pass

    log_files = [x.split("/")[-1] for x in log_files]

    links = [f'<a href="/play/logs?filename={x}">{x}</a>' for x in log_files]
    content = "\n\n".join(log_latest)
    return (
        "<p>"
        f'<code>{content.replace("\n", "<br>")}</code>'
        f'</p><p>{" | ".join(links)}</p>'
    )
