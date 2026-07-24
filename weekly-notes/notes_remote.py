#!/usr/bin/env python3
"""Remote weekly-notes helper using paramiko over SSH/SFTP.

Notes are stored on a shared server so they can be reached from any machine.
This script never touches files outside the configured NOTES_DIR.

Usage:
  notes_remote.py path            Print current week's note file path
  notes_remote.py test            Test connection and list the notes dir
  notes_remote.py show            Print current week's note content (empty if none)
  notes_remote.py append "text"   Append a timestamped work item (creates file if needed)
  notes_remote.py list            List all note files in the notes dir
"""

import sys
import datetime
import posixpath
import paramiko

HOST = "10.193.108.180"
USER = "build"
PASSWORD = "build"
PORT = 22
NOTES_DIR = "/home/build/share_write/maximus/weekly_report"


def week_start_date(now=None):
    """Week runs Thursday 15:00 -> next Thursday 15:00. Return start date str."""
    now = now or datetime.datetime.now()
    today = now.date()
    delta = (today.weekday() - 3) % 7  # Thursday == 3
    last_thu = today - datetime.timedelta(days=delta)
    last_thu_dt = datetime.datetime.combine(last_thu, datetime.time(15, 0))
    if now < last_thu_dt:
        last_thu = last_thu - datetime.timedelta(days=7)
    return last_thu.strftime("%Y-%m-%d")


def week_filename():
    return "week_%s.md" % week_start_date()


def week_path():
    return posixpath.join(NOTES_DIR, week_filename())


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=10)
    return client


def sftp_exists(sftp, path):
    try:
        sftp.stat(path)
        return True
    except IOError:
        return False


def cmd_path():
    print(week_path())


def cmd_test():
    client = connect()
    sftp = client.open_sftp()
    if not sftp_exists(sftp, NOTES_DIR):
        print("CONNECTED but notes dir MISSING: %s" % NOTES_DIR)
    else:
        print("CONNECTED. Notes dir OK: %s" % NOTES_DIR)
        for f in sorted(sftp.listdir(NOTES_DIR)):
            print("  " + f)
    sftp.close()
    client.close()


def cmd_show():
    client = connect()
    sftp = client.open_sftp()
    p = week_path()
    if sftp_exists(sftp, p):
        with sftp.open(p, "r") as fh:
            sys.stdout.write(fh.read().decode("utf-8"))
    else:
        print("(no note file for this week yet: %s)" % p)
    sftp.close()
    client.close()


def cmd_list():
    client = connect()
    sftp = client.open_sftp()
    if sftp_exists(sftp, NOTES_DIR):
        for f in sorted(sftp.listdir(NOTES_DIR)):
            print(f)
    sftp.close()
    client.close()


def cmd_append(text):
    client = connect()
    sftp = client.open_sftp()
    p = week_path()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # Allow callers to pass literal "\n" (two chars) from the shell and have it
    # rendered as a real newline / sub-bullet in the note file.
    text = text.replace("\\n", "\n")
    entry = "- [%s] %s\n" % (stamp, text)
    if sftp_exists(sftp, p):
        with sftp.open(p, "a") as fh:
            fh.write(entry)
    else:
        header = "# Weekly Notes (week starting %s)\n\n" % week_start_date()
        with sftp.open(p, "w") as fh:
            fh.write(header + entry)
        print("Created new note file: %s" % p)
    print("Appended: %s" % entry.strip())
    sftp.close()
    client.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "path":
        cmd_path()
    elif cmd == "test":
        cmd_test()
    elif cmd == "show":
        cmd_show()
    elif cmd == "list":
        cmd_list()
    elif cmd == "append":
        if len(sys.argv) < 3:
            print("append needs text")
            return 1
        cmd_append(sys.argv[2])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
