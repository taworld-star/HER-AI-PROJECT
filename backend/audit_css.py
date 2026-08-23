import re

with open("frontend/style.css", encoding="utf-8") as f:
    css = f.read()

defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))

html_classes = set()
for fname in ["index.html", "dashboard.html", "chatbot.html", "riwayat.html"]:
    with open(f"frontend/{fname}", encoding="utf-8") as f:
        for m in re.findall(r'class="([\w\s-]+)"', f.read()):
            for cls in m.split():
                html_classes.add(cls)

js_classes = set()
for fname in ["app.js", "dashboard.js", "chatbot.js", "riwayat.js"]:
    with open(f"frontend/{fname}", encoding="utf-8") as f:
        content = f.read()
    for _, cls in re.findall(r'classList\.(add|remove|toggle)\("([\w-]+)"\)', content):
        js_classes.add(cls)
    for m in re.findall(r'className\s*=\s*"([\w\s-]+)"', content):
        for cls in m.split():
            js_classes.add(cls)

all_used = html_classes | js_classes
missing = {c for c in all_used if c not in defined and len(c) > 2}

# Ignore utility-like patterns that are set inline or from libraries
ignore = {"active", "open", "scrolled", "spin", "has-data", "today", "empty",
          "stable", "irregular", "warning", "error-bubble", "msg-source", "user-avatar"}
missing -= ignore

print("Undefined CSS classes referenced in HTML/JS:")
if missing:
    for c in sorted(missing):
        print(f"  MISSING: .{c}")
else:
    print("  None found - all clear")

print()
print(f"Total CSS classes defined : {len(defined)}")
print(f"Used in HTML              : {len(html_classes)}")
print(f"Used in JS (classList)    : {len(js_classes)}")
print(f"Needs CSS styles (missing): {len(missing)}")
