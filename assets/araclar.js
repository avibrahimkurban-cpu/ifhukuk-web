/* IF PARTNERS HUKUK — hesaplama araçları (kira artışı, yasal faiz, kıdem ve ihbar).
   Veriler: assets/araclar-veri.js (window.ARAC_VERI). Tüm sonuçlar örnek niteliğindedir. */
(function () {
  var V = window.ARAC_VERI || {};
  var AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
  var tl = new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY", minimumFractionDigits: 2, maximumFractionDigits: 2 });
  var pct = function (x) { return "%" + x.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };
  var $ = function (id) { return document.getElementById(id); };

  function num(v) {
    v = String(v == null ? "" : v).trim().replace(/\s|₺|TL/gi, "");
    if (!v) return NaN;
    if (v.indexOf(",") > -1) v = v.replace(/\./g, "").replace(",", ".");
    else if (/^\d{1,3}(\.\d{3})+$/.test(v)) v = v.replace(/\./g, "");
    var n = parseFloat(v);
    return isFinite(n) ? n : NaN;
  }
  function d(s) { var p = String(s).split("-"); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
  function iso(dt) { return dt.toISOString().slice(0, 10); }
  function trDate(dt) { return dt.getUTCDate() + " " + AYLAR[dt.getUTCMonth()] + " " + dt.getUTCFullYear(); }
  function days(a, b) { return Math.round((b - a) / 864e5); }
  function addYears(dt, n) {
    var y = dt.getUTCFullYear() + n, m = dt.getUTCMonth(), day = dt.getUTCDate();
    var last = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    return new Date(Date.UTC(y, m, Math.min(day, last)));
  }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (k === "class") e.className = attrs[k]; else e.setAttribute(k, attrs[k]); }
    if (text != null) e.textContent = text;
    return e;
  }
  function row(cells, th) {
    var tr = el("tr");
    cells.forEach(function (c) {
      var td = el(th ? "th" : "td");
      if (c && c.nodeType) td.appendChild(c); else td.textContent = c;
      tr.appendChild(td);
    });
    return tr;
  }
  function msg(box, text) { box.innerHTML = ""; box.appendChild(el("p", { class: "tool-msg" }, text)); }
  function summary(box, items) {
    var s = el("dl", { class: "tool-sum" });
    items.forEach(function (it) {
      var dv = el("div", it[2] ? { class: "hl" } : null);
      dv.appendChild(el("dt", null, it[0])); dv.appendChild(el("dd", null, it[1])); s.appendChild(dv);
    });
    box.appendChild(s);
  }
  function table(box, head, rows, foot) {
    var w = el("div", { class: "tool-table" }), t = el("table"), th = el("thead"), tb = el("tbody");
    th.appendChild(row(head, true)); rows.forEach(function (r) { tb.appendChild(row(r)); });
    t.appendChild(th); t.appendChild(tb);
    if (foot) { var tf = el("tfoot"); tf.appendChild(row(foot)); t.appendChild(tf); }
    w.appendChild(t); box.appendChild(w);
  }
  function onAll(ids, fn) { ids.forEach(function (id) { var x = $(id); if (x) { x.addEventListener("input", fn); x.addEventListener("change", fn); } }); }

  /* ---------------- Kira artışı ---------------- */
  function kira() {
    var box = $("kSonuc"); if (!box) return;
    var T = V.tufe12 || {}, keys = Object.keys(T).sort();
    var first = keys[0], last = keys[keys.length - 1];
    var y = +$("kYil").value, m = +$("kAy").value, g = Math.max(1, Math.min(31, +$("kGun").value || 1));
    var bedel = num($("kBedel").value), tur = $("kTur").value;
    var hy = +$("kHedefYil").value, hm = +$("kHedefAy").value;
    if (!(bedel > 0)) return msg(box, "Başlangıç kira bedelini girin.");
    var start = new Date(Date.UTC(y, m - 1, Math.min(g, new Date(Date.UTC(y, m, 0)).getUTCDate())));
    var target = new Date(Date.UTC(hy, hm, 0));
    if (target <= start) return msg(box, "Hesaplanacak dönem, sözleşme başlangıcından sonra olmalı.");
    var rows = [], cur = bedel, k = 1, stop = "";
    var capS = d("2022-06-11"), capE = d("2024-07-01");
    while (true) {
      var ren = addYears(start, k);
      if (ren > target) break;
      var dm = new Date(Date.UTC(ren.getUTCFullYear(), ren.getUTCMonth() - 1, 1));
      var key = dm.getUTCFullYear() + "-" + String(dm.getUTCMonth() + 1).padStart(2, "0");
      if (!(key in T)) {
        stop = key < first
          ? "Bu araç, TÜFE 12 aylık ortalama verisinin bulunduğu " + AYLAR[+first.slice(5) - 1] + " " + first.slice(0, 4) + " sonrasındaki yenilemeleri hesaplar."
          : AYLAR[dm.getUTCMonth()] + " " + dm.getUTCFullYear() + " oranı henüz açıklanmadı; hesaplama " + trDate(ren) + " öncesindeki son kira yılında durdu.";
        break;
      }
      var r = T[key], used = r, notes = [];
      if (tur === "konut" && ren >= capS && ren <= capE && r > 25) { used = 25; notes.push("Konutta %25 sınırı uygulandı (TÜFE " + pct(r) + ")."); }
      if (ren < d("2012-07-01")) notes.push("TBK yürürlüğünden önce: yasal üst sınır yoktu, bilgi amaçlıdır.");
      else if (tur === "isyeri" && ren < d("2020-07-01")) notes.push("Tacir kiracılar için TBK 344 bu tarihte uygulanmıyordu; sözleşme hükmüne bakılmalı.");
      if (k > 5) notes.push("Beş yılı aşan kira ilişkisi: bedel kira tespit davasıyla hakkaniyete göre belirlenebilir.");
      var art = cur * used / 100, yeni = cur + art;
      rows.push([String(k) + ". yenileme · " + trDate(ren), AYLAR[dm.getUTCMonth()] + " " + dm.getUTCFullYear(), pct(used), tl.format(cur), tl.format(art), tl.format(yeni), notes.join(" ")]);
      cur = yeni; k++;
      if (k > 60) break;
    }
    box.innerHTML = "";
    if (!rows.length) { msg(box, stop || "Seçilen dönemde henüz kira yılı yenilenmemiş; kira bedeli değişmez."); return; }
    summary(box, [
      ["Başlangıç kira bedeli", tl.format(bedel)],
      ["Yenileme sayısı", String(rows.length)],
      ["Güncel kira bedeli (en fazla)", tl.format(cur), true]
    ]);
    table(box, ["Kira yılı", "Uygulanan veri ayı", "Oran", "Önceki kira", "Artış", "Yeni kira", "Açıklama"], rows);
    if (stop) box.appendChild(el("p", { class: "tool-msg" }, stop));
  }

  /* ---------------- Yasal faiz ---------------- */
  function rateSegments(a, b, table) {
    var ks = Object.keys(table).sort(), segs = [];
    for (var i = 0; i < ks.length; i++) {
      var s = d(ks[i]), e = i + 1 < ks.length ? d(ks[i + 1]) : null;
      var from = s > a ? s : a, to = e && e < b ? e : b;
      if (to > from) segs.push({ from: from, to: to, rate: table[ks[i]] });
    }
    return segs;
  }
  function faiz() {
    var box = $("fSonuc"); if (!box) return;
    var Y = V.yasal_faiz || {}, end = $("fBitis").value ? d($("fBitis").value) : null;
    var minD = d(Object.keys(Y).sort()[0]);
    if (!end) return msg(box, "Faizin hesaplanacağı son tarihi girin.");
    var items = [].slice.call(document.querySelectorAll("#fKalemler .kalem")), rows = [], totA = 0, totF = 0, err = "";
    items.forEach(function (it, i) {
      var ad = it.querySelector(".k-ad").value.trim() || ("Kalem " + (i + 1));
      var tut = num(it.querySelector(".k-tutar").value), bas = it.querySelector(".k-tarih").value;
      if (!(tut > 0) || !bas) return;
      var a = d(bas);
      if (a < minD) { err = "Yasal faiz oranları " + trDate(minD) + " tarihinden itibaren tanımlıdır; daha eski başlangıç tarihleri için hesaplama yapılmadı."; return; }
      if (end <= a) { rows.push([ad, tl.format(tut), trDate(a), "—", "Bitiş tarihi başlangıçtan sonra olmalı", tl.format(0)]); totA += tut; return; }
      var segs = rateSegments(a, end, Y), f = 0, parts = [];
      segs.forEach(function (s) {
        var g = days(s.from, s.to), x = tut * s.rate / 100 * g / 365; f += x;
        parts.push(trDate(s.from) + " → " + trDate(s.to) + ": " + g + " gün × %" + s.rate + " = " + tl.format(x));
      });
      totA += tut; totF += f;
      rows.push([ad, tl.format(tut), trDate(a), String(days(a, end)) + " gün", parts.join("\n"), tl.format(f)]);
    });
    box.innerHTML = "";
    if (!rows.length) { msg(box, err || "En az bir alacak kalemi için tutar ve başlangıç tarihi girin."); return; }
    summary(box, [["Toplam asıl alacak", tl.format(totA)], ["Toplam yasal faiz", tl.format(totF)], ["Asıl alacak + faiz", tl.format(totA + totF), true]]);
    table(box, ["Kalem", "Tutar", "Faiz başlangıcı", "Süre", "Dönemlere göre faiz", "Faiz"], rows, ["Toplam", tl.format(totA), "", "", "", tl.format(totF)]);
    if (err) box.appendChild(el("p", { class: "tool-msg" }, err));
  }
  function addKalem(ad, tutar, tarih) {
    var box = $("fKalemler"); if (!box) return;
    var n = box.querySelectorAll(".kalem").length + 1, w = el("div", { class: "kalem" });
    w.innerHTML = '<div class="f"><label>Alacak kalemi</label><input class="k-ad" placeholder="Örn. Fatura alacağı"></div>' +
      '<div class="f"><label>Tutar (TL)</label><input class="k-tutar" inputmode="decimal" placeholder="0,00"></div>' +
      '<div class="f"><label>Faiz başlangıç tarihi</label><input class="k-tarih" type="date"></div>' +
      '<button type="button" class="k-sil" aria-label="Kalemi sil">Sil</button>';
    var ins = w.querySelectorAll("input"), lbs = w.querySelectorAll("label");
    ins.forEach(function (inp, i) { inp.id = "kalem" + n + "-" + i; lbs[i].setAttribute("for", inp.id); inp.addEventListener("input", faiz); inp.addEventListener("change", faiz); });
    if (ad) ins[0].value = ad; if (tutar) ins[1].value = tutar; if (tarih) ins[2].value = tarih;
    w.querySelector(".k-sil").addEventListener("click", function () { w.remove(); faiz(); });
    box.appendChild(w);
  }

  /* ---------------- Kıdem ve ihbar ---------------- */
  function tavanAt(dt) {
    var T = V.kidem_tavan || {}, ks = Object.keys(T).sort(), v = null, k0 = null;
    ks.forEach(function (k) { if (d(k) <= dt) { v = T[k]; k0 = k; } });
    return v == null ? null : { v: v, from: k0 };
  }
  function kidem() {
    var box = $("kdSonuc"); if (!box) return;
    if (!$("kdGiris").value || !$("kdCikis").value) return msg(box, "İşe giriş ve işten çıkış tarihlerini girin.");
    var a = d($("kdGiris").value), b = d($("kdCikis").value);
    var ucret = num($("kdUcret").value), ek = num($("kdEk").value) || 0, vergi = num($("kdVergi").value) || 0;
    var kHak = $("kdKidemHak").checked, iHak = $("kdIhbarHak").checked;
    if (!(b > a)) return msg(box, "Çıkış tarihi giriş tarihinden sonra olmalı.");
    if (!(ucret > 0)) return msg(box, "Son brüt aylık ücreti girin.");
    var gun = days(a, b) + 1, yil = Math.floor(gun / 365), kalan = gun - yil * 365, ay = Math.floor(kalan / 30), g = kalan - ay * 30;
    var giydirilmis = ucret + ek, dv = (V.damga_vergisi || 0) / 100, rows = [], net = 0;
    box.innerHTML = "";
    var sumItems = [["Hizmet süresi", yil + " yıl " + ay + " ay " + g + " gün (" + gun + " gün)"], ["Giydirilmiş brüt aylık ücret", tl.format(giydirilmis)]];
    if (kHak) {
      if (gun < 365) rows.push(["Kıdem tazminatı", "Hizmet süresi bir yıldan az; kıdem tazminatı hakkı doğmaz.", "—", "—", "—"]);
      else {
        var t = tavanAt(b), esas = giydirilmis, not = "";
        if (!t) not = "Çıkış tarihi için tavan verisi yok.";
        else if (giydirilmis > t.v) { esas = t.v; not = "Tavan uygulandı (" + tl.format(t.v) + ")."; }
        var brut = esas * gun / 365, damga = brut * dv, kNet = brut - damga; net += kNet;
        rows.push(["Kıdem tazminatı", tl.format(esas) + " × " + gun + " gün / 365. " + not, tl.format(brut), "Damga vergisi " + tl.format(damga), tl.format(kNet)]);
      }
    }
    if (iHak) {
      var hafta = gun < 183 ? 2 : gun < 548 ? 4 : gun < 1095 ? 6 : 8;
      var iBrut = giydirilmis / 30 * hafta * 7, gv = iBrut * vergi / 100, idv = iBrut * dv, iNet = iBrut - gv - idv; net += iNet;
      rows.push(["İhbar tazminatı", hafta + " hafta (" + hafta * 7 + " gün) × günlük brüt " + tl.format(giydirilmis / 30), tl.format(iBrut), "Gelir vergisi %" + vergi + " " + tl.format(gv) + " · Damga vergisi " + tl.format(idv), tl.format(iNet)]);
    }
    if (!rows.length) return msg(box, "Hesaplamak istediğiniz tazminatı seçin.");
    sumItems.push(["Toplam net (yaklaşık)", tl.format(net), true]);
    summary(box, sumItems);
    table(box, ["Kalem", "Hesap", "Brüt", "Kesintiler", "Net"], rows);
  }

  function fill(sel, from, to, val, labels) {
    var s = $(sel); if (!s) return;
    for (var i = from; i <= to; i++) { var o = el("option", { value: String(i) }, labels ? labels[i - 1] : String(i)); if (i === val) o.selected = true; s.appendChild(o); }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var today = new Date(), ty = today.getFullYear();
    if ($("kSonuc")) {
      var T = V.tufe12 || {}, ks = Object.keys(T).sort(), firstY = +ks[0].slice(0, 4) - 0;
      fill("kYil", firstY, ty, 2021); fill("kAy", 1, 12, 3, AYLAR); fill("kHedefYil", firstY + 1, ty, ty); fill("kHedefAy", 1, 12, today.getMonth() + 1, AYLAR);
      var lk = ks[ks.length - 1]; $("kSonVeri").textContent = AYLAR[+lk.slice(5) - 1] + " " + lk.slice(0, 4);
      onAll(["kYil", "kAy", "kGun", "kBedel", "kTur", "kHedefYil", "kHedefAy"], kira); kira();
    }
    if ($("fSonuc")) {
      $("fBitis").value = today.toISOString().slice(0, 10);
      addKalem("", "", ""); onAll(["fBitis"], faiz);
      $("fEkle").addEventListener("click", function () { addKalem(); });
      var rt = $("fOranlar"), Y = V.yasal_faiz || {}, yk = Object.keys(Y).sort();
      yk.forEach(function (k, i) { var e = i + 1 < yk.length ? trDate(new Date(d(yk[i + 1]) - 864e5)) : "günümüz"; rt.appendChild(row([trDate(d(k)) + " – " + e, "%" + Y[k]])); });
      faiz();
    }
    if ($("kdSonuc")) {
      onAll(["kdGiris", "kdCikis", "kdUcret", "kdEk", "kdVergi", "kdKidemHak", "kdIhbarHak"], kidem);
      var tv = $("kdTavanlar"), KT = V.kidem_tavan || {}, kk = Object.keys(KT).sort().reverse().slice(0, 6);
      kk.forEach(function (k) { tv.appendChild(row([trDate(d(k)), tl.format(KT[k])])); });
      kidem();
    }
    document.querySelectorAll("form.tool-form").forEach(function (f) { f.addEventListener("submit", function (e) { e.preventDefault(); }); });
  });
})();
