# kvlog

A tiny durable key-value store backed by an append-only log with compaction.

## Usage

```python
from kvlog import KVStore

with KVStore("data.log") as db:
    db.put("name", "Ada")
    db.get("name")   # -> "Ada"
    db.delete("name")
```

## Test

```bash
pip install pytest && pytest
```

## License

MIT
