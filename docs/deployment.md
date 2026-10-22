# Free-tier judge deployment preparation

The authorized hosting budget is **free tier only**. Do not create a paid App Service plan as a fallback.

The existing same-origin FastAPI service serves built frontend files. Build frontend normally, then run:

```powershell
backend/.venv/Scripts/python.exe scripts/package_hosting.py --output artifacts/matchlens-hosting.zip
```

The packager exports exact locked production dependencies via uv, packages Python sources and built assets, and rejects credential-like content. It includes no local environment, token, SDK credential cache, database or real match data. Existing output files are not overwritten. This deployment ZIP is different from the source judge handoff.

For an available Azure Linux Free F1 App Service, use Python 3.12, build automation enabled (`SCM_DO_BUILD_DURING_DEPLOYMENT=true`), `MATCHLENS_FRONTEND_DIR=public`, and `MATCHLENS_AI_MODE=template`. Startup command:

```text
python -m uvicorn matchlens.api:app --host 0.0.0.0 --port 8000 --workers 1
```

Public template mode does not expose paid model requests or enable administrator ingestion. No Foundry identity/role is granted merely by deploying the local demo. A future hosted model path needs verified workload identity, appropriate resource-scoped permissions, access limits and current semantic evaluation.

Acceptance: anonymous HTTPS page, correct hashed assets, `/api/health` reporting template mode, match/player/comparison/questions/recap requests working at the selected clock, no environment/config files served, and a useful fallback without Azure credentials. A deployment is not verified until these checks run against the actual public hostname.

Current status: **https://matchlens-chris-demo-2026.azurewebsites.net** is deployed and verified anonymously. North Central US returned zero F1 quota; West US 3 succeeded on the requested F1 plan, returned by Azure as LinuxFree/U13. Deployment completed successfully. Public page, hashed assets, environment rejection, health, state, player, comparison, question and selected-clock recap checks pass; browser question/recap interactions also passed. See hosting-verification.json. No paid hosting tier or public paid-model endpoint was enabled. Free-tier cold starts/quotas remain; no uptime or load-testing claim.

Sources: [Microsoft Python quickstart](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python), [Python runtime/build configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python), [Linux App Service pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/linux/).
