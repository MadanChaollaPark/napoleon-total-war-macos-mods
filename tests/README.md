# Tests

Run the repository-only verification suite with:

```bash
python3 -m unittest discover -s tests -v
```

The tests verify artifact hashes and source row counts, exclude upstream game
and personal backup files, exercise UTF-16LE script merging, and confirm exact
transactional rollback. The compact startpos delta is hash-checked in CI; an
end-to-end startpos application test additionally requires the user's own
checksummed WW0 startpos and is performed outside the public repository.

