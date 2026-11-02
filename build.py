#!/usr/bin/env python3
"""IF PARTNERS HUKUK sitesini src/ altındaki kaynaklardan üretir.

Kullanım:  python3 build.py
Gerekenler: jinja2, markdown, pyyaml

Üretilen dosyalar deponun köküne yazılır (GitHub Pages doğrudan bunları yayınlar):
  index.html, blog.html, blog/<yazı>/index.html, calisma-alanlari/<alan>/index.html,
  kvkk.html, cerez-politikasi.html, 404.html, sitemap.xml
Yeni blog yazısı: src/blog/<adres-adi>.md (başında title, date, category, description).
"""
import datetime, pathlib, re, shutil, time
import yaml, markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
AYLAR = "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split()

site = yaml.safe_load((SRC / "site.yml").read_text(encoding="utf-8"))
env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html"]))
common = dict(site=site, year=datetime.date.today().year, build_id=int(time.time()))


def front(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, text)


def md(text):
    html = markdown.markdown(text, extensions=["extra", "sane_lists"])
    return html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")


def write(rel, html):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def render(tpl, rel, **ctx):
    depth = rel.count("/")
    write(rel, env.get_template(tpl).render(root=("../" * depth) or "./", **common, **ctx))



# hesaplama araçlarının verisi
import json as _json
_v = yaml.safe_load((SRC / "veri" / "araclar.yml").read_text(encoding="utf-8"))
_v["tufe12"] = _json.loads((SRC / "veri" / "tufe12.json").read_text(encoding="utf-8"))
write("assets/araclar-veri.js", "window.ARAC_VERI=" + _json.dumps(_v, ensure_ascii=False, separators=(",", ":")) + ";\n")

# çalışma alanları
alanlar = []
for f in (SRC / "alanlar").glob("*.md"):
    meta, body = front(f)
    meta.update(slug=f.stem, html=md(body))
    alanlar.append(meta)
alanlar.sort(key=lambda a: a.get("order", 99))

# blog yazıları
posts = []
for f in (SRC / "blog").glob("*.md"):
    meta, body = front(f)
    if meta.get("draft"):
        continue
    d = meta["date"] if isinstance(meta["date"], datetime.date) else datetime.date.fromisoformat(str(meta["date"]))
    meta.update(slug=f.stem, html=md(body), date_iso=d.isoformat(), date_tr=f"{d.day} {AYLAR[d.month-1]} {d.year}")
    posts.append(meta)
posts.sort(key=lambda p: p["date_iso"], reverse=True)
categories = sorted({p["category"] for p in posts if p.get("category")})

# eski üretimleri temizle
for d in ("calisma-alanlari", "blog", "araclar"):
    shutil.rmtree(ROOT / d, ignore_errors=True)

render("blog.html", "blog.html", posts=posts, categories=categories, section="blog",
       page_title="Blog", canonical="/blog.html",
       description="IF PARTNERS HUKUK'tan ceza, ticaret, icra-iflas, gayrimenkul, yabancılar, sigorta ve sağlık hukuku alanlarında bilgilendirici yazılar.")
for p in posts:
    render("post.html", f"blog/{p['slug']}/index.html", p=p, section="blog", og_type="article",
           page_title=p["title"], description=p.get("description", ""), canonical=f"/blog/{p['slug']}/")
for a in alanlar:
    render("alan.html", f"calisma-alanlari/{a['slug']}/index.html", a=a, alanlar=alanlar, section="alan",
           page_title=a["title"], description=a.get("description", a["short"]), canonical=f"/calisma-alanlari/{a['slug']}/")

# hesaplama araçları
araclar = [
    dict(slug="kira-artis-hesaplama", title="Kira Artış Hesaplama", tpl="t_kira.html",
         lead="Sözleşmenin başladığı yıl ve aydan itibaren her kira yılının artışını TÜFE 12 aylık ortalamaya ve %25 sınırına göre yıl yıl hesaplayın.",
         desc="Kira yılını ve başlangıç ayını seçin; her yılın artışını TÜFE 12 aylık ortalama ve konutta %25 sınırına göre görün."),
    dict(slug="yasal-faiz-hesaplama", title="Yasal Faiz Hesaplama", tpl="t_faiz.html",
         lead="Birden fazla alacak kalemi için, her kalemin kendi başlangıç tarihinden itibaren işleyen yasal faizi dönem dönem hesaplayın.",
         desc="Alacak kalemlerini ve başlangıç tarihlerini girin; 3095 sayılı Kanun'a göre yasal faizi dönem dönem görün."),
    dict(slug="kidem-ihbar-tazminati-hesaplama", title="Kıdem ve İhbar Tazminatı Hesaplama", tpl="t_kidem.html",
         lead="İşe giriş ve çıkış tarihleri ile brüt ücrete göre kıdem ve ihbar tazminatını, tavan ve kesintilerle birlikte yaklaşık olarak hesaplayın.",
         desc="Giriş-çıkış tarihi ve brüt ücretle kıdem ve ihbar tazminatını tavan ve kesintilerle birlikte görün."),
]
for t in araclar:
    render("arac.html", f"araclar/{t['slug']}/index.html", tool_tpl=t["tpl"], slug=t["slug"], araclar=araclar,
           section="arac", page_title=t["title"], lead=t["lead"], description=t["lead"], canonical=f"/araclar/{t['slug']}/")

render("home.html", "index.html", alanlar=alanlar, posts=posts, araclar=araclar, canonical="/")
render("page.html", "kvkk.html", body=(SRC / "kvkk.html").read_text(encoding="utf-8"),
       page_title="KVKK Aydınlatma Metni", canonical="/kvkk.html")
render("page.html", "cerez-politikasi.html", body=(SRC / "cerez.html").read_text(encoding="utf-8"),
       page_title="Çerez Politikası", canonical="/cerez-politikasi.html")

# 404: her adreste açılabildiği için mutlak yollar kullanır
html404 = env.get_template("page.html").render(
    root=site["base_path"], noindex=True, page_title="Sayfa bulunamadı", **common,
    body=f'''<section class="block tone-stone doc"><div class="wrap narrow prose">
<h1>Aradığınız sayfa bulunamadı</h1>
<p>Sayfa taşınmış ya da kaldırılmış olabilir. Ana sayfadan devam edebilir veya bize doğrudan ulaşabilirsiniz.</p>
<p><a class="btn solid" href="{site["base_path"]}">Ana sayfaya dön</a></p>
</div></section>''')
write("404.html", html404)

urls = ["/", "/blog.html"] + [f"/calisma-alanlari/{a['slug']}/" for a in alanlar] + \
       [f"/blog/{p['slug']}/" for p in posts] + [f"/araclar/{t['slug']}/" for t in araclar] + ["/kvkk.html", "/cerez-politikasi.html"]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f"<url><loc>{site['url']}{u}</loc></url>\n" for u in urls) + "</urlset>\n")

print(f"Tamam: {len(alanlar)} çalışma alanı, {len(posts)} blog yazısı.")
