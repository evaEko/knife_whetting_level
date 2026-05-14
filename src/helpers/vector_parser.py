def parse(raw):
    """Parse 'x,y,z' string to (float, float, float) or None."""
    if raw is None:
        return None
    parts = raw.split(',')
    if len(parts) != 3:
        return None
    return (float(parts[0]), float(parts[1]), float(parts[2]))
