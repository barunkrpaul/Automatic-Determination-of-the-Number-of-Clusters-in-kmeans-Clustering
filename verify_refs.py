#!/usr/bin/env python3
"""Verification script for the reference list of the review
"Automatic Determination of the Number of Clusters in K-Means Clustering:
A Critical Review, 2016--2026".

What it does, in plain terms. The script reads ref_records.json, which holds
one record per reference entry, viz. the entry number, the DOI printed in the
reference list, the arXiv identifier where one is printed instead, and the
plain text of the entry. For every DOI it queries the Crossref API and checks
two things. First, that the DOI resolves at all. Second, that the title
returned by Crossref shares enough words with the printed entry for the two to
be the same work. For every arXiv identifier it queries the arXiv API and
performs the same title check. Entries marked as caution entries in the paper
are expected to fail more often; the report separates them in the output.

Run it anywhere with internet access:

    python3 verify_refs.py

It writes verification_report.csv and prints a summary. It needs only the
Python standard library plus the requests package.
"""

import csv
import json
import re
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("Please install requests first: pip install requests")

MAILTO = "verification-script@example.org"  # set your email; Crossref asks for one
HEADERS = {"User-Agent": "ref-verifier/1.0 (mailto:%s)" % MAILTO}

STOP = set("a an the of on in for and to with by from is are as at its it "
           "clustering cluster clusters number k means k-means data".split())


def tokens(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2]


def title_overlap(crossref_title, entry_text):
    """Fraction of the record title's informative words found in the entry."""
    tt = tokens(crossref_title)
    if not tt:
        return 0.0
    et = set(tokens(entry_text))
    hit = sum(1 for w in tt if w in et)
    return hit / len(tt)


def check_doi(doi, entry):
    url = "https://api.crossref.org/works/" + doi
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        return "network-error", "", str(e)
    if r.status_code == 404:
        # DataCite mints some DOIs that Crossref does not know
        try:
            r2 = requests.get("https://api.datacite.org/dois/" + doi,
                              headers=HEADERS, timeout=30)
            if r2.status_code == 200:
                t = r2.json()["data"]["attributes"].get("titles", [{}])
                title = t[0].get("title", "") if t else ""
                ov = title_overlap(title, entry)
                return ("ok" if ov >= 0.5 else "title-mismatch"), title, "datacite, overlap %.2f" % ov
        except requests.RequestException:
            pass
        return "unresolved", "", "404 from Crossref and DataCite"
    if r.status_code != 200:
        return "http-%d" % r.status_code, "", ""
    msg = r.json().get("message", {})
    titles = msg.get("title") or [""]
    title = titles[0]
    ov = title_overlap(title, entry)
    status = "ok" if ov >= 0.5 else "title-mismatch"
    return status, title, "overlap %.2f" % ov


def check_arxiv(aid, entry):
    url = "https://export.arxiv.org/api/query?id_list=" + aid
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        return "network-error", "", str(e)
    if r.status_code != 200:
        return "http-%d" % r.status_code, "", ""
    m = re.search(r"<title>(.*?)</title>\s*</entry>", r.text, re.S)
    if m is None:
        m2 = re.findall(r"<title>(.*?)</title>", r.text, re.S)
        title = m2[1].strip() if len(m2) > 1 else ""
    else:
        title = m.group(1).strip()
    if not title or "Error" in title:
        return "unresolved", "", "no entry returned"
    title = re.sub(r"\s+", " ", title)
    ov = title_overlap(title, entry)
    status = "ok" if ov >= 0.5 else "title-mismatch"
    return status, title, "overlap %.2f" % ov


def main():
    records = json.load(open("ref_records.json"))
    rows = []
    counts = {"ok": 0, "title-mismatch": 0, "unresolved": 0, "other": 0, "skipped": 0}
    for rec in records:
        n = rec["ref"]
        entry = rec["entry"]
        if rec["doi"]:
            status, title, note = check_doi(rec["doi"], entry)
            kind = "doi"
            ident = rec["doi"]
        elif rec["arxiv"]:
            status, title, note = check_arxiv(rec["arxiv"], entry)
            kind = "arxiv"
            ident = rec["arxiv"]
        else:
            status, title, note = "skipped", "", "no identifier printed (venue mints none)"
            kind = ""
            ident = ""
        key = status if status in counts else "other"
        counts[key] = counts.get(key, 0) + 1
        rows.append([n, kind, ident, rec["caution"], status, note, title[:120]])
        print("[%3d] %-7s %-45s %s %s" % (n, kind, ident[:45], status, note))
        time.sleep(0.5)  # be polite to the APIs
    with open("verification_report.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ref", "id_type", "identifier", "caution_flag",
                    "status", "note", "record_title"])
        w.writerows(rows)
    print()
    print("Summary:", counts)
    print("Report written to verification_report.csv")
    bad = [r for r in rows if r[4] not in ("ok", "skipped") and not r[3]]
    if bad:
        print("\nEntries needing attention (not caution-flagged):")
        for r in bad:
            print("  [%d] %s %s -> %s" % (r[0], r[1], r[2], r[4]))
    else:
        print("\nAll non-caution entries verified or skipped as expected.")


if __name__ == "__main__":
    main()
