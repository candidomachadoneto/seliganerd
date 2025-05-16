import os
from datetime import date
from pathlib import Path

import pandas as pd
import snscrape.modules.twitter as sntwitter


def fetch_tweets():
    if os.getenv("GLEISI_TWEETS_FAKE"):
        yield {
            "id": 0,
            "date": date.today().isoformat(),
            "content": "Fake tweet about Selic",
            "likeCount": 0,
            "retweetCount": 0,
            "url": "https://twitter.com/gleisi/status/0",
        }
        return

    query = 'from:gleisi (Selic OR juros OR "Banco Central")'
    scraper = sntwitter.TwitterSearchScraper(query)
    for i, tweet in enumerate(scraper.get_items()):
        if i >= 100:
            break
        yield {
            "id": tweet.id,
            "date": tweet.date.isoformat(),
            "content": tweet.content,
            "likeCount": tweet.likeCount,
            "retweetCount": tweet.retweetCount,
            "url": tweet.url,
        }


def main():
    out_dir = Path('data')
    out_dir.mkdir(exist_ok=True)
    today_str = date.today().isoformat()
    csv_path = out_dir / f'gleisi_selic_{today_str}.csv'

    existing_ids = set()
    if csv_path.exists():
        try:
            df_existing = pd.read_csv(csv_path)
            existing_ids = set(df_existing['id'].astype(str))
        except Exception:
            pass

    new_rows = []
    for row in fetch_tweets():
        if str(row['id']) not in existing_ids:
            new_rows.append(row)

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        mode = 'a' if csv_path.exists() else 'w'
        header = not csv_path.exists()
        df_new.to_csv(csv_path, index=False, mode=mode, header=header)


if __name__ == '__main__':
    main()
