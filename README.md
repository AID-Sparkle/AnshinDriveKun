# あんしんどらいぶくん 🚗

運転時の状況（時間帯・年齢・車種・天候）と  
現在地周辺の交通事故データをもとに、  
運転リスクを可視化する Web アプリです。

Flask を用いたシンプルな構成で、スマートフォンからの利用も想定しています。

---

## 主な機能

- 質問フォームによる運転状況の入力
- ブラウザの位置情報 API を用いた現在地取得
- Google Maps API による地図表示
- 緯度・経度を事故データ（CSV）形式に変換
- 現在地周辺の交通事故地点を地図上に表示（予定）

---

## 使用技術

- フロントエンド  
  - HTML / CSS / JavaScript
  - Google Maps JavaScript API

- バックエンド  
  - Python / Flask

- データ  
  - 出典：警察庁 「交通事故統計情報のオープンデータ」(2024年6月)
  - https://www.npa.go.jp/publications/statistics/koutsuu/opendata/index_opendata.html

- インフラ  
  - Render（デプロイ予定）

---

