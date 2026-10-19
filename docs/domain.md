# Domain

> İş dünyası, insanlar ve ajanlar arasındaki ortak dil. Kodda yalnız "Kod adı" sütunu kullanılır;
> arayüz metinlerinde ve dokümanlarda Türkçe terim kullanılır. Bir terim burada yoksa önce eklenir.

## Ubiquitous language

| Term | Meaning | Notes / not to be confused with |
|---|---|---|
| Şirketler grubu — `Group` | Ana şirket ve tüm alt şirketlerinin bütünü | Ayrı bir tüzel kişi değildir |
| Şirket — `Company` | Tek bir tüzel kişi/işveren (ayrı SGK sicili); `parent_id` ile ağaç oluşturur | |
| Ana şirket — `ParentCompany` | Ağacın kökündeki şirket (`parent_id` boş) | |
| Alt şirket — `Subsidiary` | Bir üst şirkete bağlı şirket | "Departman" değildir |
| Çalışan — `Employee` | Tam olarak **bir** şirkete bağlı kişi | Kullanıcı hesabından ayrıdır |
| Kullanıcı hesabı — `UserAccount` | Giriş yapan kimlik (identity modülü); en fazla bir çalışana bağlanır | Sistem Yöneticisi hesabının çalışanı olmayabilir |
| Yönetici — `Manager` | Bir çalışanın doğrudan bağlı olduğu çalışan (`manager_id`) | Bir **rol değildir**, hiyerarşiden türetilir |
| Şirket İK — `CompanyHR` | Yalnız kendi şirketinin izin verisini yöneten rol | |
| Grup İK — `GroupHR` | Tüm şirketlerin izin verisini gören/yöneten rol | |
| Sistem Yöneticisi — `SystemAdmin` | Kullanıcı ve rol yönetimi; izin verisine erişimi yok | |
| İzin türü — `LeaveType` | Yıllık, mazeret, ücretsiz, rapor, doğum | |
| Yıllık izin — `AnnualLeave` | Bakiyeden düşen ücretli izin (İş K. md. 53) | |
| Mazeret izni — `StatutoryExcuseLeave` | Yasal sabit süreli ücretli izin (İş K. ek md. 2): evlilik, ölüm, babalık vb. | Bakiyeden düşmez |
| Ücretsiz izin — `UnpaidLeave` | Bakiyesiz, ücretsiz izin | |
| Rapor kaydı — `SickLeaveRecord` | Sağlık raporu nedeniyle devamsızlık; **yalnız tarih ve tür** | Tanı/açıklama tutulmaz (KVKK) |
| Doğum izni kaydı — `MaternityLeaveRecord` | Doğum izni; MVP'de yalnız kayıt | |
| İzin talebi — `LeaveRequest` | Bir çalışanın belirli tarih aralığı için izin talebi | |
| Talep durumu — `LeaveRequestStatus` | `PENDING` Beklemede · `APPROVED` Onaylandı · `REJECTED` Reddedildi · `WITHDRAWN` Geri çekildi · `CANCELLED` İptal edildi | ANEW spec `Status:` alanıyla ilgisizdir |
| Onaylayan — `Approver` | Talebi onaylama/reddetme yetkisi olan kişi (BR-12) | |
| İzne esas kıdem tarihi — `SeniorityDate` | Hakedişin hesaplandığı başlangıç tarihi; İK girer | İşe giriş tarihiyle aynı olmak zorunda değildir |
| Hizmet yılı — `ServiceYear` | Kıdem tarihinden itibaren tamamlanan her tam yıl | |
| Hakediş — `Entitlement` | Bir hizmet yılı tamamlanınca doğan yıllık izin hakkı | |
| Ek gün — `ExtraDays` | Şirket veya çalışan bazında yasal tabana eklenen gün | Yasal tabanı azaltamaz |
| Bakiye — `Balance` | Bir çalışanın kullanılabilir yıllık izin miktarı; hareketlerin toplamı | |
| Bakiye hareketi — `BalanceEntry` | Bakiyeyi değiştiren tek kayıt: hakediş, kullanım, iade, avans, düzeltme | Silinmez, düzeltme yeni hareketle yapılır |
| Devir — `Carryover` | Kullanılmayan bakiyenin sonraki yıla geçmesi (otomatik, sınırsız) | |
| Avans izin — `AdvanceLeave` | Hak doğmadan İK'nın açık işlemiyle verilen izin; eksi bakiye oluşturur | |
| İş günü — `WorkingDay` | Şirketin çalışma düzenine göre çalışılan, tatil olmayan gün | |
| Resmi tatil — `PublicHoliday` | Ulusal bayram ve genel tatil; İK takvime girer | |
| Arife — `HalfDayHoliday` | Öğleden sonrası tatil olan gün; izinde yarım gün sayılır | |
| Yarım gün birimi — `half_days` | Tüm süre hesaplarının birimi: 1 gün = 2 birim | Kodda `float` gün kullanılmaz |
| Denetim olayı — `AuditEvent` | Değişmez kayıt: kim, ne zaman, hangi kayıt, önce/sonra | |

## Business rules
**Hakediş (İş K. md. 53–54)**
- BR-1: Yıllık izin hakkı, izne esas kıdem tarihinden itibaren her tam hizmet yılı tamamlandığında
  doğar; ilk hak 1. yıl dolunca doğar.
- BR-2: Hakediş miktarı, tamamlanan hizmet yılına göre: 1–5 yıl (5 dahil) → 14 gün;
  6–14 yıl → 20 gün; 15 yıl ve üzeri → 26 gün.
- BR-3: Hakediş tarihinde 18 yaş veya altında ya da 50 yaş veya üstünde olan çalışanın hakkı
  20 günden az olamaz.
- BR-4: Ek gün (şirket ve/veya çalışan bazında) yasal hakedişin üstüne eklenir; sonuç hiçbir
  zaman BR-2/BR-3'ün altına düşemez.

**Süre sayımı (İş K. md. 56)**
- BR-5: İzin süresi yarım gün birimiyle hesaplanır; talep tam gün veya yarım gün olabilir.
- BR-6: Hafta tatili (şirket çalışma düzeninde çalışılmayan günler) ve resmi tatiller izin
  süresinden sayılmaz. Varsayılan çalışma düzeni Pzt–Cum; şirket bazında Cumartesi eklenebilir.
- BR-7: Arife günü izne denk gelirse 1 yarım gün birimi sayılır.

**Bakiye**
- BR-8: Bakiye, bakiye hareketlerinin toplamıdır; hiçbir zaman doğrudan düzenlenmez.
- BR-9: Kullanılmayan yıllık izin süresiz devreder; yıl sonunda silinmez veya sıfırlanmaz.
- BR-10: Normal talep bakiyeyi eksiye düşüremez; eksi bakiye yalnız İK'nın avans izin işlemiyle
  oluşur.
- BR-11: Mazeret, ücretsiz izin, rapor ve doğum izni bakiyeyi etkilemez. Mazeret izni süreleri
  yasal sabittir: evlilik 3, evlat edinme 3, birinci derece yakının ölümü 3, eşin doğumu
  (babalık) 5 gün; engelli çocuk tedavisi yılda 10 güne kadar.

**Onay akışı**
- BR-12: Talebi çalışanın doğrudan yöneticisi onaylar/reddeder. Doğrudan yönetici yoksa bir üst
  yönetici; hiyerarşide hiç yönetici yoksa çalışanın şirketinin Şirket İK'sı onaylar.
- BR-13: Kimse kendi talebini onaylayamaz.
- BR-14: Onay tek kademelidir; onaylanan yıllık izin talebi onay anında bakiyeden düşer.
- BR-15: Çalışan yalnız `PENDING` talebini geri çekebilir (`WITHDRAWN`). Onaylanmış izni yalnız
  İK iptal eder (`CANCELLED`); kullanılmamış kısım bakiyeye iade hareketi olarak döner.
- BR-16: Rapor ve doğum izni kayıtlarını yalnız İK girer; onay akışına girmez.

**Görünürlük**
- BR-17: Çalışan yalnız kendi kayıtlarını; yönetici kendisine (doğrudan veya dolaylı) bağlı
  çalışanların talep ve bakiyelerini; Şirket İK yalnız kendi şirketini; Grup İK tüm şirketleri
  görür. Sistem Yöneticisi izin verisi görmez.
- BR-18: Yönetici, ekibinin rapor/doğum kayıtlarında yalnız "izinli" bilgisini görür; türü ve
  detayı yalnız İK görür.

## Key domain invariants
- Her çalışan tam olarak bir şirkete bağlıdır; şirket ağacında döngü olamaz.
- Yönetici hiyerarşisinde döngü olamaz; bir çalışanın yöneticisi kendisi olamaz.
- Aynı çalışan için tarih aralığı çakışan iki aktif (`PENDING`/`APPROVED`) talep olamaz.
- Bir bakiye hareketi ve bir denetim olayı oluşturulduktan sonra değiştirilmez veya silinmez.
- Yıllık izin hakkı yasal tabanın altına düşürülemez (BR-2, BR-3, BR-4).
- Durum değiştiren her işlem (talep, onay, ret, iptal, kıdem tarihi, ek gün, tatil, rol) bir
  denetim olayı üretir.
