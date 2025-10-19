from __future__ import annotations
import json
import os
import tempfile
from typing import Dict, Any
from temporalio import activity


@activity.defn
async def sitearchitect_generate(site_id: str) -> Dict[str, Any]:
    activity.logger.info("SiteArchitect.generate for %s", site_id)
    return {"sections": ["HeroSplit", "FeaturesGrid", "CTA"], "tokens": {"brand": "Default"}}


@activity.defn
async def copyweb_write_all(site_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info("CopyWeb.write_all for %s (keys=%s)", site_id, list(spec.keys()))
    return {
        "HeroSplit": {
            "title": spec.get("title", "Your Product"),
            "subtitle": spec.get("subtitle", "Do more with less."),
        },
        "FeaturesGrid": {
            "items": [
                {"title": "Fast", "body": "Blazing setup."},
                {"title": "Secure", "body": "Policies enforced."},
                {"title": "Scalable", "body": "From 0→1M users."},
            ]
        },
        "CTA": {"label": "Get Started", "href": "#"},
    }


@activity.defn
async def visualgen_generate(site_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info("VisualGen.generate for %s", site_id)
    return {"HeroSplit": {"img": "/placeholder.svg"}}


@activity.defn
async def webbuilder_materialize(site_id: str, copy: Dict[str, Any], imgs: Dict[str, Any]) -> str:
    activity.logger.info("WebBuilder.materialize for %s", site_id)
    tmp = tempfile.mkdtemp(prefix=f"sitegen-{site_id}-")
    os.makedirs(os.path.join(tmp, "data"), exist_ok=True)
    with open(os.path.join(tmp, "data", "copy.json"), "w", encoding="utf-8") as f:
        json.dump({"copy": copy, "imgs": imgs}, f, indent=2)
    return tmp


@activity.defn
async def qaweb_run_checks(repo_dir: str) -> Dict[str, Any]:
    activity.logger.info("QAWeb.run_checks in %s", repo_dir)
    return {"lighthouse": 95, "a11y": "AA", "links_ok": True}


@activity.defn
async def deploy_preview(repo_dir: str, provider: str, creds: Dict[str, Any]) -> str:
    activity.logger.info("Deploy.preview provider=%s dir=%s", provider, repo_dir)
    return f"https://preview.example.com/{os.path.basename(repo_dir)}"


@activity.defn
async def deploy_promote(preview_url: str, provider: str, creds: Dict[str, Any]) -> str:
    activity.logger.info("Deploy.promote provider=%s preview=%s", provider, preview_url)
    return preview_url.replace("preview", "prod")


@activity.defn
async def reporting_lh_seo_report(prod_url: str) -> Dict[str, Any]:
    activity.logger.info("Reporting.lh_seo_report for %s", prod_url)
    return {"url": prod_url, "lighthouse": {"performance": 95, "seo": 98}}
