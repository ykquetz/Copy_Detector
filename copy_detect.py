import os
import sys
import json
import hashlib
import threading
import subprocess
import ctypes
import customtkinter as ctk
from collections import defaultdict
from tkinter import filedialog, messagebox
import webbrowser
from datetime import datetime
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

RESIM_UZANTILARI = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".ico"}
ONIZLEME_BOYUTU = (64, 64)
SON_TARAMA_DOSYASI = "son_tarama_sonuclari.json"


class SonucPenceresi(ctk.CTkToplevel):
    def __init__(self, master, sonuclar, klasor_ac_fonksiyonu, hedef_yol, kaydet_fonksiyonu=None):
        super().__init__(master)
        self.title("Tarama Sonuçları")
        self.geometry("950x740")

        self.grab_set()

        self.sonuclar = sonuclar
        self.klasor_ac = klasor_ac_fonksiyonu
        self.hedef_yol = hedef_yol
        self.kaydet_fonksiyonu = kaydet_fonksiyonu

        self.su_anki_sayfa = 0
        self.sayfa_basina_oge = 25
        self.toplam_sayfa = max(1, (len(sonuclar) + self.sayfa_basina_oge - 1) // self.sayfa_basina_oge)

        self._onizleme_cache = {}
        self._kilitli_gruplar = set()
        self._grup_widgetlari = {}

        self._orijinal_kume = {}
        for grup in self.sonuclar:
            self._orijinal_kume[id(grup)] = self._orijinalleri_hesapla(grup)

        self.ust_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ust_frame.pack(fill="x", pady=15, padx=15)

        self.baslik = ctk.CTkLabel(
            self.ust_frame,
            text=f"Bulunan Kopya Grupları ({len(sonuclar)} Farklı İçerik Eşleşmesi)",
            font=("Arial", 18, "bold"), text_color="#00BFFF",
        )
        self.baslik.pack(side="left")

        self.buton_grubu = ctk.CTkFrame(self.ust_frame, fg_color="transparent")
        self.buton_grubu.pack(side="right")

        self.genel_sil_btn = ctk.CTkButton(
            self.buton_grubu, text="🗑 Tümünde İlkini Tut, Gerisini Sil", font=("Arial", 13, "bold"),
            fg_color="#c0392b", hover_color="#922b21", command=self.genel_toplu_sil_onayla,
        )
        self.genel_sil_btn.pack(side="left", padx=(0, 8))

        self.html_btn = ctk.CTkButton(
            self.buton_grubu, text="📄 HTML Rapor Oluştur", font=("Arial", 14, "bold"),
            fg_color="#28a745", hover_color="#218838", command=self.html_rapor_olustur,
        )
        self.html_btn.pack(side="left")

        self.liste_alani = ctk.CTkScrollableFrame(self, width=900, height=540)
        self.liste_alani.pack(pady=5, padx=15, fill="both", expand=True)

        self.alt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.alt_frame.pack(fill="x", pady=10, padx=20)

        self.onceki_btn = ctk.CTkButton(self.alt_frame, text="<< Önceki Sayfa", width=120, command=self.onceki_sayfa)
        self.onceki_btn.pack(side="left")

        self.sayfa_bilgisi = ctk.CTkLabel(self.alt_frame, text="", font=("Arial", 14, "bold"))
        self.sayfa_bilgisi.pack(side="left", expand=True)

        self.sayfaya_git_girisi = ctk.CTkEntry(self.alt_frame, width=60, placeholder_text="Sayfa")
        self.sayfaya_git_girisi.pack(side="right", padx=(8, 0))
        self.sayfaya_git_girisi.bind("<Return>", lambda e: self.sayfaya_git())

        self.sayfaya_git_btn = ctk.CTkButton(self.alt_frame, text="Git", width=50, command=self.sayfaya_git)
        self.sayfaya_git_btn.pack(side="right", padx=(8, 0))

        self.sonraki_btn = ctk.CTkButton(self.alt_frame, text="Sonraki Sayfa >>", width=120, command=self.sonraki_sayfa)
        self.sonraki_btn.pack(side="right")

        self.sayfayi_ciz()

    def _orijinalleri_hesapla(self, grup):
        mtimeler = {}
        for yol in grup:
            try:
                mtimeler[yol] = os.path.getmtime(yol)
            except Exception:
                pass
        if not mtimeler:
            return set()
        en_eski = min(mtimeler.values())
        return {yol for yol, m in mtimeler.items() if m == en_eski}

    def _silinebilir_mi(self, yol, grup):
        orijinal_kume = self._orijinal_kume.get(id(grup), set())
        if yol not in orijinal_kume:
            return True
        mevcut_orijinal_sayisi = sum(1 for o in orijinal_kume if o in grup)
        return mevcut_orijinal_sayisi > 1

    def sayfayi_ciz(self):
        for widget in self.liste_alani.winfo_children():
            widget.destroy()
        self._grup_widgetlari.clear()

        baslangic = self.su_anki_sayfa * self.sayfa_basina_oge
        bitis = baslangic + self.sayfa_basina_oge
        gosterilecekler = self.sonuclar[baslangic:bitis]

        for i, grup in enumerate(gosterilecekler):
            gercek_index = baslangic + i + 1
            kilitli = id(grup) in self._kilitli_gruplar

            grup_frame = ctk.CTkFrame(
                self.liste_alani,
                fg_color="#3a3220" if kilitli else "#2B2B2B",
                corner_radius=10,
                border_width=2 if kilitli else 0,
                border_color="#FFD700" if kilitli else None,
            )
            grup_frame.pack(pady=10, padx=10, fill="x")

            grup_ust_satir = ctk.CTkFrame(grup_frame, fg_color="transparent")
            grup_ust_satir.pack(fill="x", padx=10, pady=(10, 5))

            grup_basligi = ctk.CTkLabel(
                grup_ust_satir,
                text=f"{'🔒 ' if kilitli else ''}Kopya Grubu {gercek_index} - ({len(grup)} Adet Birebir Aynı Dosya)",
                font=("Arial", 14, "bold"), text_color="#FFA500",
            )
            grup_basligi.pack(side="left")

            kilit_btn = ctk.CTkButton(
                grup_ust_satir, text="🔓 Kilidi Aç" if kilitli else "🔒 Kilitle", width=110, height=26,
                fg_color="#555555" if kilitli else "#2f6f4f",
                hover_color="#444444" if kilitli else "#235a3c",
                font=("Arial", 11),
                command=lambda g=grup, gi=gercek_index: self._kilit_durumunu_degistir(g, gi),
            )
            kilit_btn.pack(side="right")

            toplu_sil_btn = ctk.CTkButton(
                grup_ust_satir, text="🗑 İlkini Tut, Gerisini Sil", width=170, height=26,
                fg_color="#8e2de2", hover_color="#6a1cb5", font=("Arial", 11),
                command=lambda g=grup, gf=grup_frame, gb=grup_basligi: self._toplu_sil_onayla(g, gf, gb),
            )
            toplu_sil_btn.pack(side="right", padx=(0, 8))

            self._grup_widgetlari[id(grup)] = (grup_frame, grup_basligi, kilit_btn, gercek_index)

            for yol in list(grup):
                self._dosya_satiri_olustur(grup_frame, grup, yol, grup_basligi)

        self.sayfa_bilgisi.configure(text=f"Sayfa {self.su_anki_sayfa + 1} / {self.toplam_sayfa}")
        self.onceki_btn.configure(state="normal" if self.su_anki_sayfa > 0 else "disabled")
        self.sonraki_btn.configure(state="normal" if self.su_anki_sayfa < self.toplam_sayfa - 1 else "disabled")

        self.liste_alani._parent_canvas.yview_moveto(0)

    def sayfaya_git(self):
        metin = self.sayfaya_git_girisi.get().strip()
        if not metin.isdigit():
            messagebox.showwarning("Geçersiz Sayfa", "Lütfen geçerli bir sayfa numarası girin.")
            return
        hedef_sayfa = int(metin)
        if hedef_sayfa < 1 or hedef_sayfa > self.toplam_sayfa:
            messagebox.showwarning(
                "Geçersiz Sayfa",
                f"Sayfa numarası 1 ile {self.toplam_sayfa} arasında olmalıdır.",
            )
            return
        self.su_anki_sayfa = hedef_sayfa - 1
        self.sayfayi_ciz()
        self.sayfaya_git_girisi.delete(0, "end")

    def _kilit_durumunu_degistir(self, grup, gercek_index):
        if id(grup) in self._kilitli_gruplar:
            self._kilitli_gruplar.discard(id(grup))
        else:
            self._kilitli_gruplar.add(id(grup))

        kayit = self._grup_widgetlari.get(id(grup))
        if kayit is None:
            self.sayfayi_ciz()
            return

        grup_frame, grup_basligi, kilit_btn, gi = kayit
        kilitli = id(grup) in self._kilitli_gruplar

        grup_frame.configure(
            fg_color="#3a3220" if kilitli else "#2B2B2B",
            border_width=2 if kilitli else 0,
            border_color="#FFD700" if kilitli else None,
        )
        grup_basligi.configure(
            text=f"{'🔒 ' if kilitli else ''}Kopya Grubu {gi} - ({len(grup)} Adet Birebir Aynı Dosya)",
        )
        kilit_btn.configure(
            text="🔓 Kilidi Aç" if kilitli else "🔒 Kilitle",
            fg_color="#555555" if kilitli else "#2f6f4f",
            hover_color="#444444" if kilitli else "#235a3c",
        )

    def _resim_mi(self, yol):
        _, uzanti = os.path.splitext(yol)
        return uzanti.lower() in RESIM_UZANTILARI

    def _onizleme_olustur(self, yol):
        if yol in self._onizleme_cache:
            return self._onizleme_cache[yol]
        try:
            img = Image.open(yol)
            img.thumbnail(ONIZLEME_BOYUTU)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self._onizleme_cache[yol] = ctk_img
            return ctk_img
        except Exception:
            self._onizleme_cache[yol] = None
            return None

    def _dosya_satiri_olustur(self, grup_frame, grup, yol, grup_basligi):
        dosya_satiri = ctk.CTkFrame(grup_frame, fg_color="transparent")
        dosya_satiri.pack(pady=2, fill="x")

        if self._resim_mi(yol):
            onizleme = self._onizleme_olustur(yol)
            if onizleme is not None:
                ctk.CTkLabel(dosya_satiri, image=onizleme, text="").pack(side="left", padx=(15, 5), pady=5)
            else:
                ctk.CTkLabel(dosya_satiri, text="🖼", width=64, font=("Arial", 24)).pack(side="left", padx=(15, 5), pady=5)

        orijinal_kume = self._orijinal_kume.get(id(grup), set())
        etiket_metni = yol
        if yol in orijinal_kume:
            etiket_metni = "⭐ " + yol

        yol_etiketi = ctk.CTkLabel(
            dosya_satiri, text=etiket_metni, font=("Consolas", 12),
            wraplength=420, justify="left",
            text_color="#FFD700" if yol in orijinal_kume else None,
        )
        yol_etiketi.pack(side="left", padx=15, pady=5, fill="x", expand=True)

        silinebilir = self._silinebilir_mi(yol, grup)
        sil_butonu = ctk.CTkButton(
            dosya_satiri,
            text="🗑 Sil" if silinebilir else "🔒 Korumalı",
            width=90, height=28,
            fg_color="#a93226" if silinebilir else "#555555",
            hover_color="#7b241c" if silinebilir else "#555555",
            state="normal" if silinebilir else "disabled",
            command=(lambda y=yol, gf=grup_frame, ds=dosya_satiri, g=grup, gb=grup_basligi:
                     self._dosya_sil_onayla(y, gf, ds, g, gb)) if silinebilir else None,
        )
        sil_butonu.pack(side="right", padx=(5, 5), pady=5)

        git_butonu = ctk.CTkButton(dosya_satiri, text="Klasörde Göster", width=120, height=28,
                                    command=lambda y=yol: self.klasor_ac(y))
        git_butonu.pack(side="right", padx=5, pady=5)

    def _dosya_sil_onayla(self, yol, grup_frame, dosya_satiri, grup, grup_basligi):
        if not self._silinebilir_mi(yol, grup):
            messagebox.showwarning(
                "Korumalı Dosya",
                "Bu dosya grubun son kalan orijinal dosyasıdır ve silinemez.\n"
                "Bir grupta her zaman en az bir dosya korunur.",
            )
            return

        onay = messagebox.askyesno(
            "Dosyayı Sil",
            f"Bu dosyayı kalıcı olarak silmek istediğinize emin misiniz?\n\n{yol}\n\n"
            "Bu işlem GERİ ALINAMAZ.",
            icon="warning",
        )
        if not onay:
            return

        try:
            os.remove(yol)
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya silinemedi:\n{yol}\n\n{e}")
            return

        self._dosyayi_yapidan_cikar(yol, grup, grup_frame, dosya_satiri, grup_basligi)
        self._degisikligi_kaydet()

    def _toplu_sil_onayla(self, grup, grup_frame, grup_basligi):
        orijinal_kume = self._orijinal_kume.get(id(grup), set())
        korunacak = next((o for o in grup if o in orijinal_kume), grup[0])
        silinecekler = [y for y in grup if y != korunacak]

        if not silinecekler:
            messagebox.showinfo("Bilgi", "Bu grupta silinecek başka dosya yok.")
            return

        liste_metni = "\n".join(f"  • {y}" for y in silinecekler[:15])
        if len(silinecekler) > 15:
            liste_metni += f"\n  ... ve {len(silinecekler) - 15} dosya daha"

        onay = messagebox.askyesno(
            "Toplu Silme Onayı",
            f"'{korunacak}' korunacak (silinmeyecek).\n\n"
            f"Aşağıdaki {len(silinecekler)} dosya KALICI olarak silinecek:\n\n"
            f"{liste_metni}\n\nBu işlem GERİ ALINAMAZ. Onaylıyor musunuz?",
            icon="warning",
        )
        if not onay:
            return

        basarisiz = []
        for yol in list(silinecekler):
            try:
                os.remove(yol)
                grup.remove(yol)
                self._onizleme_cache.pop(yol, None)
            except Exception as e:
                basarisiz.append((yol, str(e)))

        if basarisiz:
            hata_metni = "\n".join(f"  • {y}: {e}" for y, e in basarisiz[:10])
            messagebox.showerror(
                "Bazı Dosyalar Silinemedi",
                f"{len(basarisiz)} dosya silinirken hata oluştu:\n\n{hata_metni}",
            )

        if len(grup) <= 1 and grup in self.sonuclar:
            self.sonuclar.remove(grup)
            self._kilitli_gruplar.discard(id(grup))
            self._grup_silindi_sonrasi_guncelle()
        self.sayfayi_ciz()
        self._degisikligi_kaydet()

    def genel_toplu_sil_onayla(self):
        silinecek_gruplar = [g for g in self.sonuclar if id(g) not in self._kilitli_gruplar]
        kilitli_grup_sayisi = len(self.sonuclar) - len(silinecek_gruplar)

        if not silinecek_gruplar:
            messagebox.showinfo("Bilgi", "Silinecek hiçbir grup yok (tüm gruplar kilitli).")
            return

        toplam_silinecek_dosya = 0
        plan = []
        for grup in silinecek_gruplar:
            orijinal_kume = self._orijinal_kume.get(id(grup), set())
            korunacak = next((o for o in grup if o in orijinal_kume), grup[0])
            silinecekler = [y for y in grup if y != korunacak]
            toplam_silinecek_dosya += len(silinecekler)
            plan.append((grup, korunacak, silinecekler))

        if toplam_silinecek_dosya == 0:
            messagebox.showinfo("Bilgi", "Silinecek hiçbir dosya yok.")
            return

        kilit_notu = f"\n\n({kilitli_grup_sayisi} kilitli grup bu işlemden muaf tutulacak.)" if kilitli_grup_sayisi else ""
        onay = messagebox.askyesno(
            "Genel Toplu Silme Onayı",
            f"Kilitli olmayan {len(silinecek_gruplar)} grupta, her grubun ilk (orijinal) "
            f"dosyası korunacak ve toplam {toplam_silinecek_dosya} kopya dosya KALICI olarak "
            f"silinecek.{kilit_notu}\n\nBu işlem GERİ ALINAMAZ. Onaylıyor musunuz?",
            icon="warning",
        )
        if not onay:
            return

        basarisiz_toplam = []
        silinen_toplam = 0
        elenen_gruplar = []

        for grup, korunacak, silinecekler in plan:
            for yol in list(silinecekler):
                try:
                    os.remove(yol)
                    grup.remove(yol)
                    self._onizleme_cache.pop(yol, None)
                    silinen_toplam += 1
                except Exception as e:
                    basarisiz_toplam.append((yol, str(e)))

            if len(grup) <= 1:
                elenen_gruplar.append(grup)

        for grup in elenen_gruplar:
            if grup in self.sonuclar:
                self.sonuclar.remove(grup)
            self._kilitli_gruplar.discard(id(grup))

        self._grup_silindi_sonrasi_guncelle()
        self.su_anki_sayfa = 0
        self.sayfayi_ciz()
        self._degisikligi_kaydet()

        sonuc_mesaji = f"{silinen_toplam} dosya başarıyla silindi."
        if basarisiz_toplam:
            sonuc_mesaji += f"\n{len(basarisiz_toplam)} dosya silinemedi (erişim hatası vb.)."
        messagebox.showinfo("Genel Silme Tamamlandı", sonuc_mesaji)

    def _dosyayi_yapidan_cikar(self, yol, grup, grup_frame, dosya_satiri, grup_basligi):
        grup.remove(yol)
        self._onizleme_cache.pop(yol, None)
        dosya_satiri.destroy()

        if len(grup) <= 1:
            if grup in self.sonuclar:
                self.sonuclar.remove(grup)
            self._kilitli_gruplar.discard(id(grup))
            grup_frame.destroy()
            self._grup_silindi_sonrasi_guncelle()
            self.sayfayi_ciz()
        else:
            grup_basligi.configure(text=f"Kopya Grubu - ({len(grup)} Adet Birebir Aynı Dosya)")

    def _grup_silindi_sonrasi_guncelle(self):
        self.toplam_sayfa = max(1, (len(self.sonuclar) + self.sayfa_basina_oge - 1) // self.sayfa_basina_oge)
        if self.su_anki_sayfa >= self.toplam_sayfa:
            self.su_anki_sayfa = self.toplam_sayfa - 1
        self.baslik.configure(text=f"Bulunan Kopya Grupları ({len(self.sonuclar)} Farklı İçerik Eşleşmesi)")

    def _degisikligi_kaydet(self):
        if self.kaydet_fonksiyonu is not None:
            try:
                self.kaydet_fonksiyonu(self.sonuclar, self.hedef_yol)
            except Exception:
                pass

    def onceki_sayfa(self):
        if self.su_anki_sayfa > 0:
            self.su_anki_sayfa -= 1
            self.sayfayi_ciz()

    def sonraki_sayfa(self):
        if self.su_anki_sayfa < self.toplam_sayfa - 1:
            self.su_anki_sayfa += 1
            self.sayfayi_ciz()

    def html_rapor_olustur(self):
        temiz_yol = self.hedef_yol.replace("\\", "_").replace("/", "_").replace(":", "")
        while "__" in temiz_yol:
            temiz_yol = temiz_yol.replace("__", "_")
        temiz_yol = temiz_yol.strip("_")

        varsayilan_dosya_adi = f"{temiz_yol}_kopya_raporu.html" if temiz_yol else "kopya_raporu.html"

        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Dosyası", "*.html")],
            title="Raporu Nereye Kaydetmek İstersiniz?",
            initialfile=varsayilan_dosya_adi,
        )

        if not dosya_yolu:
            return

        html_icerik = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Kopya Dosya Raporu ({self.hedef_yol})</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; padding: 20px; }}
        h1 {{ color: #00BFFF; text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        .summary {{ text-align: center; font-size: 1.2em; margin-bottom: 30px; color: #32CD32; }}
        .group {{ background-color: #1e1e1e; margin-bottom: 20px; padding: 15px; border-radius: 8px; border-left: 5px solid #FFA500; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .group-title {{ color: #FFA500; font-weight: bold; margin-bottom: 10px; font-size: 1.1em; }}
        .file-row {{ display: flex; align-items: center; margin: 5px 0; margin-left: 20px; padding: 8px; background-color: #2b2b2b; border-radius: 4px; }}
        .file-path {{ font-family: Consolas, monospace; word-break: break-all; margin-left: 15px; color: #dcdcdc; }}
        .copy-btn {{ background-color: #007bff; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-size: 0.9em; font-weight: bold; white-space: nowrap; cursor: pointer; transition: 0.2s; }}
        .copy-btn:hover {{ background-color: #0056b3; }}
        .copy-btn.copied {{ background-color: #28a745; }}
    </style>
    <script>
        function copyToClipboard(button, text) {{
            navigator.clipboard.writeText(text).then(function() {{
                var originalText = button.innerText;
                button.innerText = "✓ Kopyalandı";
                button.classList.add("copied");
                setTimeout(function() {{
                    button.innerText = originalText;
                    button.classList.remove("copied");
                }}, 2000);
            }});
        }}
    </script>
</head>
<body>
    <h1>Kopya Dosya Tarama Raporu</h1>
    <div class="summary">Taranan Yol: <b>{self.hedef_yol}</b><br>Toplam {len(self.sonuclar)} farklı içerik eşleşmesi bulundu.</div>
"""
        for i, grup in enumerate(self.sonuclar, 1):
            html_icerik += f'    <div class="group">\n'
            html_icerik += f'        <div class="group-title">Kopya Grubu {i} ({len(grup)} Adet Dosya)</div>\n'
            for yol in grup:
                klasor_yolu = os.path.dirname(yol)
                js_yol = klasor_yolu.replace('\\', '\\\\')

                html_icerik += f'        <div class="file-row">\n'
                html_icerik += f'            <button class="copy-btn" onclick="copyToClipboard(this, \'{js_yol}\')">📋 Yolu Kopyala</button>\n'
                html_icerik += f'            <div class="file-path">{yol}</div>\n'
                html_icerik += f'        </div>\n'
            html_icerik += f'    </div>\n'

        html_icerik += "</body>\n</html>"

        try:
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(html_icerik)
            messagebox.showinfo("Başarılı", "HTML raporu başarıyla oluşturuldu!\nTarayıcınızda açılıyor.")
            webbrowser.open(dosya_yolu)
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor kaydedilirken bir hata oluştu:\n{e}")


class KopyaBulucuUygulamasi(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NAS Kopya Dosya Bulucu")
        self.geometry("750x600")

        self._kapatiliyor = False
        self.protocol("WM_DELETE_WINDOW", self._pencereyi_kapat)

        self._iptal_bayragi = threading.Event()
        self._tarama_devam_ediyor = False

        self.ust_frame = ctk.CTkFrame(self)
        self.ust_frame.pack(pady=20, padx=20, fill="x")

        self.yol_etiketi = ctk.CTkLabel(self.ust_frame, text="Taranacak Sürücü veya Klasör Yolu (Örn: A:\\ veya C:\\):", font=("Arial", 14, "bold"))
        self.yol_etiketi.pack(pady=(10, 0))

        self.yol_satiri = ctk.CTkFrame(self.ust_frame, fg_color="transparent")
        self.yol_satiri.pack(pady=10)

        self.yol_girisi = ctk.CTkEntry(self.yol_satiri, width=450, placeholder_text="Dosya yolunu buraya yapıştırın...")
        self.yol_girisi.pack(side="left")

        self.klasor_sec_butonu = ctk.CTkButton(
            self.yol_satiri, text="📁 Klasör Seç", width=110,
            command=self.klasor_secici_ac,
        )
        self.klasor_sec_butonu.pack(side="left", padx=(8, 0))

        self.buton_satiri = ctk.CTkFrame(self.ust_frame, fg_color="transparent")
        self.buton_satiri.pack(pady=(0, 10))

        self.baslat_butonu = ctk.CTkButton(self.buton_satiri, text="Taramayı Başlat", font=("Arial", 14, "bold"), command=self.taramayi_baslat_thread)
        self.baslat_butonu.pack(side="left", padx=5)

        self.iptal_butonu = ctk.CTkButton(
            self.buton_satiri, text="İptal Et", font=("Arial", 14, "bold"),
            fg_color="#a93226", hover_color="#7b241c", state="disabled",
            command=self.taramayi_iptal_et,
        )
        self.iptal_butonu.pack(side="left", padx=5)

        self.son_sonucu_yukle_butonu = ctk.CTkButton(
            self.buton_satiri, text="Son Sonucu Yükle", font=("Arial", 13),
            fg_color="#444444", hover_color="#555555",
            command=self.son_sonucu_yukle,
        )
        self.son_sonucu_yukle_butonu.pack(side="left", padx=5)
        if not os.path.isfile(SON_TARAMA_DOSYASI):
            self.son_sonucu_yukle_butonu.configure(state="disabled")

        self.log_ekrani = ctk.CTkTextbox(self, width=710, height=350, state="disabled", font=("Consolas", 12))
        self.log_ekrani.pack(pady=10, padx=20)

        self.atlanan_dosyalar = []

    def _pencereyi_kapat(self):
        if self._tarama_devam_ediyor:
            onay = messagebox.askyesno(
                "Tarama Sürüyor",
                "Tarama henüz tamamlanmadı. Programı kapatırsanız tarama "
                "iptal edilecek. Kapatmak istediğinize emin misiniz?",
            )
            if not onay:
                return
            self._iptal_bayragi.set()

        self._kapatiliyor = True
        self.destroy()

    def _guvenli_after(self, *args, **kwargs):
        if self._kapatiliyor:
            return
        try:
            self.after(*args, **kwargs)
        except Exception:
            pass

    def log_yaz(self, mesaj):
        self._guvenli_after(0, self._log_yaz_ui, mesaj)

    def _log_yaz_ui(self, mesaj):
        self.log_ekrani.configure(state="normal")
        self.log_ekrani.insert("end", mesaj + "\n")
        self.log_ekrani.see("end")
        self.log_ekrani.configure(state="disabled")

    def buton_durumunu_ayarla(self, durum):
        self._guvenli_after(0, lambda: self.baslat_butonu.configure(state=durum))

    def sonuc_ekranini_ac_thread_safe(self, sonuclar, hedef_yol):
        self._guvenli_after(0, self.sonuc_ekranini_ac, sonuclar, hedef_yol)

    def klasor_secici_ac(self):
        secilen_klasor = filedialog.askdirectory(title="Taranacak Klasörü Seçin")
        if secilen_klasor:
            self.yol_girisi.delete(0, "end")
            self.yol_girisi.insert(0, secilen_klasor)

    def klasoru_ac_ve_sec(self, dosya_yolu):
        uygun_yol = os.path.normpath(dosya_yolu)
        if sys.platform != "win32":
            self.log_yaz("Bu özellik sadece Windows'ta çalışır.")
            return
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
            subprocess.Popen(["explorer", "/select,", uygun_yol])
        except Exception as e:
            self.log_yaz(f"Klasör açılamadı: {e}")

    def taramayi_baslat_thread(self):
        hedef_yol = self.yol_girisi.get().strip()

        if not hedef_yol or not os.path.exists(hedef_yol):
            self.log_yaz("Hata: Lütfen geçerli ve var olan bir dosya yolu girin!")
            return

        self.baslat_butonu.configure(state="disabled")
        self.iptal_butonu.configure(state="normal")
        self.log_ekrani.configure(state="normal")
        self.log_ekrani.delete("1.0", "end")
        self.log_ekrani.configure(state="disabled")

        self.atlanan_dosyalar = []
        self._iptal_bayragi.clear()
        self._tarama_devam_ediyor = True
        threading.Thread(target=self.tarama_motoru, args=(hedef_yol,), daemon=True).start()

    def taramayi_iptal_et(self):
        if not self._tarama_devam_ediyor:
            return
        onay = messagebox.askyesno("Taramayı İptal Et", "Devam eden taramayı iptal etmek istediğinize emin misiniz?")
        if onay:
            self._iptal_bayragi.set()
            self.log_yaz("\n[!] İptal isteği alındı, tarama durduruluyor...")
            self.iptal_butonu.configure(state="disabled")

    def tarama_motoru(self, hedef_yol):
        self.log_yaz(f"[*] Tarama Başladı: {hedef_yol}")
        self.log_yaz("[*] Adım 1: Klasörler taranıyor ve dosya boyutları kontrol ediliyor. Bu işlem disk hızına/ağa bağlıdır...")

        boyut_gruplari = defaultdict(list)
        taranan_dosya_sayisi = 0
        iptal_edildi = False

        for kok_klasor, _, dosyalar in os.walk(hedef_yol):
            if self._iptal_bayragi.is_set():
                iptal_edildi = True
                break
            for dosya_adi in dosyalar:
                if self._iptal_bayragi.is_set():
                    iptal_edildi = True
                    break

                tam_yol = os.path.join(kok_klasor, dosya_adi)

                if os.path.islink(tam_yol):
                    continue

                try:
                    dosya_boyutu = os.path.getsize(tam_yol)
                    boyut_gruplari[dosya_boyutu].append(tam_yol)
                    taranan_dosya_sayisi += 1

                    if taranan_dosya_sayisi % 5000 == 0:
                        self.log_yaz(f"   ...Şu ana kadar {taranan_dosya_sayisi} dosya kontrol edildi.")
                except Exception as e:
                    self.atlanan_dosyalar.append((tam_yol, f"Boyut okunamadı: {e}"))

        if iptal_edildi:
            self.log_yaz(f"\n[!] Tarama kullanıcı tarafından iptal edildi. ({taranan_dosya_sayisi} dosya kontrol edilmişti)")
            self._taramayi_sonlandir(sonuclar=[], hedef_yol=hedef_yol, iptal=True)
            return

        self.log_yaz(f"\n[*] Toplam {taranan_dosya_sayisi} dosyanın boyutu analiz edildi.")

        supheli_gruplar = [yollar for yollar in boyut_gruplari.values() if len(yollar) > 1]
        toplam_supheli_dosya = sum(len(grup) for grup in supheli_gruplar)

        if toplam_supheli_dosya == 0:
            self.log_yaz("\n[✓] İşlem Tamamlandı: İçeriği aynı olabilecek (aynı boyutta) hiçbir şüpheli dosya bulunamadı!")
            self._taramayi_sonlandir(sonuclar=[], hedef_yol=hedef_yol)
            return

        self.log_yaz(f"[*] Adım 2: Aynı boyutta olan toplam {toplam_supheli_dosya} şüpheli dosya bulundu.")
        self.log_yaz("[*] Adım 3: İçerikler (SHA-256 Hash) ağ üzerinden parça parça okunarak analiz ediliyor. Lütfen bekleyin...\n")

        kesin_kopyalar = defaultdict(list)
        islenen_supheli = 0

        for yollar in supheli_gruplar:
            if self._iptal_bayragi.is_set():
                iptal_edildi = True
                break
            for yol in yollar:
                if self._iptal_bayragi.is_set():
                    iptal_edildi = True
                    break

                islenen_supheli += 1
                hasher = hashlib.sha256()
                try:
                    with open(yol, 'rb') as f:
                        while chunk := f.read(65536):
                            hasher.update(chunk)
                    dosya_hash = hasher.hexdigest()
                    if dosya_hash:
                        kesin_kopyalar[dosya_hash].append(yol)

                    if islenen_supheli % 10 == 0 or islenen_supheli == toplam_supheli_dosya:
                        self.log_yaz(f"   ...İçerik analizi: %{int((islenen_supheli/toplam_supheli_dosya)*100)} tamamlandı. ({islenen_supheli}/{toplam_supheli_dosya})")
                except Exception as e:
                    self.atlanan_dosyalar.append((yol, f"İçerik okunamadı: {e}"))
                    continue

        if iptal_edildi:
            self.log_yaz(f"\n[!] Tarama kullanıcı tarafından iptal edildi. (İçerik analizi: {islenen_supheli}/{toplam_supheli_dosya} tamamlanmıştı)")
            self._taramayi_sonlandir(sonuclar=[], hedef_yol=hedef_yol, iptal=True)
            return

        sonuclar = [yollar for yollar in kesin_kopyalar.values() if len(yollar) > 1]

        self.log_yaz(f"\n[✓] Tarama Tamamlandı! Toplam {len(sonuclar)} farklı kopya dosya grubu bulundu.")
        self._taramayi_sonlandir(sonuclar, hedef_yol)

    def _taramayi_sonlandir(self, sonuclar, hedef_yol, iptal=False):
        if self.atlanan_dosyalar:
            self.log_yaz(f"\n[!] Uyarı: Tarama sırasında {len(self.atlanan_dosyalar)} dosyaya erişilemedi/okunamadı (atlandı):")
            for yol, sebep in self.atlanan_dosyalar[:50]:
                self.log_yaz(f"     - {yol}  [{sebep}]")
            if len(self.atlanan_dosyalar) > 50:
                self.log_yaz(f"     ...ve {len(self.atlanan_dosyalar) - 50} dosya daha.")

        self._tarama_devam_ediyor = False
        self.buton_durumunu_ayarla("normal")
        self._guvenli_after(0, lambda: self.iptal_butonu.configure(state="disabled"))

        if sonuclar and not iptal:
            self._sonuclari_diske_kaydet(sonuclar, hedef_yol)
            self.sonuc_ekranini_ac_thread_safe(sonuclar, hedef_yol)

    def sonuc_ekranini_ac(self, sonuclar, hedef_yol):
        SonucPenceresi(self, sonuclar, self.klasoru_ac_ve_sec, hedef_yol, kaydet_fonksiyonu=self._sonuclari_diske_kaydet)
        self._guvenli_after(0, lambda: self.son_sonucu_yukle_butonu.configure(state="normal"))

    def _sonuclari_diske_kaydet(self, sonuclar, hedef_yol):
        try:
            veri = {
                "hedef_yol": hedef_yol,
                "olusturma_zamani": datetime.now().isoformat(timespec="seconds"),
                "gruplar": sonuclar,
            }
            with open(SON_TARAMA_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_yaz(f"[!] Sonuçlar diske kaydedilemedi: {e}")

    def son_sonucu_yukle(self):
        if not os.path.isfile(SON_TARAMA_DOSYASI):
            messagebox.showinfo("Bilgi", "Kayıtlı bir tarama sonucu bulunamadı.")
            return
        try:
            with open(SON_TARAMA_DOSYASI, "r", encoding="utf-8") as f:
                veri = json.load(f)
        except Exception as e:
            messagebox.showerror("Hata", f"Kayıtlı sonuç okunamadı:\n{e}")
            return

        gruplar = veri.get("gruplar", [])
        hedef_yol = veri.get("hedef_yol", "")
        zaman = veri.get("olusturma_zamani", "bilinmiyor")

        guncel_gruplar = []
        for grup in gruplar:
            var_olanlar = [y for y in grup if os.path.exists(y)]
            if len(var_olanlar) > 1:
                guncel_gruplar.append(var_olanlar)

        if not guncel_gruplar:
            messagebox.showinfo(
                "Bilgi",
                "Kayıtlı sonuçtaki dosyaların hiçbiri artık geçerli bir kopya "
                "grubu oluşturmuyor (silinmiş/taşınmış olabilirler).",
            )
            return

        self.log_yaz(f"[*] Kayıtlı sonuç yüklendi (tarama zamanı: {zaman}, yol: {hedef_yol})")
        if len(guncel_gruplar) != len(gruplar):
            self.log_yaz(f"[!] {len(gruplar) - len(guncel_gruplar)} grup artık geçerli değil, listeden çıkarıldı.")

        self.sonuc_ekranini_ac(guncel_gruplar, hedef_yol)


if __name__ == "__main__":
    uygulama = KopyaBulucuUygulamasi()
    uygulama.mainloop()