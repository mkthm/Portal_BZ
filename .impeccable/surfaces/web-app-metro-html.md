---
version: 1
slug: "web-app-metro-html"
primary_target: "web_app/metro.html"
related_targets: []
---

Scope: web_app/metro.html, the "Метро связок" screen of the Portal BZ Telegram Mini App. Mode: Operate (find a node, open its materials, plan a route).

Audience and job: reader on a phone in Telegram finds how AI, marketing, business and service topics connect and opens the real materials in one tap. Constraints: dark only, fixed palette and type from METRO_NAVIGATION_DESIGN_SPEC.md, 360–430 px wide, static files on GitHub Pages, data from posts.json.

Chosen direction: pinned by the brief (Harry Beck transit diagram). Stations are real subcategories of the base (user card recommendation), interchanges are the five links named in the spec.

## Direction contract

THESIS: the base is a transit diagram; the map is the navigation, not decoration around a list. Refuses the category default of chips + card feed.
OWN-WORLD: canvas #080C14 with 24 px dot grid; four lines cyan #06B6D4, purple #A855F7, emerald #10B981, amber #F59E0B dashed; white-ringed interchange nodes with concentric line dots; surface #111827 sheets with 1px #1F2937 borders; system SF Pro / Inter stack, tabular counts.
STORY: see all four lines at once, tap a node, read what links there, pull the sheet to read every card, or ask for a route from where you are to where you want to be.
FIRST VIEWPORT: whole map fits the phone with 24 px padding, header with count and actions, floating line filter above a tab bar.
SIGNATURE: tap an interchange, camera glides to it, other lines dim to 15%, ring pings, sheet rises at 40%; route mode runs a moving dash along the path.
RISK: label crowding at 360 px; thin data in some nodes must read as honest, not broken.
