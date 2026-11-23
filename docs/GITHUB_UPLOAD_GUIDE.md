# GitHub upload guide (Windows / VS Code)

## 1. Create an empty repository on GitHub
Suggested repository name: `NetWatch-Agentic-AI`.
Choose **Public** only if the team is comfortable making source and documentation visible to everyone; otherwise choose **Private**. Do not initialise with a README, .gitignore or license because those files already exist in this project.

## 2. Open the extracted `NetWatch` folder in VS Code
Open Terminal → New Terminal. Confirm the terminal is at the folder containing `app.py`, `agents/`, `data/` and `requirements.txt`.

## 3. Check that secrets and local runtime files are excluded
```powershell
git status --short
git check-ignore .env data/netwatch.db .venv
```
If `.env` was ever committed previously, deleting it locally is not enough; rotate the Gemini API key and remove it from Git history.

## 4. Initialise and push
Replace `<YOUR-GITHUB-USERNAME>` and `<REPOSITORY-NAME>` with the values from the newly created GitHub repository.

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Initial release: NetWatch 2.0 multi-agent support platform"
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/<REPOSITORY-NAME>.git
git push -u origin main
```

If Git reports that `origin` already exists:
```powershell
git remote set-url origin https://github.com/<YOUR-GITHUB-USERNAME>/<REPOSITORY-NAME>.git
```

If Git asks for authentication, complete the browser sign-in flow or use Git Credential Manager. Do not paste a personal access token into chat or commit it to the repository.

## 5. Verify on GitHub
Check that the repository contains `agents/`, `data/generator.py`, `llm/`, `memory/`, `tools/`, `tests/`, `docs/`, `README.md`, `requirements.txt` and `.env.example`.
Check that `.env`, `.venv/` and `data/netwatch.db` are absent.
