from __future__ import print_function
import sys
import os
import hashlib
import json
from subprocess import call
from io import open

def run(options, url):
    dorkbot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

    if "wapiti_dir" in options:
        wapiti_path = os.path.join(os.path.abspath(options["wapiti_dir"]), "bin")
    elif os.path.isdir(os.path.join(dorkbot_dir, "tools", "wapiti", "bin")):
        wapiti_path = os.path.join(dorkbot_dir, "tools", "wapiti", "bin")
    else:
        wapiti_path = ""

    wapiti_cmd = os.path.join(wapiti_path, "wapiti")

    if "report_dir" in options:
        report_dir = os.path.abspath(options["report_dir"])
    else:
        report_dir = os.path.join(dorkbot_dir, "reports")

    url_base = url.split("?", 1)[0]
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    report_stderr = os.path.join(report_dir, url_hash + ".stderr")
    report_json = os.path.join(report_dir, url_hash + ".json")
    scan_cmd = [wapiti_cmd]
    scan_cmd += ["--url", url]
    scan_cmd += ["--module", "blindsql,exec,file,permanentxss,sql,xss"]
    scan_cmd += ["--scope", "page"]
    scan_cmd += ["--timeout", "5"]
    scan_cmd += ["--format", "json"]
    scan_cmd += ["--output", report_json]

    if os.path.isfile(report_json) or os.path.isfile(report_stderr): 
        print("Skipping (found report file): " + url)
    else:
        print("Scanning: " + url)
        report_stderr_f = open(report_stderr, "a")
        try:
            ret = call(scan_cmd, cwd=wapiti_path, stderr=report_stderr_f)
            if ret != 0: sys.exit(1)
        except OSError as e:
            if "No such file or directory" in e:
                print("Could not execute wapiti. If not in PATH, then download and unpack as /path/to/dorkbot/tools/wapiti/ or set wapiti_dir option to correct directory.", file=sys.stderr)
                report_stderr_f.close()
                os.remove(report_stderr)
                sys.exit(1)
        if os.path.isfile(report_stderr):
            report_stderr_f.close()
            os.remove(report_stderr)

        with open(report_json, encoding="utf-8") as data_file:
            contents = data_file.read()
            data = json.loads(contents)
            vulns = []
            for vuln_type in data["vulnerabilities"]:
                for vulnerability in data["vulnerabilities"][vuln_type]:
                    vuln = {}
                    vuln["vulnerability"] = vuln_type
                    vuln["url"] = data["infos"]["target"]
                    vuln["parameter"] = vulnerability["parameter"]
                    vuln["method"] = vulnerability["method"]
                    vulns.append(vuln)
        return vulns


