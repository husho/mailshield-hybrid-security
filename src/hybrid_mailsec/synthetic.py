from __future__ import annotations

import argparse
import datetime as dt
import random
from pathlib import Path


def _rand_ip(rng: random.Random) -> str:
    return f"{rng.randint(1,223)}.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(1,254)}"


def _message_id(rng: random.Random) -> str:
    return "".join(rng.choice("0123456789ABCDEF") for _ in range(32)) + ".MAI"


def _smtp_log_header(day: dt.date) -> list[str]:
    return [
        "#Software: MailEnable SMTP Server Version 1.0a",
        "#Version: 1.0",
        f"#Date: {day.strftime('%m/%d/%y')} 00:00:01",
        "#Fields: date time c-ip agent account s-ip s-port cs-method cs-uristem cs-uriquery s-computername sc-bytes cs-bytes cs-username",
    ]


def _mtafilter_header() -> str:
    return "Time\tAction\tMessageID\tConnector\tFilter\tResult\tAccount\tSender\tIPAddress\tData\tSubject"


def generate_synthetic_logs(
    output_dir: Path,
    hosts: int,
    days: int,
    events_per_day: int,
    seed: int,
) -> None:
    rng = random.Random(seed)
    start_day = dt.date(2026, 1, 1)

    domains = [
        "alpha-mail.net",
        "beta-fabric.com",
        "delta-consulting.org",
        "omega-hotel.co",
        "nova-trade.io",
    ]

    users = [
        "info",
        "sales",
        "support",
        "admin",
        "ops",
        "finance",
        "muhasebe",
        "contact",
    ]

    for host_num in range(1, hosts + 1):
        host_name = f"host{host_num}"
        host_id = f"HOST{host_num}"
        base = output_dir / f"{host_name}-Logging"
        smtp_dir = base / "SMTP"
        mta_dir = base / "MTA"
        smtp_dir.mkdir(parents=True, exist_ok=True)
        mta_dir.mkdir(parents=True, exist_ok=True)

        for d in range(days):
            day = start_day + dt.timedelta(days=d)
            day_tag = day.strftime("%y%m%d")

            smtp_lines: list[str] = _smtp_log_header(day)
            mta_lines: list[str] = [f"{day.strftime('%m/%d/%y')} 00:00:01\tLOG FILE STARTED"]
            mtafilter_lines: list[str] = [_mtafilter_header(), f"{day.strftime('%m/%d/%y')} 00:00:01\tStart\t-\t-\t-\t-\t-\t-\t-\t-\t-"]

            for i in range(events_per_day):
                sec = i % 86400
                ts = dt.datetime.combine(day, dt.time(0, 0, 0)) + dt.timedelta(seconds=sec)

                domain = rng.choice(domains)
                user = rng.choice(users)
                sender = f"{user}@{domain}"
                src_ip = _rand_ip(rng)
                server_ip = _rand_ip(rng)
                port = rng.randint(1000, 60000)

                # Normal traffic (MAIL/RCPT/DATA) and some AUTH attempts.
                if rng.random() < 0.82:
                    smtp_lines.append(
                        f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {src_ip} SMTP-IN {domain} {server_ip} {port} MAIL "
                        f"MAIL+FROM:<{sender}> 250+Requested+mail+action+okay,+completed {host_id} 43 36 {sender}"
                    )
                    smtp_lines.append(
                        f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {src_ip} SMTP-IN {domain} {server_ip} {port} RCPT "
                        f"RCPT+TO:<{sender}> 250+Requested+mail+action+okay,+completed {host_id} 43 32 {sender}"
                    )
                    smtp_lines.append(
                        f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {src_ip} SMTP-IN {domain} {server_ip} {port} DATA DATA "
                        f"354+Start+mail+input;+end+with+<CRLF>.<CRLF> {host_id} 46 6 {sender}"
                    )
                else:
                    fail = rng.random() < 0.85
                    result = "504+Invalid+Username+or+Password" if fail else "235+Authentication+successful"
                    smtp_lines.append(
                        f"{ts.strftime('%Y-%m-%d %H:%M:%S')} {src_ip} SMTP-IN {domain} {server_ip} {port} AUTH AUTH+LOGIN "
                        f"{result} {host_id} 34 14 {sender}"
                    )

                # MTA route entries
                msgid = _message_id(rng)
                mta_lines.append(
                    f"{ts.strftime('%m/%d/%y %H:%M:%S')}\t[{msgid}] from (SMTP) [SMTP:{sender}]->[SF:{domain}/{user}] Mapped Literal"
                )

                # Weak labels: occasional spam high/delete, some low suspicion.
                spam_roll = rng.random()
                if spam_roll < 0.004:
                    spam_msgid = _message_id(rng)
                    mtafilter_lines.append(
                        f"{ts.strftime('%m/%d/%y %H:%M:%S')}\tExecuted\t{spam_msgid}\tSMTP\tspam\tDELETE\t{domain}\t"
                        f"[SMTP:{sender}]\t{src_ip}\tCRITERIA=BODY, DATA=<MF-W>viagra</MF-W>\tPromo content"
                    )
                elif spam_roll < 0.015:
                    spam_msgid = _message_id(rng)
                    mtafilter_lines.append(
                        f"{ts.strftime('%m/%d/%y %H:%M:%S')}\tExecuted\t{spam_msgid}\tSMTP\t[System Spam Filter]\tADD_HEADER\t"
                        f"{domain}\t[SMTP:{sender}]\t{src_ip}\tHigh (960)\tPotential phishing"
                    )
                elif spam_roll < 0.05:
                    spam_msgid = _message_id(rng)
                    mtafilter_lines.append(
                        f"{ts.strftime('%m/%d/%y %H:%M:%S')}\tExecuted\t{spam_msgid}\tSMTP\t[System Spam Filter]\tADD_HEADER\t"
                        f"{domain}\t[SMTP:{sender}]\t{src_ip}\tLow (45)\tNewsletter"
                    )

            mtafilter_lines.append(f"{day.strftime('%m/%d/%y')} 23:59:59\tEnd\t-\t-\t-\t-\t-\t-\t-\t-\t-")

            (smtp_dir / f"ex{day_tag}.log").write_text("\n".join(smtp_lines) + "\n", encoding="utf-8")
            (mta_dir / f"MTA-Activity-{day_tag}.log").write_text("\n".join(mta_lines) + "\n", encoding="utf-8")
            (mta_dir / f"MTAFILTER-Report-{day_tag}.log").write_text(
                "\n".join(mtafilter_lines) + "\n", encoding="utf-8"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic MailEnable-like logs for public demo")
    parser.add_argument("--output-dir", type=Path, default=Path("./sample_data/synthetic-logs"))
    parser.add_argument("--hosts", type=int, default=3)
    parser.add_argument("--days", type=int, default=21)
    parser.add_argument("--events-per-day", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_synthetic_logs(
        output_dir=args.output_dir,
        hosts=args.hosts,
        days=args.days,
        events_per_day=args.events_per_day,
        seed=args.seed,
    )
    print(f"[info] synthetic_logs_created={args.output_dir}")


if __name__ == "__main__":
    main()
