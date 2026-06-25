# Polityka bezpieczeństwa

## Zgłaszanie podatności

Jeśli znajdziesz lukę bezpieczeństwa, **nie otwieraj publicznego zgłoszenia (issue)**.
Skorzystaj z prywatnego zgłaszania podatności w GitHub (zakładka **Security** →
**Report a vulnerability**) albo skontaktuj się bezpośrednio z właścicielem repozytorium.

Opisz w zgłoszeniu:

- czego dotyczy problem i jaki jest jego wpływ,
- kroki do odtworzenia (np. przykładowy request),
- wersję / commit, na którym problem występuje.

## Zakres

Projekt jest MVP o charakterze demonstracyjnym, bez uwierzytelniania i bez
przeznaczenia produkcyjnego. Mimo to staramy się traktować poważnie obsługę danych
wejściowych — np. importy TMX/TBX odrzucają deklaracje DTD/DOCTYPE, a serwer ogranicza
rozmiar ciała żądania. Zgłoszenia dotyczące takich mechanizmów są mile widziane.
