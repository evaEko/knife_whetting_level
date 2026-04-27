import ctx


def load_preset_angles():
    try:
        with open('angles.csv') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) == 2:
                    ctx.angle_settings.append((parts[0].strip(), float(parts[1].strip())))
        print(f"Loaded {len(ctx.angle_settings)} angle presets")
    except Exception as e:
        print(f"angles.csv error: {e}")
