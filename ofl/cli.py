"""ofl: rent GPUs from the terminal."""

from __future__ import annotations

import argparse
import getpass
import os
import sys

from ofl import config
from ofl.client import ApiError, Client
from ofl.query import QueryError, parse


def table(rows: list[dict], columns: list[tuple[str, str]]) -> str:
    cells = [[title for title, _ in columns]]
    for row in rows:
        cells.append([str(row.get(key, "")) for _, key in columns])
    widths = [max(len(line[i]) for line in cells) for i in range(len(columns))]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip()
        for line in cells
    )


def cmd_login(args: argparse.Namespace) -> int:
    key = args.key or getpass.getpass("API key: ").strip()
    if not key:
        print("no key given", file=sys.stderr)
        return 1
    values = config.load()
    values["api_key"] = key
    config.save(values)
    print(f"saved to {config.path()}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    offers = Client(config.api_key()).search(parse(args.query), sort=args.sort, limit=args.limit)
    print(table(offers, [("ID", "id"), ("GPU", "gpu"), ("N", "gpus"), ("VRAM", "vram"),
                         ("EUR/H", "price"), ("REGION", "region"), ("UPTIME", "uptime")]))
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    onstart = open(args.onstart, encoding="utf-8").read() if args.onstart else None
    instance = Client(config.api_key()).create(
        args.offer, args.image, disk_gb=args.disk, bid=args.bid, onstart=onstart
    )
    print(f"instance {instance['id']} {instance['state']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    print(table(Client(config.api_key()).instances(),
                [("ID", "id"), ("STATE", "state"), ("GPU", "gpu"), ("IMAGE", "image"),
                 ("EUR/H", "price"), ("REGION", "region")]))
    return 0


def cmd_ssh(args: argparse.Namespace) -> int:
    instance = Client(config.api_key()).instance(args.instance)
    if instance.get("state") != "running":
        print(f"instance {args.instance} is {instance.get('state')}", file=sys.stderr)
        return 1
    os.execvp("ssh", ["ssh", "-p", str(instance["ssh_port"]), f"root@{instance['ssh_host']}", *args.command])


def cmd_logs(args: argparse.Namespace) -> int:
    sys.stdout.write(Client(config.api_key()).logs(args.instance, tail=args.tail))
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    print(Client(config.api_key()).stop(args.instance)["state"])
    return 0


def cmd_destroy(args: argparse.Namespace) -> int:
    Client(config.api_key()).destroy(args.instance)
    print("destroyed")
    return 0


def cmd_balance(args: argparse.Namespace) -> int:
    balance = Client(config.api_key()).balance()
    print(f"{balance['eur']:.2f} EUR, spending {balance['burn_eur_h']:.2f} EUR/h")
    return 0


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="ofl", description=__doc__)
    sub = top.add_subparsers(dest="command", required=True)

    p = sub.add_parser("login", help="store an API key")
    p.add_argument("--key")
    p.set_defaults(run=cmd_login)

    p = sub.add_parser("search", help="find offers")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--sort", default="price", choices=["price", "vram", "uptime"])
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(run=cmd_search)

    p = sub.add_parser("create", help="start an instance on an offer")
    p.add_argument("offer", type=int)
    p.add_argument("--image", required=True)
    p.add_argument("--disk", type=int, default=40, help="GB")
    p.add_argument("--bid", type=float, help="EUR per hour; makes the instance interruptible")
    p.add_argument("--onstart", help="script to run when the container starts")
    p.set_defaults(run=cmd_create)

    p = sub.add_parser("list", help="your instances")
    p.set_defaults(run=cmd_list)

    p = sub.add_parser("ssh", help="open a shell on an instance")
    p.add_argument("instance")
    p.add_argument("command", nargs=argparse.REMAINDER)
    p.set_defaults(run=cmd_ssh)

    p = sub.add_parser("logs", help="container output")
    p.add_argument("instance")
    p.add_argument("--tail", type=int, default=200)
    p.set_defaults(run=cmd_logs)

    p = sub.add_parser("stop", help="stop an instance, keep its disk")
    p.add_argument("instance")
    p.set_defaults(run=cmd_stop)

    p = sub.add_parser("destroy", help="delete an instance and its disk")
    p.add_argument("instance")
    p.set_defaults(run=cmd_destroy)

    p = sub.add_parser("balance", help="credit left and current spend")
    p.set_defaults(run=cmd_balance)
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.run(args) or 0
    except QueryError as e:
        print(f"ofl: {e}", file=sys.stderr)
        return 2
    except ApiError as e:
        print(f"ofl: {e.message} (HTTP {e.status})", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"ofl: cannot reach the API: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
