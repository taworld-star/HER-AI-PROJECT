import re

# Patch: replace logo emoji spans with logo image tag in all HTML files

NAV_OLD = re.compile(
    r'<a href="index\.html" class="nav-logo">\s*'
    r'<span class="logo-icon">[^<]*</span>\s*'
    r'<span class="logo-text">Siklika</span>\s*'
    r'</a>',
    re.DOTALL
)
NAV_NEW = '<a href="index.html" class="nav-logo">\n                <img src="assets/logo.png" alt="Siklika" class="nav-logo-img" />\n            </a>'

FOOTER_OLD = re.compile(
    r'<div class="footer-brand">\s*'
    r'<span class="logo-icon">[^<]*</span>\s*'
    r'<span class="logo-text">Siklika</span>\s*'
    r'</div>',
    re.DOTALL
)
FOOTER_NEW = '<div class="footer-brand">\n                <img src="assets/logo.png" alt="Siklika" class="footer-logo-img" />\n            </div>'

MOCK_LOGO_OLD = re.compile(
    r'<span class="mock-logo">[^<]*</span>',
)
MOCK_LOGO_NEW = '<img src="assets/logo.png" alt="Siklika" class="mock-logo-img" />'

CHATBOT_AVATAR_OLD = re.compile(
    r'<div class="chatbot-avatar">\s*<span>[^<]*</span>\s*</div>',
    re.DOTALL
)
CHATBOT_AVATAR_NEW = '<div class="chatbot-avatar">\n                        <img src="assets/logo.png" alt="Sika" class="chatbot-avatar-img" />\n                    </div>'

MSG_AVATAR_FLOWER_OLD = re.compile(r'<div class="msg-avatar">[^<]*\U0001f338[^<]*</div>')
MSG_AVATAR_FLOWER_NEW = '<div class="msg-avatar"><img src="assets/logo.png" alt="Sika" class="msg-avatar-img" /></div>'

MSG_AVATAR_SMALL_OLD = re.compile(r'<div class="msg-avatar small">[^<]*\U0001f338[^<]*</div>')
MSG_AVATAR_SMALL_NEW = '<div class="msg-avatar small"><img src="assets/logo.png" alt="Sika" class="msg-avatar-img" /></div>'

files = {
    "frontend/index.html":    [NAV_OLD, FOOTER_OLD, MOCK_LOGO_OLD],
    "frontend/dashboard.html":[NAV_OLD, FOOTER_OLD],
    "frontend/chatbot.html":  [NAV_OLD, CHATBOT_AVATAR_OLD, MSG_AVATAR_FLOWER_OLD, MSG_AVATAR_SMALL_OLD],
    "frontend/riwayat.html":  [NAV_OLD, FOOTER_OLD],
}

replacements = {
    NAV_OLD: NAV_NEW,
    FOOTER_OLD: FOOTER_NEW,
    MOCK_LOGO_OLD: MOCK_LOGO_NEW,
    CHATBOT_AVATAR_OLD: CHATBOT_AVATAR_NEW,
    MSG_AVATAR_FLOWER_OLD: MSG_AVATAR_FLOWER_NEW,
    MSG_AVATAR_SMALL_OLD: MSG_AVATAR_SMALL_NEW,
}

for fpath, patterns in files.items():
    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    original = content
    for pat in patterns:
        new = replacements[pat]
        content, n = pat.subn(new, content)
        print(f"  {fpath}: pattern '{pat.pattern[:40]}...' -> {n} replacement(s)")

    if content != original:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Saved: {fpath}")
    else:
        print(f"  No change: {fpath}")

print("\nDone patching logo.")
