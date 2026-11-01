OPTIONAL: offline copy of Chart.js
-----------------------------------
ProcessX loads Chart.js from the internet (jsDelivr CDN). If you need to demo without internet:

1. While online, open this address and save the page as "chart.umd.min.js" in THIS folder:
   https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js
2. Reload ProcessX. It uses this local copy whenever the CDN cannot be reached.

Without either, the Compare screen still works and draws simple bar charts instead.
