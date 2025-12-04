# Contributing to DocTree.AI

Thanks for your interest in contributing! A few guidelines to make contributions smooth:

1. Reporting issues
- Use GitHub Issues to report bugs or request features. Provide steps to reproduce and a small sample PDF if possible.

2. Code style
- Python: follow PEP8. Use black/isort if you run formatters locally.
- JavaScript/TypeScript: follow the existing project conventions (Prettier / ESLint if present).

3. Running tests
- Run Python tests locally with:
```powershell
pytest -q
```

4. Making changes
- Create a topic branch from `main` (e.g., `feat/upload-s3` or `fix/upload-size`)
- Add tests for bug fixes / new features where practical
- Open a Pull Request with a clear description and link to relevant issues

5. CI and checks
- Keep changes small and focused. The repository includes CI workflows that run tests and frontend build on PRs.

6. Code of Conduct
- Be respectful and constructive in reviews and discussion.
