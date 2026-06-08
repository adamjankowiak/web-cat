# Wprowadzenie

Celem projektu jest stworzenie webowej platformy CAT wspierajacej tlumacza w pracy nad dokumentami segment po segmencie. System nie musi na starcie wykonywac automatycznego tlumaczenia maszynowego. Kluczowe funkcje to pamiec tlumaczen, slownik kontekstowy i kontrola pisowni po stronie docelowej.

## Minimalny scenariusz pracy

1. Uzytkownik importuje dokument z tekstem zrodlowym.
2. Backend dzieli tekst na segmenty.
3. Frontend pokazuje segment zrodlowy, pole tlumaczenia i panele pomocnicze.
4. System wyszukuje podobne segmenty w pamieci tlumaczen.
5. System pokazuje terminy ze slownika pasujace do kontekstu segmentu.
6. System sprawdza pisownie wpisanego tlumaczenia.
7. Po zatwierdzeniu segment trafia do pamieci tlumaczen.
8. Uzytkownik eksportuje przetlumaczony dokument lub plik wymiany.

## Zakres funkcjonalny

- Edytor segmentow: statusy, zapis roboczy, zatwierdzanie, filtrowanie.
- Pamiec tlumaczen: exact match, fuzzy match, metadane projektu i jezykow.
- Slownik kontekstowy: terminy, warianty, definicje, przyklady, domeny.
- Sprawdzanie pisowni: lista bledow, sugestie, ignorowanie slow.
- Import/eksport: poczatkowo TXT/CSV/JSON, pozniej XLIFF/TMX/TBX.

## Poza MVP

- Wspolpraca wielu tlumaczy w czasie rzeczywistym.
- Zaawansowane workflow recenzji i akceptacji.
- Integracja z tlumaczeniem maszynowym.
- Rozbudowane zarzadzanie uprawnieniami.
