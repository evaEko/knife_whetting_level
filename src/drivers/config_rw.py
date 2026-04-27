_CONFIG_PATH = 'config.py'


def read_config(key):
    search = key.upper()
    try:
        with open(_CONFIG_PATH) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('#') or '=' not in stripped:
                    continue
                k, _, v = stripped.partition('=')
                if k.strip().upper() == search:
                    v = v.partition('#')[0].strip().strip('"\'')
                    return v
    except Exception:
        pass
    return None


def write_config(key, py_value):
    search = key.upper()
    new_line = f'{search} = {py_value}\n'
    print(f"write_config: searching for {search}, new_line: {repr(new_line)}")
    try:
        with open(_CONFIG_PATH) as f:
            lines = f.readlines()
    except Exception as e:
        print(f"write_config: read error: {e}")
        return False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') or '=' not in stripped:
            continue
        k = stripped.partition('=')[0].strip().upper()
        if k == search:
            print(f"write_config: found at line {i}, old: {repr(line)}")
            lines[i] = new_line
            try:
                with open(_CONFIG_PATH, 'w') as f:
                    f.write(''.join(lines))
                import os
                os.sync()
                print(f"write_config: wrote successfully")
                return True
            except Exception as e:
                print(f"write_config: write error: {e}")
                return False
    print(f"write_config: {search} not found in config.py")
    return False
