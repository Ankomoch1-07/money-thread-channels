#!/usr/bin/env python3
"""完成mp4をYouTubeに限定→予約公開でアップロード。

channel_03/build/upload.py を移植。認証情報はチャンネル別に置く：
  channels/<channel>/secrets/client_secret.json（Google Cloud OAuthクライアント/デスクトップ）
  channels/<channel>/secrets/token.json（初回ブラウザ認証で自動生成・以降無人）
概要欄にフィクション明記(DISCLAIMER)を自動付与。

usage: upload.py <channel> <mp4> <title> <description> <publishAt(ISO8601 UTC)>
"""
import sys, pathlib
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.http
import google.oauth2.credentials as oc

SC = ["https://www.googleapis.com/auth/youtube.upload"]
DISCLAIMER = ("\n\n※本動画はフィクションであり、特定の投資を推奨するものではありません。"
              "投資は自己責任で。")

def creds(channel: str):
    root = pathlib.Path(__file__).resolve().parents[2]
    sdir = root / "channels" / channel / "secrets"
    token = sdir / "token.json"
    if token.exists():
        return oc.Credentials.from_authorized_user_file(str(token), SC)
    fl = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        str(sdir / "client_secret.json"), SC)
    cr = fl.run_local_server(port=0)
    open(token, "w").write(cr.to_json())
    return cr

def main(argv) -> int:
    channel, mp4, title, desc, publish_at = argv[:5]
    yt = googleapiclient.discovery.build("youtube", "v3", credentials=creds(channel))
    body = {
        "snippet": {"title": title, "description": desc + DISCLAIMER, "categoryId": "25"},
        "status": {"privacyStatus": "private", "publishAt": publish_at,
                   "selfDeclaredMadeForKids": False},
    }
    req = yt.videos().insert(
        part="snippet,status", body=body,
        media_body=googleapiclient.http.MediaFileUpload(mp4, chunksize=-1, resumable=True))
    r = req.execute()
    print("uploaded:", r["id"], "publishAt:", publish_at)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("usage: upload.py <channel> <mp4> <title> <description> <publishAt>"); sys.exit(2)
    sys.exit(main(sys.argv[1:]))
