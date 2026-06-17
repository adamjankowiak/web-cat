# Moduły CAT

## Edytor webowy

Edytor powinien być centralnym widokiem aplikacji. Minimalny układ to lista segmentów, aktywny segment oraz panele z sugestiami.

Funkcje startowe:

- lista segmentów z numerami i statusami,
- pole tekstu docelowego,
- automatyczny zapis roboczy,
- zatwierdzanie segmentu,
- skróty klawiaturowe,
- panel pamięci tłumaczeń,
- panel słownika,
- panel sprawdzania pisowni.

Stan po Etapie 2:

- edytor pobiera dokumenty i segmenty z API,
- uzytkownik moze zaimportowac plik TXT z poziomu frontendu,
- backend segmentuje dokument po zdaniach albo akapitach i zapisuje segmenty w bazie,
- edytor pozwala zapisac robocze tlumaczenie segmentu i oznaczyc segment jako `translated`,
- istnieja statyczne panele pamieci tlumaczen, slownika i spellchecka,
- przycisk wyszukiwania pamieci tlumaczen oraz panele pomocnicze pozostaja statyczne do kolejnych etapow.

## Pamięć tłumaczeń

Pamięć tłumaczeń ma zwracać sugestie na podstawie segmentu źródłowego.

Źródła z laboratoriów:

- `lab_01.ipynb`: `tm_lookup`, dopasowanie bez uwzględniania wielkości liter i interpunkcji, zdania różniące się jednym słowem.
- `lab_02.ipynb`: `ice_lookup`, `levenshtein_similarity`, `fuzzy_lookup`.

Poziomy dopasowania:

- Exact match: ten sam znormalizowany tekst źródłowy.
- Fuzzy match: podobieństwo tekstu, np. RapidFuzz, Levenshtein, trigramy PostgreSQL.
- ICE/context match: ten sam segment z takim samym poprzednim i następnym kontekstem.

Minimalny wynik sugestii:

- `source_text`
- `target_text`
- `score`
- `match_type`
- `domain`
- `created_at`

Stan po Etapie 3:

- backend zapisuje wpis TM po zatwierdzeniu segmentu przez `POST /segments/{segment_id}/approve`,
- endpoint `POST /translation-memory/search` zwraca posortowane sugestie exact/fuzzy,
- exact match ma `score` 100 i `match_type` rowny `exact`,
- fuzzy match jest liczony przez RapidFuzz i sortowany malejaco po score,
- panel pamieci tlumaczen w edytorze pobiera sugestie z API dla aktywnego segmentu,
- panel pokazuje score, typ dopasowania, tekst docelowy, tekst zrodlowy, domene i date,
- klikniecie sugestii wstawia jej tekst docelowy do roboczego pola tlumaczenia aktywnego segmentu,
- panel obsluguje stany ladowania, braku sugestii i bledu API.

## Słownik kontekstowy

Słownik powinien odpowiadać na pytanie: jakie terminy z aktualnego segmentu mają ustalone tłumaczenie?

Źródła z laboratoriów:

- `lab_01.ipynb`: `glossary_lookup` i optymalizacja wyszukiwania.
- `lab_03.ipynb`: `terminology_lookup`, `get_nouns`, `extract_terms`, pozycje terminów w tekście.
- `lab_04-05.ipynb`: TF-IDF i ekstrakcja terminów z korpusu.

Mechanizm startowy:

- tokenizacja segmentu źródłowego,
- wyszukiwanie terminów jedno- i wielowyrazowych,
- filtrowanie po parze językowej i domenie,
- oznaczenie terminów wymaganych i zakazanych,
- zwracanie pozycji terminu w segmencie.

Stan po Etapie 4:

- backend udostepnia `POST /glossary/search` oraz CRUD terminow przez `/glossary/terms`,
- wyszukiwanie dziala deterministycznie po stronie Pythona, dzieki czemu testy przechodza na SQLite,
- wyniki zawieraja termin, dopasowany fragment oraz pozycje `start` i `end` w segmencie zrodlowym,
- import CSV przez `POST /glossary/import-csv` obsluguje kolumny terminu, jezykow, definicji,
  domeny, flag `case_sensitive` i `forbidden` oraz przykladow,
- panel slownika w edytorze pobiera terminy dla aktywnego segmentu, pokazuje definicje, domene,
  status wymagany/zakazany i przyklady,
- klikniecie zalecanego terminu w panelu wstawia `target_term` do tlumaczenia aktywnego segmentu,
- zatwierdzanie segmentu waliduje terminologie przed zmiana statusu na `approved` i przed zapisem
  wpisu do pamieci tlumaczen,
- naruszenia terminologii zwracaja `409` z lista brakujacych terminow wymaganych lub uzytych
  terminow zakazanych.

Możliwe rozszerzenia:

- odmiana fleksyjna dla języka polskiego,
- lematyzacja przez spaCy,
- priorytety terminów,
- terminy zależne od klienta lub projektu,
- automatyczna ekstrakcja kandydatów terminologicznych przez TF-IDF.

## Sprawdzanie pisowni

Spellcheck działa na tekście docelowym, a nie źródłowym.

Źródła z laboratoriów:

- `lab_13-14.ipynb`: podstawowy algorytm korekty, `L1(w)`, `generate_suggestions`.
- `lab_15.ipynb`: `language_tool_python`, wykrywanie błędów w treści strony i komentarzach kodu.

Adaptery:

- prosty adapter słownikowy z laboratorium jako fallback demonstracyjny,
- Hunspell jako szybki lokalny adapter,
- LanguageTool jako bogatszy adapter gramatyczno-stylistyczny.

Minimalny wynik sprawdzania:

- zakres błędu w tekście,
- wykryty token,
- komunikat,
- sugestie poprawy,
- kod reguły lub typ błędu.

Stan po Etapie 5:

- backend udostepnia `POST /spellcheck`, `POST /spellcheck/ignore`, `GET /spellcheck/ignore`
  oraz `DELETE /spellcheck/ignore/{ignore_id}`,
- sprawdzanie dziala na tekscie docelowym aktywnego segmentu,
- lokalny adapter slownikowy jest deterministycznym fallbackiem demonstracyjnym dla `pl`, `en`
  i `de`, dzieki czemu testy nie wymagaja zewnetrznego LanguageTool,
- wynik zawiera `start`, `end`, token, komunikat, liste sugestii, kod reguly
  `LOCAL_DICTIONARY_UNKNOWN_WORD` i jezyk,
- ignorowane slowa sa zapisywane per projekt i jezyk w `SpellcheckIgnore`, a ponowne dodanie
  tego samego slowa zwraca istniejacy wpis,
- panel spellcheck w edytorze pobiera realne wyniki z API po kliknieciu `Check`, zeby nie
  wykonywac requestow przy kazdym znaku,
- panel pokazuje stany: brak aktywnego segmentu, brak tekstu docelowego, ladowanie, brak bledow,
  blad API oraz potwierdzenie zignorowania slowa,
- uzytkownik moze zastosowac sugestie przez podmiane zakresu bledu w aktualnym tekscie
  docelowym albo zignorowac token dla projektu i jezyka,
- spellcheck nie blokuje zatwierdzania segmentu; twarda walidacja zatwierdzania pozostaje po
  stronie terminologii z Etapu 4.

## Import, eksport i QA

Źródła z laboratoriów:

- `lab_06-07.ipynb`: tagi XML, segmenty nietłumaczalne, daty, transfer tagów.
- `lab_11.ipynb`: segmentacja i Hunalign.
- `lab_11_hunalign.py`: konwersja ladder Hunalign do XLIFF.
- `lab_08.ipynb`: BLEU, WER i Levenshtein jako metryki jakości korpusowej.

Formaty startowe:

- TXT dla dokumentów - import wdrozony w Etapie 2,
- CSV dla słownika,
- JSON dla danych demonstracyjnych.

Formaty docelowe:

- TMX dla pamięci tłumaczeń,
- TBX dla terminologii,
- XLIFF dla dokumentów i wymiany z innymi narzędziami CAT.

Reguły QA po MVP:

- zgodność tagów XML/HTML,
- zgodność liczby i wartości dat,
- zgodność terminologii wymaganej,
- ostrzeżenia dla segmentów nietłumaczalnych,
- metryki BLEU/WER dla korpusów testowych.
