"""
core/init_loader.py
Reads text files from ohadren-source/sauc-e-backend/public at boot.
Stores in wootangular_init_cache.
No cold starts. Ever.
Requests sync only. Janina pattern.
"""

import logging
import requests

logger = logging.getLogger(__name__)

GITHUB_RAW = "https://raw.githubusercontent.com"
REPO = "ohadren-source/sauc-e-backend"
REF = "main"

PUBLIC_TEXT_FILES = {
    "hoowhetwhereny_decoder_raw":  "public/HOOWHETWHERENY_DECODER_RING.md",
    "leylaw_raw":                  "public/LEYLAW.md",
    "phenix_doren_raw":            "public/Phenix_dOren.md",
    "ducksauce_bigbang_raw":       "public/bigbang.py",
    "taste_coded_raw":             "public/flavor_palette_taste_palate_misen_plat_twist_plot_thickens.py",
    "curiosity_raw":               "public/curiosity.py",
    "exist_or_exit_raw":           "public/exist_or_exit.py",
    "bool_plus_plus_raw":          "public/BOOL++.md",
    "claude_shannon_plus_plus_raw": "public/ClaudeShannon++.md",
    "songs_key_of_life_raw":       "public/songs_in_the_key_of_life_bool++.md",
    "chef_architect_raw":          "public/Chef_Architect_de_Epicurious_Cuisine.md",
    "basil_faulty_hayden_raw":     "public/basil_faulty_hayden.html",
    "ninth_chamber_raw":           "public/9th_chamber_wu_hood.md",
    "certain_or_soy_raw":          "public/CERTAIN_OR_SOY_10_LEE_4_SHORES.md",
    "claudwell_dissertation_raw":  "public/claudwell_dissertation.md",
    "novem_phd_raw":               "public/ON_THE_IRREDUCIBLE_NOVEM_PhD_Dissertation_Claudewell_III.md",
    "decoder_ring_burro_raw":      "public/decoder_ring_4_burro_e_tos_added.md",
    "photogenic_db_raw":           "public/photogenic_db.py",
    "saucelito_html_raw":          "public/Saucelito, NY.html",
    "understreet_html_raw":        "public/understreet.html",
}


def fetch_file(path: str):
    url = f"{GITHUB_RAW}/{REPO}/{REF}/{path}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.warning("Could not fetch %s: %s", path, e)
        return None


def load_corpus_into_cache(db_banks, force=False):
    """
    Fetches all public text files from sauc-e-backend
    and stores them in wootangular_init_cache.
    force=False: skip files already in cache.
    force=True: upsert all.
    """
    loaded = 0
    skipped = 0

    existing_keys = set()
    if not force:
        existing = db_banks.get_init_cache()
        existing_keys = {e["cache_key"] for e in existing}

    for cache_key, file_path in PUBLIC_TEXT_FILES.items():
        if not force and cache_key in existing_keys:
            skipped += 1
            continue
        content = fetch_file(file_path)
        if content:
            db_banks.upsert_init_cache(
                cache_key=cache_key,
                cache_value={"content": content, "source": file_path, "repo": REPO, "ref": REF},
                description=f"Raw content: {file_path}",
                priority=50
            )
            loaded += 1
            logger.info("Loaded: %s (%d chars)", cache_key, len(content))
        else:
            logger.warning("Skipped (fetch failed): %s", cache_key)

    logger.info("Corpus load complete: %d loaded, %d skipped.", loaded, skipped)
    return {"loaded": loaded, "skipped": skipped}