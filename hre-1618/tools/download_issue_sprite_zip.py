#!/usr/bin/env python3
"""Download ZIPs attached to authorized HRE sprite intake issue comments."""
import json, os, re, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAX_BYTES=90*1024*1024
HOSTS={"github.com","user-images.githubusercontent.com","private-user-images.githubusercontent.com"}
def main():
    event=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    issue=event.get("issue",{}); comment=event.get("comment",{})
    if not issue.get("title","").startswith("[HRE SPRITE INTAKE]"):
        raise SystemExit("Not designated intake issue")
    if comment.get("author_association") not in ("OWNER","MEMBER","COLLABORATOR"):
        raise SystemExit("Unauthorized intake author")
    body=comment.get("body","")
    urls=[]
    for link in re.findall(r'https://[^\s<>")\]]+',body):
        link=link.strip(".,;'")
        p=urllib.parse.urlparse(link)
        if p.hostname not in HOSTS or not p.path.lower().endswith(".zip"):
            continue
        if p.hostname=="github.com" and not p.path.startswith("/user-attachments/files/"):
            continue
        if link not in urls: urls.append(link)
    if not urls: raise SystemExit("No attached GitHub-hosted ZIP file found in comment")
    out=ROOT/"inbox"/"issue-attachments";out.mkdir(parents=True,exist_ok=True)
    for index,url in enumerate(urls[:3],1):
        req=urllib.request.Request(url,headers={"User-Agent":"HRE1618-sprite-intake"})
        with urllib.request.urlopen(req,timeout=90) as resp:
            final_host=(urllib.parse.urlparse(resp.url).hostname or "").lower()
            if final_host not in HOSTS and not final_host.endswith(".githubusercontent.com"):
                raise ValueError("Unexpected attachment download domain")
            data=resp.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES or not data.startswith(b"PK\x03\x04"):
            raise ValueError("Invalid or oversized ZIP attachment")
        basename=urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/",1)[-1])
        basename=re.sub(r"[^A-Za-z0-9_.-]","_",basename)[:70]
        name="issue-{}-comment-{}-{}-{}".format(issue["number"],comment["id"],index,basename)
        (out/name).write_bytes(data)
        print("Downloaded",name,len(data),"bytes")
if __name__=="__main__":main()
