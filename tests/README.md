# Tests

Run the repository-only verification suite with:

```bash
python3 -m unittest discover -s tests -v
```

The tests verify artifact hashes, source row counts, the deterministic
university-pack rebuild, UTF-16LE script merging, exact transactional rollback,
and refusal to overwrite unknown packs. They also exclude upstream game files
and personal backups. The compact startpos delta is hash-checked in CI; an
end-to-end startpos application test additionally requires the user's own
checksummed WW0 startpos and is performed outside the public repository.
