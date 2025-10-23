# Docker Compose (app + streamlit + nginx)

Bring up the app stack for local testing (builds streamlit and backend images):

```bash
docker compose -f docker-compose.app.yml up -d --build
docker compose -f docker-compose.app.yml ps
```

Create basic auth file for nginx before starting:

```bash
mkdir -p ops
docker run --rm --entrypoint htpasswd httpd:2 -Bbn admin "your-strong-pass" > ops/.htpasswd
```

Then open http://localhost:8080 and login with admin/your-strong-pass.
