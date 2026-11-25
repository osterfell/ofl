# ofl

Command line client and Python library for the [Osterfell](https://osterfell.com) GPU cloud.

    pip install git+https://github.com/osterfell/ofl

## Quick start

    ofl login                                     # paste an API key from the console
    ofl search "vram>=80 region=eu" --sort price
    ofl create 48211 --image pytorch:2.5-cuda12 --disk 80
    ofl list
    ofl ssh i-7c41
    ofl logs i-7c41 --tail 50
    ofl destroy i-7c41

Interruptible instances cost about half and can be reclaimed; give a bid:

    ofl create 48211 --image pytorch:2.5-cuda12 --bid 0.55

## Search filters

Terms are separated by spaces and all have to hold.

| field | type | example |
|---|---|---|
| `gpu` | text | `gpu=a100`, `gpu="rtx 4090"` |
| `gpus` | number | `gpus>=2` |
| `vram` | GB per GPU | `vram>=48` |
| `vcpu`, `ram`, `disk` | number | `ram>=64` |
| `price` | EUR per hour | `price<1.2` |
| `region` | text | `region=eu`, `region=hel-1` |
| `uptime` | percent | `uptime>=99` |
| `interruptible` | true/false | `interruptible=true` |

## From Python

```python
from ofl import Client

client = Client()                      # reads OFL_API_KEY or ~/.config/ofl/config.json
offer = client.search({"vram": {"gte": 80}})[0]
instance = client.create(offer["id"], image="pytorch:2.5-cuda12", disk_gb=80)
```

## Configuration

| variable | meaning |
|---|---|
| `OFL_API_KEY` | API key; overrides the config file |
| `OFL_API_BASE` | API base URL, default `https://api.osterfell.com/v1` |

## Development

    python -m unittest discover -s tests

MIT licensed.
