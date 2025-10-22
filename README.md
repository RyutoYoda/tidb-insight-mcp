# TiDB Insight MCP

TiDBデータベースの分析とパフォーマンス監視のためのカスタムModel Context Protocol (MCP) サーバーです。

## 機能

- **SQLクエリ実行**: 実行時間測定オプション付きで任意のSQLクエリを実行
- **テーブル分析**: サイズ、行数、インデックス統計を含む詳細なテーブル情報を取得
- **データベース統計**: 包括的なデータベース全体のメトリクスと情報
- **クエリベンチマーク**: クエリを複数回実行して平均実行時間とパフォーマンスを測定

## 利用可能なツール

### 1. `execute_sql`
TiDBデータベースでSQLクエリを実行し、オプションでタイミング測定を行います。

**パラメータ:**
- `query` (必須): 実行するSQLクエリ
- `measure_time` (オプション): 実行時間を測定するかどうか

### 2. `get_table_info`
サイズと構造を含むテーブルの詳細情報を取得します。

**パラメータ:**
- `table_name` (オプション): 特定のテーブル名、または空白ですべてのテーブル

### 3. `get_database_stats`
包括的なデータベース統計と接続情報を取得します。

### 4. `benchmark_query`
SQLクエリのパフォーマンスベンチマークを実行します。

**パラメータ:**
- `query` (必須): ベンチマークするSQLクエリ
- `iterations` (オプション): 反復回数（デフォルト: 5、最大: 50）

## インストール

1. このリポジトリをクローン:
```bash
git clone https://github.com/yourusername/tidb-insight-mcp.git
cd tidb-insight-mcp
```

2. 環境変数を設定:
```bash
cp .env.example .env
# .envファイルを編集してTiDBの接続情報を入力
```

3. セットアップスクリプトを実行:
```bash
./setup.sh
```

## 設定

Claude Desktop設定ファイルに以下を追加してください:

```json
{
  "mcpServers": {
    "tidb-insight": {
      "command": "/path/to/tidb-insight-mcp/venv/bin/python",
      "args": ["/path/to/tidb-insight-mcp/server.py"],
      "env": {
        "TIDB_HOST": "your-tidb-host",
        "TIDB_PORT": "4000",
        "TIDB_USERNAME": "your-username",
        "TIDB_PASSWORD": "your-password",
        "TIDB_DATABASE": "your-database"
      }
    }
  }
}
```

## 環境変数

- `TIDB_HOST`: TiDBサーバーのホスト名
- `TIDB_PORT`: TiDBサーバーのポート番号（デフォルト: 4000）
- `TIDB_USERNAME`: データベースユーザー名
- `TIDB_PASSWORD`: データベースパスワード
- `TIDB_DATABASE`: データベース名

## 必要条件

- Python 3.10+
- TiDB CloudまたはセルフホストTiDBインスタンス
- Claude Desktop

## ライセンス

MIT License