import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: "https://persnally.com/sitemap.xml",
    host: "https://persnally.com",
  };
}
