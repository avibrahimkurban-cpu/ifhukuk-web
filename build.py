#!/usr/bin/env python3
"""IF PARTNERS HUKUK sitesini src/ altındaki kaynaklardan üretir.

Kullanım:  python3 build.py
Gerekenler: jinja2, markdown, pyyaml

Üretilen dosyalar deponun köküne yazılır (GitHub Pages doğrudan bunları yayınlar):
  index.html, blog.html, blog/<yazı>/index.html, calisma-alanlari/<alan>/index.html,
  kvkk.html, cerez-politikasi.html, 404.html, sitemap.xml
Yeni yayın: src/yayinlar/<adres-adi>.md (başında title, date, category, description).
"""
import datetime, pathlib, re, shutil, time
import yaml, markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
AYLAR = "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split()

site = yaml.safe_load((SRC / "site.yml").read_text(encoding="utf-8"))
env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html"]))
import os
TEMALAR = yaml.safe_load((SRC / "temalar.yml").read_text(encoding="utf-8"))
theme = TEMALAR.get(int(os.environ["TEMA"])) if os.environ.get("TEMA") else None
common = dict(site=site, theme=theme, year=datetime.date.today().year, build_id=int(time.time()))


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


def redirect(rel, target):
    write(rel, f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Yönlendiriliyor… | IF PARTNERS HUKUK</title><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={target}"><script>location.replace("{target}")</script></head><body><p><a href="{target}">IF PARTNERS HUKUK</a></p></body></html>\n')


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
for f in (SRC / "yayinlar").glob("*.md"):
    meta, body = front(f)
    if meta.get("draft"):
        continue
    d = meta["date"] if isinstance(meta["date"], datetime.date) else datetime.date.fromisoformat(str(meta["date"]))
    meta.update(slug=f.stem, html=md(body), date_iso=d.isoformat(), date_tr=f"{d.day} {AYLAR[d.month-1]} {d.year}")
    posts.append(meta)
posts.sort(key=lambda p: p["date_iso"], reverse=True)
categories = sorted({p["category"] for p in posts if p.get("category")})
alan_by = {a["slug"]: a for a in alanlar}

# ekip
ekip = []
for f in (SRC / "ekip").glob("*.md"):
    meta, body = front(f)
    words = [w for w in meta["name"].replace("Stj.", "").replace("Av.", "").split() if w]
    meta.update(slug=f.stem, html=md(body), initials=(words[0][0] + words[-1][0]).upper(),
                area_objs=[alan_by[s] for s in meta.get("areas", []) if s in alan_by])
    ekip.append(meta)
ekip.sort(key=lambda p: p.get("order", 99))

# sektörler
sektorler = []
for f in (SRC / "sektorler").glob("*.md"):
    meta, body = front(f)
    meta.update(slug=f.stem, html=md(body), area_objs=[alan_by[s] for s in meta.get("areas", []) if s in alan_by])
    sektorler.append(meta)
sektorler.sort(key=lambda s: s.get("order", 99))

beklentiler = [
    ("Dosyanıza bir avukat sahip çıkar", "Dosyanız, ilk görüşmeden sonuçlanana kadar büromuzun avukatlarından biri tarafından birebir takip edilir."),
    ("Süreler ayrı ayrı izlenir", "Kanuni süreler, duruşma ve keşif tarihleri büro içindeki takip sistemimize işlenir ve sorumlu avukata önceden hatırlatılır."),
    ("Her gelişmeyi yazılı olarak öğrenirsiniz", "Duruşma, tebligat, bilirkişi raporu ve karar gibi önemli gelişmeleri size yazılı olarak iletiriz."),
    ("Kapsam ve ücret baştan bellidir", "Yapılacak işin kapsamı, ücret ve masraflar avukatlık sözleşmesiyle açıkça belirlenir."),
    ("Kendi dilinizde görüşürsünüz", "Türkçe ve İngilizcenin yanı sıra Uygurca ve Özbekçe görüşme yapabiliyoruz."),
]
common["nav_alanlar"] = alanlar

# eski üretimleri temizle
for d in ("calisma-alanlari", "blog", "araclar", "yayinlar", "ekibimiz", "sektorler", "hakkimizda", "iletisim"):
    shutil.rmtree(ROOT / d, ignore_errors=True)

render("yayin_list.html", "yayinlar/index.html", posts=posts, categories=categories, section="yayin",
       page_title="Yayınlar", canonical="/yayinlar/",
       description="IF PARTNERS HUKUK'tan ceza, ticaret, icra-iflas, gayrimenkul, yabancılar, sigorta ve sağlık hukuku alanlarında bilgilendirici yayınlar.")
for p in posts:
    render("yayin.html", f"yayinlar/{p['slug']}/index.html", p=p, section="yayin", og_type="article",
           page_title=p["title"], description=p.get("description", ""), canonical=f"/yayinlar/{p['slug']}/")
    # eski blog adresinden yönlendirme
    redirect(f"blog/{p['slug']}/index.html", f"../../yayinlar/{p['slug']}/")
redirect("blog.html", "yayinlar/")
render("alan_list.html", "calisma-alanlari/index.html", alanlar=alanlar, section="alan",
       page_title="Çalışma Alanları", canonical="/calisma-alanlari/")
render("ekip_list.html", "ekibimiz/index.html", ekip=ekip, section="ekip", page_title="Ekibimiz", canonical="/ekibimiz/",
       description="IF PARTNERS HUKUK ortakları ve ekibi.")
for p in ekip:
    render("ekip.html", f"ekibimiz/{p['slug']}/index.html", p=p, ekip=ekip, section="ekip",
           page_title=p["name"], description=f"{p['name']}, {p['role']}. {p['summary']}", canonical=f"/ekibimiz/{p['slug']}/")
render("sektor_list.html", "sektorler/index.html", sektorler=sektorler, section="sektor", page_title="Sektörler", canonical="/sektorler/",
       description="IF PARTNERS HUKUK'un birlikte çalıştığı sektörler: yabancılar ve yabancı yatırımcılar, hizmet sektörü, teknoloji şirketleri, sağlık kuruluşları.")
for s in sektorler:
    render("sektor.html", f"sektorler/{s['slug']}/index.html", s=s, sektorler=sektorler, section="sektor",
           page_title=s["title"], description=s.get("description", s["short"]), canonical=f"/sektorler/{s['slug']}/")
render("hakkimizda.html", "hakkimizda/index.html", ekip=ekip, beklentiler=beklentiler, section="hakkimizda",
       page_title="Hakkımızda", canonical="/hakkimizda/")
render("iletisim.html", "iletisim/index.html", section="iletisim", page_title="İletişim", canonical="/iletisim/",
       description="IF PARTNERS HUKUK iletişim bilgileri: Uzunçayır Cad. No:43 D1 Blok D:26 Kadıköy/İstanbul, +90 538 040 82 72, info@ifhukuk.com.")
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

render("arac_list.html", "araclar/index.html", araclar=araclar, section="arac", page_title="Hesaplama Araçları", canonical="/araclar/")
render("home.html", "index.html", alanlar=alanlar, posts=posts, araclar=araclar, ekip=ekip, sektorler=sektorler, beklentiler=beklentiler, canonical="/")
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

urls = ["/", "/hakkimizda/", "/calisma-alanlari/", "/sektorler/", "/ekibimiz/", "/yayinlar/", "/araclar/", "/iletisim/"] + \
       [f"/calisma-alanlari/{a['slug']}/" for a in alanlar] + [f"/sektorler/{s['slug']}/" for s in sektorler] + \
       [f"/ekibimiz/{p['slug']}/" for p in ekip] + [f"/yayinlar/{p['slug']}/" for p in posts] + \
       [f"/araclar/{t['slug']}/" for t in araclar] + ["/kvkk.html", "/cerez-politikasi.html"]
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + "".join(f"<url><loc>{site['url']}{u}</loc></url>\n" for u in urls) + "</urlset>\n")

print(f"Tamam: {len(alanlar)} çalışma alanı, {len(sektorler)} sektör, {len(ekip)} kişi, {len(posts)} yayın.")
