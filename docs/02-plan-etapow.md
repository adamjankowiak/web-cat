# Plan etapow

## Etap 1: Fundament repozytorium

- Ustalic wariant stacku technologicznego.
- Przygotowac Docker Compose albo lokalne skrypty uruchomieniowe.
- Dodac minimalny backend z endpointem healthcheck.
- Dodac minimalny frontend z widokiem edytora.
- Przygotowac bazowy model danych i migracje.

## Etap 2: Dokumenty i segmentacja

- Dodac import pliku TXT.
- Podzielic dokument na segmenty po zdaniach lub akapitach.
- Zapisac dokument, segmenty i statusy segmentow w bazie.
- Wyswietlic segmenty w frontendzie.
- Dodac zapis tlumaczenia roboczego.

## Etap 3: Pamiec tlumaczen

- Po zatwierdzeniu segmentu zapisac pare zrodlo-docelowy.
- Dodac exact match po znormalizowanym tekscie zrodlowym.
- Dodac fuzzy match z RapidFuzz albo `pg_trgm`.
- Pokazywac najlepsze sugestie w panelu edytora.
- Dodac metadane: para jezykowa, projekt, domena, autor, data.

## Etap 4: Slownik kontekstowy

- Dodac model terminu: source term, target term, definicja, domena, jezyki.
- Wyszukiwac terminy wystepujace w aktualnym segmencie.
- Pokazywac propozycje terminologiczne w panelu bocznym.
- Dodac walidacje, czy zatwierdzone tlumaczenie zawiera wymagany termin.
- Dodac import slownika z CSV, pozniej TBX.

## Etap 5: Sprawdzanie pisowni

- Dodac endpoint sprawdzania tekstu docelowego.
- Podlaczyc lokalny adapter Hunspell lub LanguageTool.
- Pokazac bledy i sugestie w interfejsie.
- Dodac ignorowanie slow dla projektu/uzytkownika.
- Dodac testy dla kilku jezykow docelowych.

## Etap 6: Eksport i formaty CAT

- Dodac eksport przetlumaczonego TXT.
- Dodac import/eksport TMX dla pamieci tlumaczen.
- Dodac import/eksport TBX dla terminologii.
- Rozwazyc XLIFF dla dokumentow roboczych.

## Etap 7: Jakosc i prezentacja

- Dodac testy jednostkowe backendu.
- Dodac testy komponentow frontendu.
- Dodac test e2e przeplywu: import, tlumaczenie, sugestia TM, spellcheck, eksport.
- Przygotowac dane demonstracyjne.
- Opisac ograniczenia i mozliwe rozszerzenia.
