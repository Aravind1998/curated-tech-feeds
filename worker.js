import html from "./index.html";
import opml from "./feeds.opml";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    if (url.pathname === "/feeds.opml") {
      return new Response(opml, {
        headers: {
          "content-type": "application/xml; charset=utf-8",
          "cache-control": "public, max-age=86400",
        },
      });
    }

    return new Response(html, {
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "public, max-age=3600",
        "x-frame-options": "SAMEORIGIN",
        "x-content-type-options": "nosniff",
      },
    });
  },
};
