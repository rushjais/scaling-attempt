# Contract-check config: content cache on (for incremental builds), a theme
# override that does string ops on path values, fixed dates.
AUTHOR = "Pilot"
SITENAME = "Contract check"
SITEURL = "https://example.org"
TIMEZONE = "UTC"
DEFAULT_DATE = (2024, 1, 1)
PATH = "content"
STATIC_PATHS = ["images", "files"]
ARTICLE_URL = "posts/{category}/{slug}/"
ARTICLE_SAVE_AS = "posts/{category}/{slug}/index.html"
USE_FOLDER_AS_CATEGORY = True
CACHE_CONTENT = True
LOAD_CONTENT_CACHE = True
CACHE_PATH = "cache"
THEME_TEMPLATES_OVERRIDES = ["/check/contracts/theme_overrides"]
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
