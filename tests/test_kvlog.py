from kvlog import KVStore


def test_put_get_delete(tmp_path):
    with KVStore(str(tmp_path / "db.log")) as db:
        db.put("a", {"x": [1, 2]})
        assert db.get("a") == {"x": [1, 2]} and "a" in db
        assert db.delete("a") and not db.delete("a")
        assert db.get("a", "gone") == "gone" and len(db) == 0


def test_persists_across_reopen(tmp_path):
    path = str(tmp_path / "db.log")
    with KVStore(path) as db:
        db.put("a", 1)
        db.put("b", 2)
        db.put("a", 3)
        db.delete("b")
    with KVStore(path) as db:
        assert db.get("a") == 3 and "b" not in db and list(db.keys()) == ["a"]


def test_torn_trailing_write_is_ignored(tmp_path):
    path = tmp_path / "db.log"
    with KVStore(str(path)) as db:
        db.put("a", 1)
    with open(path, "a") as f:
        f.write('{"k":"b","v":')
    with KVStore(str(path)) as db:
        assert db.get("a") == 1 and "b" not in db


def test_compaction_shrinks_log_and_keeps_data(tmp_path):
    path = tmp_path / "db.log"
    with KVStore(str(path)) as db:
        for i in range(50):
            db.put("k", i)
        db.put("other", "v")
        before = path.stat().st_size
        db.compact()
        assert path.stat().st_size < before
        db.put("after", True)
    with KVStore(str(path)) as db:
        assert db.get("k") == 49 and db.get("other") == "v" and db.get("after") is True
