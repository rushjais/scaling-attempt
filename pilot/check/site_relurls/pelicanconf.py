# Hidden check site: RELATIVE_URLS with directory-style URLs, nesting, and
# cross-links between depths. The visible tests never set RELATIVE_URLS.
AUTHOR = "Pilot"
SITENAME = "Relative URL check"
SITEURL = "https://example.org/blog"
RELATIVE_URLS = True
TIMEZONE = "UTC"
DEFAULT_LANG = "en"
DEFAULT_DATE = (2024, 1, 1)
PATH = "content"
STATIC_PATHS = ["images", "files"]
ARTICLE_URL = "posts/{category}/{slug}/"
ARTICLE_SAVE_AS = "posts/{category}/{slug}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"
CATEGORY_URL = "c/{slug}/"
CATEGORY_SAVE_AS = "c/{slug}/index.html"
USE_FOLDER_AS_CATEGORY = True
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
