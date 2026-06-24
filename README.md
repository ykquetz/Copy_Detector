# Copy_Detector
Windows üzerinde çalışan, yerel diskleri veya ağ üzerindeki (NAS) klasörleri tarayarak içeriği birebir aynı olan (gerçek kopya) dosyaları bulan, görsel önizleme ile gösteren ve güvenli bir şekilde silmenize yardımcı olan masaüstü uygulaması.

Tarama iki aşamalıdır:

1. **Boyut karşılaştırması** — Önce tüm dosyalar boyutlarına göre gruplanır. Boyutu eşsiz olan dosyalar elenir (kopya olamazlar).
2. **SHA-256 hash karşılaştırması** — Aynı boyuttaki dosyaların içeriği parça parça okunup hash'lenir. Hash'i eşleşen dosyalar **kesin kopya** sayılır.

Bu iki aşamalı yaklaşım, büyük NAS sürücülerinde (yüz binlerce dosya) her dosyanın baştan sona okunmasını gerektirmeden hızlı ve güvenilir sonuç verir.

## Özellikler

- Binlerce kopya grubunu donmadan gösteren **sayfalama**
- Resim dosyaları için uygulama içinde **küçük önizleme (thumbnail)**
- Her grupta en eski dosyanın otomatik **"Orijinal"** olarak işaretlenmesi ve silinmekten korunması
- Tek dosya, grup bazlı veya **tüm sonuçlar için tek tıkla toplu silme**
- İstediğiniz grupları **kilitleyerek** genel toplu silmeden hariç tutma
- Sonuçlardan **HTML rapor** oluşturma (yol kopyalama butonlu)
- Devam eden taramayı **iptal etme**
- Son tarama sonucunun otomatik kaydedilip program yeniden açıldığında **geri yüklenmesi**

## Kullanım
- Dist klasörünün içindeyi dosyayı çalıştırın.
 


### Ana Pencere

| Buton / Alan | Ne işe yarar |
|---|---|
| **Yol giriş kutusu** | Taranacak klasör veya sürücü yolunu buraya yazın/yapıştırın (örn. `C:\Kullanıcılar\Fotoğraflar`). |
| **📁 Klasör Seç** | Dosya gezgini penceresi açar; klasörü elle yazmak yerine gözden geçirip seçmenizi sağlar. Seçim yapıldığında yol giriş kutusuna otomatik yazılır.
| **Taramayı Başlat** | Girilen yoldaki tüm alt klasörleri tarayıp kopya dosyaları aramaya başlar. Tarama arka planda çalışır, arayüz donmaz. |
| **İptal Et** | Devam eden taramayı durdurur. Onay penceresi çıkar; onaylanırsa tarama o ana kadar bulduklarını bir kenara bırakıp tamamen sonlanır (sonuç penceresi açılmaz). |
| **Son Sonucu Yükle** | Bir önceki taramada bulunan sonuçları yeniden taramaya gerek kalmadan diskten geri yükler. Bu arada silinmiş/taşınmış dosyalar otomatik olarak listeden çıkarılır. Hiç tarama yapılmadıysa bu buton pasif görünür. |
| **Log ekranı** | Tarama ilerlemesini (kaç dosya tarandı, hangi dosyalar atlandı, kaç kopya bulundu) canlı olarak gösterir. |
| **Sayfa numarası girişi + Git** | İstediğiniz sayfa numarasını yazıp Git butonuna basarak (veya Enter'a basarak) doğrudan o sayfaya atlayabilirsiniz. Geçersiz veya aralık dışı bir numara girilirse uyarı verilir.
Pencere kapatılmaya çalışıldığında tarama hâlâ sürüyorsa onay istenir; onaylanırsa tarama güvenli şekilde iptal edilip program kapanır.

### Sonuç Penceresi

| Buton / Alan | Ne işe yarar |
|---|---|
| **🗑 Tümünde İlkini Tut, Gerisini Sil** | Kilitli **olmayan** tüm gruplarda, her grubun orijinal (en eski) dosyasını koruyup geri kalan tüm kopyaları tek seferde siler. Silmeden önce toplam kaç dosyanın silineceğini ve kaç grubun kilitli olduğu için işlemden muaf tutulacağını gösteren bir onay penceresi çıkar. |
| **📄 HTML Rapor Oluştur** | Tüm kopya gruplarını, yol kopyalama butonlarıyla birlikte tek bir HTML dosyasına kaydeder ve tarayıcıda açar. Kaydetme konumunu siz seçersiniz. |
| **🔒 Kilitle / 🔓 Kilidi Aç** (grup başlığının yanında) | Bir grubu kilitleyerek genel "Tümünde İlkini Tut, Gerisini Sil" işleminden muaf tutar. Kilitli bir grupta tekli "Sil" ve gruba özel "İlkini Tut, Gerisini Sil" butonları yine normal şekilde çalışır — kilit sadece genel/toplu silmeyi etkiler. |
| **🗑 İlkini Tut, Gerisini Sil** (her grubun başlığının yanında) | Sadece o gruptaki orijinali koruyup diğer tüm kopyaları siler. Genel silmeden farkı: tek bir gruba özeldir ve grup kilitli olsa da çalışır. |
| **⭐ (sarı işaretli dosya)** | O gruptaki en eski değişiklik tarihine sahip "Orijinal" dosyayı gösterir. Bu dosya korumalıdır. |
| **🗑 Sil** (her dosya satırının yanında) | O tek dosyayı kalıcı olarak siler. Onay penceresi çıkar. |
| **🔒 Korumalı** (bazı dosyalarda Sil yerine görünür) | Bu dosyanın, grubun son kalan orijinali olduğu ve silinemeyeceği anlamına gelir. Bir grupta her zaman en az bir dosya korunur; birden fazla dosya aynı (en eski) tarihe sahipse bunlardan biri silinebilir, ama sonuncusu asla silinemez. |
| **Klasörde Göster** | (Sadece Windows) Dosya Gezgini'ni açıp ilgili dosyayı seçili hale getirir. |
| **<< Önceki Sayfa / Sonraki Sayfa >>** | Çok sayıda kopya grubu olduğunda (sayfa başına 25 grup) sayfalar arasında gezinmenizi sağlar. |

## Silme Kuralları (Önemli)

- Her grupta dosyalar değişiklik tarihine (mtime) göre incelenir; **en eski tarihli dosya "orijinal" sayılır** ve normalde silinemez.
- Birden fazla dosya aynı (en eski) tarihe sahipse, bunların hepsi orijinal sayılır ama yalnızca **biri** korunur — diğerleri silinebilir. Böylece bir grupta **her zaman en az bir dosya** kalır, grup hiçbir zaman tamamen boşalmaz.
- **Tüm silme işlemleri kalıcıdır ve geri alınamaz.** Program bir Geri Dönüşüm Kutusu'na taşıma yapmaz, `os.remove` ile doğrudan diskten siler. Onay pencerelerini dikkatli okuyun.
- Sembolik linkler (kısayol değil, dosya sistemi düzeyindeki linkler) tarama dışında tutulur; bu sayede bir dosya ile ona işaret eden bir link "kopya" olarak görünmez.

## Sonuçların Kaydedilmesi

Program, her tarama tamamlandığında ve sonuç ekranında her silme işleminden sonra, güncel sonuç listesini çalıştığı klasördeki `son_tarama_sonuclari.json` dosyasına otomatik olarak yazar. Bu sayede program kapanıp yeniden açılsa bile **Son Sonucu Yükle** butonuyla son durumunuza dönebilirsiniz.

## Sınırlamalar

- Sadece Windows'ta "Klasörde Göster" özelliği çalışır.
- Çok büyük NAS sürücülerinde hash hesaplama adımı, dosya sayısına ve ağ hızına bağlı olarak uzun sürebilir; bu sırada **İptal Et** butonunu kullanabilirsiniz.



- Silinen dosyalar geri alınamaz; bu repodaki kod "olduğu gibi" sağlanmıştır, kullanım sorumluluğu kullanıcıya aittir.
- Silinen dosyalar geri alınamaz; bu repodaki kod "olduğu gibi" sağlanmıştır, kullanım sorumluluğu kullanıcıya aittir.
- Silinen dosyalar geri alınamaz; bu repodaki kod "olduğu gibi" sağlanmıştır, kullanım sorumluluğu kullanıcıya aittir.
- Silinen dosyalar geri alınamaz; bu repodaki kod "olduğu gibi" sağlanmıştır, kullanım sorumluluğu kullanıcıya aittir.
- Silinen dosyalar geri alınamaz; bu repodaki kod "olduğu gibi" sağlanmıştır, kullanım sorumluluğu kullanıcıya aittir.
- Silinen dosyalar geri alınamaz; bu repodaki kod "olduğu gibi" sağlanmıştır, kullanım sorumluluğu kullanıcıya aittir.





ENGLİSH

# Copy_Detector

A Windows desktop application that scans local drives or network (NAS) folders to find exact duplicate files, displays them with visual previews, and helps you delete them securely.

The scanning process consists of two phases:

1. **Size comparison** — First, all files are grouped by size. Files with unique sizes are eliminated (they cannot be duplicates).
2. **SHA-256 hash comparison** — Files with identical sizes are read and hashed chunk by chunk. Files with matching hashes are considered **exact duplicates**.

This two-phase approach provides fast and reliable results on large NAS drives (hundreds of thousands of files) without having to read every single file from beginning to end.

## Features

* **Pagination** to display thousands of duplicate groups without freezing
* In-app **thumbnail previews** for image files
* Automatic marking of the oldest file in each group as **"Original"**, protecting it from deletion
* Single-file, group-based, or **one-click bulk deletion for all results**
* **Locking** specific groups to exclude them from global bulk deletion
* Generating an **HTML report** from the results (with path copy buttons)
* **Canceling** an ongoing scan
* Automatic saving of the last scan result and **restoring** it when the program is reopened

## Usage

* Run the executable file located in the Dist folder.

### Main Window

| Button / Area | What it does |
| --- | --- |
| **Path input box** | Type/paste the folder or drive path to be scanned here (e.g., `C:\Users\Photos`). |
| **Start Scan** | Scans all subfolders in the entered path and starts looking for duplicate files. The scan runs in the background; the interface does not freeze. |
| **Cancel** | Stops the ongoing scan. A confirmation prompt appears; if confirmed, the scan discards what it has found so far and completely terminates (the results window does not open). |
| **Load Last Result** | Restores the results found in the previous scan from the disk without needing to rescan. Meanwhile, deleted/moved files are automatically removed from the list. If no scan has been performed, this button appears disabled. |
| **Log screen** | Shows the scan progress live (how many files scanned, which files skipped, how many duplicates found). |

If you try to close the window while a scan is still running, confirmation is requested; if confirmed, the scan is safely canceled and the program closes.

### Results Window

| Button / Area | What it does |
| --- | --- |
| **🗑 Keep First in All, Delete the Rest** | In all **unlocked** groups, keeps the original (oldest) file of each group and deletes all remaining duplicates at once. Before deleting, a confirmation window shows the total number of files to be deleted and how many groups will be exempted due to being locked. |
| **📄 Generate HTML Report** | Saves all duplicate groups into a single HTML file, complete with path copy buttons, and opens it in the browser. You choose the save location. |
| **🔒 Lock / 🔓 Unlock** (next to the group title) | Locks a group to exempt it from the global "Keep First in All, Delete the Rest" operation. Single "Delete" and group-specific "Keep First, Delete the Rest" buttons still work normally in a locked group — the lock only affects global/bulk deletion. |
| **🗑 Keep First, Delete the Rest** (next to each group title) | Protects only the original in that specific group and deletes all other duplicates. Difference from global deletion: it is specific to a single group and works even if the group is locked. |
| **⭐ (yellow marked file)** | Indicates the "Original" file with the oldest modification date in that group. This file is protected. |
| **🗑 Delete** (next to each file row) | Permanently deletes that single file. A confirmation window appears. |
| **🔒 Protected** (appears instead of Delete on some files) | Means this file is the last remaining original of the group and cannot be deleted. At least one file is always protected in a group; if multiple files have the exact same (oldest) date, one of them can be deleted, but the last one never can. |
| **Show in Folder** | (Windows only) Opens File Explorer and selects the respective file. |
| **<< Previous Page / Next Page >>** | Allows you to navigate between pages when there are many duplicate groups (25 groups per page). |

## Deletion Rules (Important)

* In each group, files are evaluated based on their modification date (mtime); **the file with the oldest date is considered the "original"** and normally cannot be deleted.
* If multiple files share the exact same (oldest) date, they are all considered originals, but only **one** is protected — the others can be deleted. This ensures that **there is always at least one file left** in a group; a group is never completely emptied.
* **All deletion operations are permanent and cannot be undone.** The program does not move files to a Recycle Bin; it deletes them directly from the disk using `os.remove`. Read the confirmation prompts carefully.
* Symbolic links (not shortcuts, but file-system level links) are excluded from the scan; this prevents a file and a link pointing to it from showing up as "duplicates".

## Saving Results

Whenever a scan is completed and after every deletion operation on the results screen, the program automatically writes the updated results list to a `son_tarama_sonuclari.json` file in its working directory. This way, even if the program is closed and reopened, you can return to your last state using the **Load Last Result** button.

## Limitations

* The "Show in Folder" feature works only on Windows.
* On very large NAS drives, the hash calculation step may take a long time depending on the number of files and network speed; you can use the **Cancel** button during this time.
* Deleted files cannot be recovered; the code in this repo is provided "as is", and usage is at the user's own risk.
* Deleted files cannot be recovered; the code in this repo is provided "as is", and usage is at the user's own risk.
* Deleted files cannot be recovered; the code in this repo is provided "as is", and usage is at the user's own risk.
* Deleted files cannot be recovered; the code in this repo is provided "as is", and usage is at the user's own risk.
* Deleted files cannot be recovered; the code in this repo is provided "as is", and usage is at the user's own risk.
* Deleted files cannot be recovered; the code in this repo is provided "as is", and usage is at the user's own risk.
