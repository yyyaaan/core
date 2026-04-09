from socket import gethostbyname


def get_browser_ip(port=9222):
    """remote debugging session blocks non-IP access if not localhost"""
    try:
        docker_ip = gethostbyname("host.docker.internal")
        return f"http://{docker_ip}:{port}"
    except Exception:
        return "172.17.0.1"  # Fallback for standard Linux Docker
