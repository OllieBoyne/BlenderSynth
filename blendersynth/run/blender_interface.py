LOG_PREPEND = "### *RENDER_EVENT*"


def log_event(msg):
    """Log event to file"""
    print(f"{LOG_PREPEND}: {msg}")
